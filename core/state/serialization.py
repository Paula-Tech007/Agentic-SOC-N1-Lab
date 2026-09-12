"""
Serialização e persistência JSON do CaseState.

Este módulo permite:

- transformar um CaseState em JSON;
- reconstruir um CaseState a partir de JSON;
- salvar um caso em arquivo;
- carregar um caso salvo anteriormente.

A validação continua sendo realizada pelo Pydantic ao
reconstruir o estado.
"""

from pathlib import Path

from core.state.case_state import CaseState


def serialize_case_state(
    case_state: CaseState,
    indent: int = 2,
) -> str:
    """
    Converte um CaseState para JSON.
    """

    return case_state.model_dump_json(
        indent=indent,
    )


def deserialize_case_state(
    json_data: str,
) -> CaseState:
    """
    Reconstrói um CaseState a partir de uma string JSON.

    Todos os schemas internos também são reconstruídos
    e validados pelo Pydantic.
    """

    return CaseState.model_validate_json(
        json_data
    )


def save_case_state_json(
    case_state: CaseState,
    file_path: str | Path,
) -> Path:
    """
    Salva um CaseState em um arquivo JSON.

    O diretório de destino é criado automaticamente
    caso ainda não exista.
    """

    path = Path(file_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_data = serialize_case_state(
        case_state=case_state,
        indent=2,
    )

    path.write_text(
        json_data,
        encoding="utf-8",
    )

    return path


def load_case_state_json(
    file_path: str | Path,
) -> CaseState:
    """
    Carrega um CaseState armazenado em arquivo JSON.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de CaseState não encontrado: {path}"
        )

    json_data = path.read_text(
        encoding="utf-8",
    )

    return deserialize_case_state(
        json_data=json_data,
    )