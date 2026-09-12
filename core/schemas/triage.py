"""
Schema oficial de triagem do Agentic SOC N1 Lab.

Representa a saída estruturada produzida pelo
AG-03 Triage Analyst Agent.

A triagem é responsável por:

- classificar inicialmente o alerta;
- definir severidade;
- atribuir confidence;
- identificar IOCs relacionados;
- apontar informações faltantes;
- indicar quais especialistas devem atuar;
- sinalizar necessidade de escalonamento imediato.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import AlertType, Severity


class TriageResult(BaseModel):
    """
    Resultado oficial da triagem inicial de um alerta SOC.
    """

    model_config = ConfigDict(extra="forbid")

    triage_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da triagem.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta associado à triagem.",
    )

    alert_type: AlertType = Field(
        ...,
        description="Classificação inicial do alerta.",
    )

    severity: Severity = Field(
        ...,
        description="Severidade inicial definida pela triagem.",
    )

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confiança da triagem entre 0 e 100.",
    )

    summary: str = Field(
        ...,
        min_length=1,
        description="Resumo objetivo da triagem.",
    )

    reasons: list[str] = Field(
        default_factory=list,
        description="Motivos que sustentam a classificação.",
    )

    ioc_references: list[str] = Field(
        default_factory=list,
        description="IDs dos IOCs identificados durante a triagem.",
    )

    identity_references: list[str] = Field(
        default_factory=list,
        description="IDs de identidades relacionadas.",
    )

    asset_references: list[str] = Field(
        default_factory=list,
        description="IDs de ativos relacionados.",
    )

    required_agents: list[str] = Field(
        default_factory=list,
        description=(
            "Agentes especialistas que deverão participar "
            "da investigação."
        ),
    )

    missing_data: list[str] = Field(
        default_factory=list,
        description="Informações ainda necessárias para investigação.",
    )

    immediate_escalation: bool = Field(
        default=False,
        description=(
            "Indica se existe motivo determinístico para "
            "escalonamento imediato."
        ),
    )

    escalation_reason: str | None = Field(
        default=None,
        description="Motivo de escalonamento imediato, quando aplicável.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        """
        Impede resumo vazio.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "O resumo da triagem não pode estar vazio."
            )

        return cleaned_value