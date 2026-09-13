"""
Schema oficial de auditoria do Agentic SOC N1 Lab.

Um AuditEvent registra uma ação relevante ocorrida durante
o ciclo de vida de um caso.

Exemplos:

- criação do caso;
- mudança de estado;
- início ou término de agente;
- chamada de ferramenta;
- inclusão de evidência;
- revisão de QA;
- decisão de escalonamento;
- erro;
- acesso humano.

Eventos de auditoria são imutáveis depois de criados.
"""

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from core.schemas.immutable import FrozenDict


class AuditEvent(BaseModel):
    """
    Registro imutável de auditoria de um caso SOC.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    audit_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do evento de auditoria.",
    )

    case_id: str = Field(
        ...,
        min_length=1,
        description="Caso relacionado ao evento.",
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador global de correlação.",
    )

    event_type: str = Field(
        ...,
        min_length=1,
        description=(
            "Tipo do evento, por exemplo CASE_CREATED, "
            "AGENT_STARTED ou EVIDENCE_ADDED."
        ),
    )

    actor_type: str = Field(
        ...,
        min_length=1,
        description=(
            "Tipo do responsável pelo evento, por exemplo "
            "SYSTEM, AGENT, TOOL ou HUMAN."
        ),
    )

    actor_id: str = Field(
        ...,
        min_length=1,
        description="Identificador do ator responsável.",
    )

    action: str = Field(
        ...,
        min_length=1,
        description="Ação realizada.",
    )

    status: str = Field(
        default="SUCCESS",
        min_length=1,
        description=(
            "Resultado da ação, por exemplo SUCCESS, "
            "FAILED ou DENIED."
        ),
    )

    message: str | None = Field(
        default=None,
        description="Descrição adicional do evento.",
    )

    references: tuple[str, ...] = Field(
        default_factory=tuple,
        description=(
            "IDs relacionados ao evento, como alertas, "
            "evidências, agentes ou ferramentas."
        ),
    )

    payload: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Dados estruturados e imutáveis relacionados ao evento."
        ),
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "audit_id",
        "case_id",
        "correlation_id",
        "event_type",
        "actor_type",
        "actor_id",
        "action",
        "status",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Remove espaços extras e impede valores vazios.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Campos obrigatórios de auditoria não podem estar vazios."
            )

        return cleaned_value

    @field_validator(
        "payload",
        mode="before",
    )
    @classmethod
    def freeze_payload(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte automaticamente mappings para FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "payload precisa ser um objeto do tipo mapping."
            )

        return FrozenDict(value)

    @field_serializer("payload")
    def serialize_payload(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte o payload para dict somente durante serialização.
        """

        return value.to_dict()