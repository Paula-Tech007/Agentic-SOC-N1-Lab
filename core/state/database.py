"""
Persistência SQLite do Agentic SOC N1 Lab.

Este módulo fornece a primeira camada de banco de dados
para armazenamento estruturado dos casos SOC.

O SQLite armazenará:

- identificador do caso;
- correlation_id;
- alert_id;
- status atual;
- decisão final, quando existir;
- versão do CaseState;
- timestamps;
- JSON completo do CaseState.

O JSON completo continua sendo validado pelo Pydantic
quando o caso é carregado novamente.
"""

import sqlite3
from pathlib import Path

from core.state.case_state import CaseState
from core.state.serialization import (
    deserialize_case_state,
    serialize_case_state,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT
    / "storage"
    / "database"
    / "agentic_soc.db"
)


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Path:
    """
    Cria o banco SQLite e a tabela inicial de casos.

    Se o banco e a tabela já existirem, nenhuma informação
    existente será apagada.
    """

    path = Path(database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                correlation_id TEXT NOT NULL,
                alert_id TEXT NOT NULL,
                case_status TEXT NOT NULL,
                final_decision TEXT,
                version INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_correlation_id
            ON cases (correlation_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_alert_id
            ON cases (alert_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_status
            ON cases (case_status)
            """
        )

        connection.commit()

    return path


def save_case_state_sqlite(
    case_state: CaseState,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Path:
    """
    Insere ou atualiza um CaseState no SQLite.

    O case_id funciona como chave única.
    """

    path = initialize_database(
        database_path=database_path,
    )

    payload_json = serialize_case_state(
        case_state=case_state,
        indent=2,
    )

    final_decision = None

    if case_state.escalation is not None:
        final_decision = case_state.escalation.decision.value

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO cases (
                case_id,
                correlation_id,
                alert_id,
                case_status,
                final_decision,
                version,
                created_at,
                updated_at,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(case_id) DO UPDATE SET
                correlation_id = excluded.correlation_id,
                alert_id = excluded.alert_id,
                case_status = excluded.case_status,
                final_decision = excluded.final_decision,
                version = excluded.version,
                updated_at = excluded.updated_at,
                payload_json = excluded.payload_json
            """,
            (
                case_state.case_id,
                case_state.correlation_id,
                case_state.alert.alert_id,
                case_state.workflow.case_status.value,
                final_decision,
                case_state.version,
                case_state.created_at.isoformat(),
                case_state.updated_at.isoformat(),
                payload_json,
            ),
        )

        connection.commit()

    return path


def load_case_state_sqlite(
    case_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> CaseState:
    """
    Carrega um CaseState pelo case_id.
    """

    path = Path(database_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Banco SQLite não encontrado: {path}"
        )

    with sqlite3.connect(path) as connection:
        cursor = connection.execute(
            """
            SELECT payload_json
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        )

        row = cursor.fetchone()

    if row is None:
        raise KeyError(
            f"CaseState não encontrado: {case_id}"
        )

    return deserialize_case_state(
        json_data=row[0],
    )


def case_exists_sqlite(
    case_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """
    Verifica se um case_id já existe no banco.
    """

    path = Path(database_path)

    if not path.exists():
        return False

    with sqlite3.connect(path) as connection:
        cursor = connection.execute(
            """
            SELECT 1
            FROM cases
            WHERE case_id = ?
            LIMIT 1
            """,
            (case_id,),
        )

        return cursor.fetchone() is not None