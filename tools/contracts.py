"""
Contratos oficiais de execução de ferramentas
do Agentic SOC N1 Lab.

Fase 4.0 — Catálogo e Governança das Ferramentas.

Este módulo padroniza a comunicação entre:

- agentes SOC;
- camada de permissões;
- runtime de ferramentas;
- integrações externas;
- mecanismos de auditoria.

Princípios:

- objetos de execução imutáveis;
- extra fields proibidos;
- payloads convertidos para FrozenDict;
- nenhuma ferramenta altera diretamente o CaseState;
- falhas precisam retornar resultado estruturado;
- deny-by-default é aplicado pela camada de permissões;
- integrações da Fase 4 operam inicialmente em read-only.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from core.schemas.immutable import FrozenDict


class ToolExecutionStatus(str, Enum):
    """
    Estados possíveis para uma execução de ferramenta.
    """

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"


class ToolRequest(BaseModel):
    """
    Solicitação imutável enviada para uma ferramenta.

    A autorização efetiva deve ser validada pela
    camada de permissões antes da execução.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    request_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Identificador único da solicitação "
            "de ferramenta."
        ),
    )

    execution_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Identificador da execução do agente "
            "que originou a chamada."
        ),
    )

    agent_id: str = Field(
        ...,
        min_length=1,
        description="Agente solicitante.",
    )

    case_id: str = Field(
        ...,
        min_length=1,
        description="Caso relacionado à chamada.",
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Identificador global de correlação do caso."
        ),
    )

    tool_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Identificador oficial da ferramenta solicitada."
        ),
    )

    input_payload: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Parâmetros imutáveis autorizados "
            "para a ferramenta."
        ),
    )

    timeout_seconds: int = Field(
        default=15,
        ge=1,
        description=(
            "Timeout máximo permitido para a chamada."
        ),
    )

    max_retries: int = Field(
        default=1,
        ge=0,
        description=(
            "Quantidade máxima de novas tentativas "
            "permitidas."
        ),
    )

    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Momento de criação da solicitação.",
    )

    @field_validator(
        "input_payload",
        mode="before",
    )
    @classmethod
    def freeze_input_payload(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte mappings recebidos em FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "input_payload precisa ser um mapping."
            )

        return FrozenDict(value)

    @field_serializer(
        "input_payload",
    )
    def serialize_input_payload(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte FrozenDict para estrutura JSON
        somente durante serialização.
        """

        return value.to_dict()


class ToolResult(BaseModel):
    """
    Resultado imutável devolvido por uma ferramenta.

    O resultado nunca modifica diretamente o CaseState.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    request_id: str = Field(
        ...,
        min_length=1,
    )

    execution_id: str = Field(
        ...,
        min_length=1,
    )

    agent_id: str = Field(
        ...,
        min_length=1,
    )

    case_id: str = Field(
        ...,
        min_length=1,
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
    )

    tool_id: str = Field(
        ...,
        min_length=1,
    )

    status: ToolExecutionStatus = Field(
        ...,
        description="Estado final da chamada.",
    )

    success: bool = Field(
        ...,
        description=(
            "Indica se a ferramenta concluiu "
            "a operação com sucesso."
        ),
    )

    output_payload: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Dados estruturados retornados pela ferramenta."
        ),
    )

    evidence_payload: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Dados técnicos que podem sustentar "
            "uma evidência do caso."
        ),
    )

    error_code: str | None = Field(
        default=None,
    )

    error_message: str | None = Field(
        default=None,
    )

    attempts: int = Field(
        default=1,
        ge=0,
    )

    duration_ms: int = Field(
        default=0,
        ge=0,
    )

    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @field_validator(
        "output_payload",
        "evidence_payload",
        mode="before",
    )
    @classmethod
    def freeze_result_payloads(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte mappings recebidos em FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "Payload de resultado precisa ser "
                "um mapping."
            )

        return FrozenDict(value)

    @field_serializer(
        "output_payload",
        "evidence_payload",
    )
    def serialize_result_payloads(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte FrozenDict para estrutura JSON
        somente durante serialização.
        """

        return value.to_dict()

    @field_validator(
        "error_code",
        "error_message",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: Any,
    ) -> str | None:
        """
        Strings vazias passam a ser None.
        """

        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    def model_post_init(
        self,
        __context: Any,
    ) -> None:
        """
        Valida coerência entre status e success.
        """

        if (
            self.status == ToolExecutionStatus.COMPLETED
            and not self.success
        ):
            raise ValueError(
                "ToolResult com status COMPLETED "
                "precisa possuir success=True."
            )

        if (
            self.status
            != ToolExecutionStatus.COMPLETED
            and self.success
        ):
            raise ValueError(
                "ToolResult com status diferente de "
                "COMPLETED precisa possuir success=False."
            )

        if (
            self.status
            in {
                ToolExecutionStatus.FAILED,
                ToolExecutionStatus.DENIED,
                ToolExecutionStatus.TIMEOUT,
                ToolExecutionStatus.UNAVAILABLE,
            }
            and self.error_message is None
        ):
            raise ValueError(
                "Resultado de ferramenta sem sucesso "
                "precisa possuir error_message."
            )