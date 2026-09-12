"""
Schema oficial de alertas do Agentic SOC N1 Lab.

Este módulo representa a estrutura padronizada de um alerta
recebido pelo SOC antes de seguir para triagem e enriquecimento.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.schemas.enums import AlertType, Severity


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
    """

    model_config = ConfigDict(extra="forbid")

    event_type: AlertType

    category: str | None = None

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    message: str = Field(
        ...,
        min_length=1,
    )

    raw_event: dict[str, Any] = Field(
        default_factory=dict,
        description="Evento bruto original recebido pelo sistema.",
    )


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