"""
Schema oficial de Reflection / QA do Agentic SOC N1 Lab.

Representa a revisão realizada pelo
AG-10 Reflection / QA Agent.

O QA deverá verificar:

- se os achados possuem evidências;
- se existem contradições;
- se há afirmações sem suporte;
- se faltam informações importantes;
- se severidade e confidence são coerentes;
- se a investigação pode ser aprovada;
- se será necessário retry.

O QA não poderá criar evidências.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from core.schemas.enums import QAStatus, Severity


class QAResult(BaseModel):
    """
    Resultado oficial da revisão de qualidade de uma investigação.
    """

    model_config = ConfigDict(extra="forbid")

    qa_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da revisão QA.",
    )

    investigation_id: str = Field(
        ...,
        min_length=1,
        description="Investigação revisada.",
    )

    status: QAStatus = Field(
        ...,
        description="Resultado da revisão.",
    )

    issues: list[str] = Field(
        default_factory=list,
        description="Problemas encontrados durante a revisão.",
    )

    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Afirmações que não possuem evidência suficiente.",
    )

    contradictions: list[str] = Field(
        default_factory=list,
        description="Contradições encontradas na investigação.",
    )

    missing_evidence: list[str] = Field(
        default_factory=list,
        description="Evidências consideradas necessárias e ainda ausentes.",
    )

    reviewed_severity: Severity = Field(
        ...,
        description="Severidade validada ou sugerida pelo QA.",
    )

    reviewed_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence validado pelo QA.",
    )

    retry_required: bool = Field(
        default=False,
        description="Indica se a investigação deverá passar por novo ciclo.",
    )

    retry_targets: list[str] = Field(
        default_factory=list,
        description=(
            "Agentes que deverão ser acionados novamente "
            "caso seja necessário retry."
        ),
    )

    notes: list[str] = Field(
        default_factory=list,
        description="Observações adicionais da revisão.",
    )

    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )