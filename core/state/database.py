"""
Persistência SQLite do Agentic SOC N1 Lab.

Este módulo fornece a camada inicial de persistência
estruturada dos casos e eventos de auditoria.

O SQLite armazena:

- identificador do caso;
- correlation_id;
- alert_id;
- status atual;
- decisão final;
- versão do CaseState;
- timestamps;
- JSON completo do CaseState;
- eventos de auditoria append-only.

A tabela de casos pode ser atualizada conforme o caso evolui.

A tabela audit_events não possui operação de atualização:
novos eventos são inseridos e registros anteriores são
preservados.
"""

import sqlite3
from pathlib import Path

from core.schemas import AuditEvent
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
    Cria o banco SQLite e as tabelas iniciais.

    Se já existirem, nenhuma informação anterior é apagada.
    """

    path = Path(database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(path) as connection:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

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
            CREATE TABLE IF NOT EXISTS audit_events (
                audit_id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY (case_id)
                    REFERENCES cases (case_id)
                    ON DELETE CASCADE
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

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_case_id
            ON audit_events (case_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_correlation_id
            ON audit_events (correlation_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_event_type
            ON audit_events (event_type)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_created_at
            ON audit_events (created_at)
            """
        )

        connection.commit()

    return path


def _insert_audit_event(
    connection: sqlite3.Connection,
    audit_event: AuditEvent,
) -> None:
    """
    Insere um AuditEvent de forma append-only.

    Caso o mesmo audit_id já exista, o registro anterior
    permanece intacto.
    """

    connection.execute(
        """
        INSERT OR IGNORE INTO audit_events (
            audit_id,
            case_id,
            correlation_id,
            event_type,
            actor_type,
            actor_id,
            action,
            status,
            created_at,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_event.audit_id,
            audit_event.case_id,
            audit_event.correlation_id,
            audit_event.event_type,
            audit_event.actor_type,
            audit_event.actor_id,
            audit_event.action,
            audit_event.status,
            audit_event.created_at.isoformat(),
            audit_event.model_dump_json(),
        ),
    )


def save_case_state_sqlite(
    case_state: CaseState,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> Path:
    """
    Insere ou atualiza um CaseState no SQLite.

    Eventos de auditoria presentes no CaseState são
    persistidos na tabela append-only audit_events.
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
        final_decision = (
            case_state.escalation.decision.value
        )

    with sqlite3.connect(path) as connection:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

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

        for audit_event in case_state.audit:
            _insert_audit_event(
                connection=connection,
                audit_event=audit_event,
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


def load_audit_events_sqlite(
    case_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> tuple[AuditEvent, ...]:
    """
    Recupera o histórico de auditoria de um caso,
    respeitando a ordem de criação.
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
            FROM audit_events
            WHERE case_id = ?
            ORDER BY created_at ASC, audit_id ASC
            """,
            (case_id,),
        )

        rows = cursor.fetchall()

    return tuple(
        AuditEvent.model_validate_json(row[0])
        for row in rows
    )


def case_exists_sqlite(
    case_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> bool:
    """
    Verifica se um case_id existe no banco.
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