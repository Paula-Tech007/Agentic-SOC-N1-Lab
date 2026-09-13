"""
Schema oficial de alertas do Agentic SOC N1 Lab.

Este módulo representa a estrutura padronizada de um alerta
recebido pelo SOC antes de seguir para triagem e enriquecimento.

O evento bruto original é tratado como imutável para preservar
a integridade da informação recebida.
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

from core.schemas.enums import AlertType, Severity
from core.schemas.immutable import FrozenDict


class AlertSource(BaseModel):
    """
    Origem do alerta.
    """

    model_config = ConfigDict(extra="forbid")

    system: str = Field(
        ...,
        min_length=1,
        description="Sistema de origem do alerta, por exemplo SIEM ou EDR.",
    )

    product: str | None = Field(
        default=None,
        description="Produto ou plataforma que gerou o alerta.",
    )

    rule_name: str | None = Field(
        default=None,
        description="Nome da regra que gerou o alerta.",
    )

    rule_id: str | None = Field(
        default=None,
        description="Identificador da regra.",
    )


class AlertEvent(BaseModel):
    """
    Evento normalizado relacionado ao alerta.

    O objeto inteiro é congelado após criação e o raw_event
    utiliza FrozenDict para impedir alterações internas.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    event_type: AlertType

    category: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    message: str = Field(
        ...,
        min_length=1,
    )

    raw_event: FrozenDict = Field(
        default_factory=FrozenDict,
        description="Evento bruto original imutável recebido pelo sistema.",
    )

    @field_validator(
        "raw_event",
        mode="before",
    )
    @classmethod
    def freeze_raw_event(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte automaticamente mappings recebidos para FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "raw_event precisa ser um objeto do tipo mapping."
            )

        return FrozenDict(value)

    @field_serializer("raw_event")
    def serialize_raw_event(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte FrozenDict para dict somente durante serialização.
        """

        return value.to_dict()


class Alert(BaseModel):
    """
    Estrutura oficial de um alerta dentro do SOC N1.
    """

    model_config = ConfigDict(extra="forbid")

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do alerta.",
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador usado para correlacionar toda a investigação.",
    )

    source: AlertSource

    event: AlertEvent

    initial_severity: Severity = Severity.MEDIUM

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )