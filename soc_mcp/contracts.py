"""
Contratos internos MCP
do Agentic SOC N1 Lab.

Fase 6.0 — Fundação MCP.

Este módulo define estruturas imutáveis para:

- descrição de tools MCP;
- requisição de execução;
- resultado de execução;
- status da chamada;
- metadados de auditoria.

Os contratos desta camada NÃO substituem:

- ToolRequest;
- ToolResult;
- ToolPolicy;
- ToolAuthorization;
- ToolRuntime.

O MCP funciona como uma camada de transporte
e exposição controlada.

Fluxo conceitual:

Agente
    ↓
MCPToolCallRequest
    ↓
MCP Server
    ↓
ToolRuntime
    ↓
ToolResult
    ↓
MCPToolCallResult

Princípios:

- fail-closed;
- read-only;
- local-only;
- deny-by-default;
- IDs obrigatórios;
- payload imutável;
- nenhuma ação crítica autônoma.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    datetime,
    timezone,
)
from enum import Enum
from types import (
    MappingProxyType,
)
from typing import (
    Any,
    Mapping,
)


DEFAULT_MCP_CALL_TIMEOUT_SECONDS = 30

MIN_MCP_CALL_TIMEOUT_SECONDS = 1

MAX_MCP_CALL_TIMEOUT_SECONDS = 120


class MCPCallStatus(
    str,
    Enum,
):
    """
    Status oficial de uma chamada MCP.
    """

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"


def _utc_now() -> datetime:
    """
    Retorna timestamp UTC timezone-aware.
    """

    return datetime.now(
        timezone.utc
    )


def _required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Valida string obrigatória.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{field_name} não pode "
            "ser vazio."
        )

    return cleaned


def _optional_string(
    value: object,
    *,
    field_name: str,
) -> str | None:
    """
    Valida string opcional.
    """

    if value is None:
        return None

    return _required_string(
        value,
        field_name=field_name,
    )


def _normalize_positive_int(
    value: object,
    *,
    field_name: str,
) -> int:
    """
    Valida inteiro maior que zero.
    """

    if isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser inteiro."
        )

    if not isinstance(
        value,
        int,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser inteiro."
        )

    if value < 1:
        raise ValueError(
            f"{field_name} precisa "
            "ser maior que zero."
        )

    return value


def _normalize_non_negative_int(
    value: object,
    *,
    field_name: str,
) -> int:
    """
    Valida inteiro maior ou igual a zero.
    """

    if isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser inteiro."
        )

    if not isinstance(
        value,
        int,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser inteiro."
        )

    if value < 0:
        raise ValueError(
            f"{field_name} não pode "
            "ser negativo."
        )

    return value


def _normalize_timeout(
    value: object,
) -> int:
    """
    Valida timeout MCP.
    """

    normalized = (
        _normalize_positive_int(
            value,
            field_name=(
                "timeout_seconds"
            ),
        )
    )

    if (
        normalized
        < MIN_MCP_CALL_TIMEOUT_SECONDS
        or normalized
        > MAX_MCP_CALL_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "timeout_seconds precisa estar "
            f"entre "
            f"{MIN_MCP_CALL_TIMEOUT_SECONDS} "
            f"e "
            f"{MAX_MCP_CALL_TIMEOUT_SECONDS}."
        )

    return normalized


def _normalize_timestamp(
    value: object,
    *,
    field_name: str,
) -> datetime:
    """
    Exige datetime timezone-aware.
    """

    if not isinstance(
        value,
        datetime,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser datetime."
        )

    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} precisa "
            "possuir timezone."
        )

    return value.astimezone(
        timezone.utc
    )


def _freeze_value(
    value: Any,
) -> Any:
    """
    Converte estruturas mutáveis
    em representações imutáveis.

    dict -> MappingProxyType
    list -> tuple
    set -> frozenset
    tuple -> tuple recursiva
    """

    if isinstance(
        value,
        Mapping,
    ):
        frozen_mapping = {
            str(key): _freeze_value(
                item
            )
            for key, item
            in value.items()
        }

        return MappingProxyType(
            frozen_mapping
        )

    if isinstance(
        value,
        list,
    ):
        return tuple(
            _freeze_value(
                item
            )
            for item in value
        )

    if isinstance(
        value,
        tuple,
    ):
        return tuple(
            _freeze_value(
                item
            )
            for item in value
        )

    if isinstance(
        value,
        set,
    ):
        return frozenset(
            _freeze_value(
                item
            )
            for item in value
        )

    return value


def _freeze_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, Any]:
    """
    Valida e congela Mapping.
    """

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser um Mapping."
        )

    frozen = _freeze_value(
        value
    )

    if not isinstance(
        frozen,
        Mapping,
    ):
        raise ValueError(
            f"{field_name} inválido."
        )

    return frozen


def _normalize_agent_ids(
    value: object,
) -> tuple[str, ...]:
    """
    Normaliza agentes autorizados.
    """

    if not isinstance(
        value,
        (
            tuple,
            list,
        ),
    ):
        raise ValueError(
            "allowed_agents precisa "
            "ser lista ou tupla."
        )

    result: list[str] = []

    for item in value:
        agent_id = _required_string(
            item,
            field_name="agent_id",
        )

        if agent_id not in result:
            result.append(
                agent_id
            )

    if not result:
        raise ValueError(
            "allowed_agents não pode "
            "ser vazio."
        )

    return tuple(
        result
    )


@dataclass(
    frozen=True,
    slots=True,
)
class MCPToolDescriptor:
    """
    Descrição de uma ferramenta
    exposta pelo MCP.

    O descriptor não concede autorização.

    A autorização real continua sendo
    determinada por ToolPolicy e
    ToolRuntime.
    """

    tool_id: str

    title: str

    description: str

    allowed_agents: tuple[str, ...]

    input_schema: Mapping[str, Any] = field(
        default_factory=dict
    )

    read_only: bool = True

    local_only: bool = True

    critical_action: bool = False

    def __post_init__(
        self,
    ) -> None:
        """
        Valida descriptor.
        """

        object.__setattr__(
            self,
            "tool_id",
            _required_string(
                self.tool_id,
                field_name="tool_id",
            ),
        )

        object.__setattr__(
            self,
            "title",
            _required_string(
                self.title,
                field_name="title",
            ),
        )

        object.__setattr__(
            self,
            "description",
            _required_string(
                self.description,
                field_name=(
                    "description"
                ),
            ),
        )

        object.__setattr__(
            self,
            "allowed_agents",
            _normalize_agent_ids(
                self.allowed_agents
            ),
        )

        object.__setattr__(
            self,
            "input_schema",
            _freeze_mapping(
                self.input_schema,
                field_name=(
                    "input_schema"
                ),
            ),
        )

        if self.read_only is not True:
            raise ValueError(
                "Tools MCP precisam "
                "permanecer READ_ONLY "
                "nesta fase."
            )

        if self.local_only is not True:
            raise ValueError(
                "Tools MCP precisam "
                "permanecer locais "
                "nesta fase."
            )

        if (
            self.critical_action
            is not False
        ):
            raise ValueError(
                "Ações críticas não podem "
                "ser expostas pelo MCP."
            )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna descrição segura.
        """

        return {
            "tool_id": self.tool_id,
            "title": self.title,
            "allowed_agents": (
                self.allowed_agents
            ),
            "read_only": (
                self.read_only
            ),
            "local_only": (
                self.local_only
            ),
            "critical_action": (
                self.critical_action
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class MCPToolCallRequest:
    """
    Requisição interna para uma
    chamada MCP.
    """

    request_id: str

    execution_id: str

    agent_id: str

    case_id: str

    correlation_id: str

    tool_id: str

    arguments: Mapping[str, Any] = field(
        default_factory=dict
    )

    timeout_seconds: int = (
        DEFAULT_MCP_CALL_TIMEOUT_SECONDS
    )

    requested_at: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida requisição.
        """

        for field_name in (
            "request_id",
            "execution_id",
            "agent_id",
            "case_id",
            "correlation_id",
            "tool_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_string(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name=(
                        field_name
                    ),
                ),
            )

        object.__setattr__(
            self,
            "arguments",
            _freeze_mapping(
                self.arguments,
                field_name="arguments",
            ),
        )

        object.__setattr__(
            self,
            "timeout_seconds",
            _normalize_timeout(
                self.timeout_seconds
            ),
        )

        object.__setattr__(
            self,
            "requested_at",
            _normalize_timestamp(
                self.requested_at,
                field_name=(
                    "requested_at"
                ),
            ),
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        da requisição.
        """

        return {
            "request_id": (
                self.request_id
            ),
            "execution_id": (
                self.execution_id
            ),
            "agent_id": (
                self.agent_id
            ),
            "case_id": (
                self.case_id
            ),
            "correlation_id": (
                self.correlation_id
            ),
            "tool_id": (
                self.tool_id
            ),
            "timeout_seconds": (
                self.timeout_seconds
            ),
            "argument_keys": tuple(
                self.arguments.keys()
            ),
            "requested_at": (
                self.requested_at.isoformat()
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class MCPToolCallResult:
    """
    Resultado interno de uma
    chamada MCP.
    """

    request_id: str

    execution_id: str

    agent_id: str

    case_id: str

    correlation_id: str

    tool_id: str

    status: MCPCallStatus

    success: bool

    output: Mapping[str, Any] = field(
        default_factory=dict
    )

    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )

    error_code: str | None = None

    error_message: str | None = None

    attempts: int = 1

    duration_ms: int = 0

    completed_at: datetime = field(
        default_factory=_utc_now
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida consistência do resultado.
        """

        for field_name in (
            "request_id",
            "execution_id",
            "agent_id",
            "case_id",
            "correlation_id",
            "tool_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_string(
                    getattr(
                        self,
                        field_name,
                    ),
                    field_name=(
                        field_name
                    ),
                ),
            )

        status = self.status

        if isinstance(
            status,
            str,
        ):
            try:
                status = MCPCallStatus(
                    status
                )
            except ValueError as exc:
                raise ValueError(
                    "status MCP inválido."
                ) from exc

            object.__setattr__(
                self,
                "status",
                status,
            )

        if not isinstance(
            status,
            MCPCallStatus,
        ):
            raise ValueError(
                "status precisa ser "
                "MCPCallStatus."
            )

        if not isinstance(
            self.success,
            bool,
        ):
            raise ValueError(
                "success precisa "
                "ser booleano."
            )

        object.__setattr__(
            self,
            "output",
            _freeze_mapping(
                self.output,
                field_name="output",
            ),
        )

        object.__setattr__(
            self,
            "evidence",
            _freeze_mapping(
                self.evidence,
                field_name="evidence",
            ),
        )

        object.__setattr__(
            self,
            "error_code",
            _optional_string(
                self.error_code,
                field_name=(
                    "error_code"
                ),
            ),
        )

        object.__setattr__(
            self,
            "error_message",
            _optional_string(
                self.error_message,
                field_name=(
                    "error_message"
                ),
            ),
        )

        object.__setattr__(
            self,
            "attempts",
            _normalize_non_negative_int(
                self.attempts,
                field_name="attempts",
            ),
        )

        object.__setattr__(
            self,
            "duration_ms",
            _normalize_non_negative_int(
                self.duration_ms,
                field_name=(
                    "duration_ms"
                ),
            ),
        )

        object.__setattr__(
            self,
            "completed_at",
            _normalize_timestamp(
                self.completed_at,
                field_name=(
                    "completed_at"
                ),
            ),
        )

        if (
            status
            is MCPCallStatus.COMPLETED
        ):
            if self.success is not True:
                raise ValueError(
                    "Status COMPLETED exige "
                    "success=True."
                )

            if (
                self.error_code is not None
                or self.error_message
                is not None
            ):
                raise ValueError(
                    "Resultado COMPLETED não "
                    "pode possuir erro."
                )

        else:
            if self.success is not False:
                raise ValueError(
                    "Status diferente de "
                    "COMPLETED exige "
                    "success=False."
                )

        if status in (
            MCPCallStatus.FAILED,
            MCPCallStatus.DENIED,
            MCPCallStatus.TIMEOUT,
            MCPCallStatus.UNAVAILABLE,
        ):
            if self.error_message is None:
                raise ValueError(
                    "Resultado de falha MCP "
                    "precisa possuir "
                    "error_message."
                )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        do resultado.
        """

        return {
            "request_id": (
                self.request_id
            ),
            "execution_id": (
                self.execution_id
            ),
            "agent_id": (
                self.agent_id
            ),
            "case_id": (
                self.case_id
            ),
            "correlation_id": (
                self.correlation_id
            ),
            "tool_id": (
                self.tool_id
            ),
            "status": (
                self.status.value
            ),
            "success": (
                self.success
            ),
            "attempts": (
                self.attempts
            ),
            "duration_ms": (
                self.duration_ms
            ),
            "has_output": bool(
                self.output
            ),
            "has_evidence": bool(
                self.evidence
            ),
            "error_code": (
                self.error_code
            ),
            "completed_at": (
                self.completed_at.isoformat()
            ),
        }