"""
Schema oficial de escalonamento do Agentic SOC N1 Lab.

Representa a decisão operacional produzida pelo
AG-12 Escalation Agent.

O agente deverá utilizar:

- investigação consolidada;
- resultado do QA;
- severidade;
- confidence;
- evidências;
- hard rules;
- políticas do SOC.

As hard rules possuem prioridade sobre a interpretação do LLM.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import (
    FinalClassification,
    FinalDecision,
    Severity,
)


class EscalationResult(BaseModel):
    """
    Resultado oficial da decisão operacional do caso.
    """

    model_config = ConfigDict(extra="forbid")

    escalation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da decisão.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta relacionado à decisão.",
    )

    investigation_id: str = Field(
        ...,
        min_length=1,
        description="Investigação utilizada na decisão.",
    )

    qa_id: str = Field(
        ...,
        min_length=1,
        description="Revisão QA utilizada na decisão.",
    )

    decision: FinalDecision = Field(
        ...,
        description="Decisão operacional final do caso.",
    )

    classification: FinalClassification = Field(
        ...,
        description="Classificação consolidada do incidente.",
    )

    severity: Severity = Field(
        ...,
        description="Severidade considerada na decisão.",
    )

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confiança associada à decisão.",
    )

    reason: str = Field(
        ...,
        min_length=1,
        description="Justificativa objetiva para a decisão.",
    )

    hard_rules_triggered: list[str] = Field(
        default_factory=list,
        description="Hard rules que influenciaram a decisão.",
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="Evidências utilizadas na decisão.",
    )

    human_approval_required: bool = Field(
        default=False,
        description=(
            "Indica se a continuidade do fluxo depende "
            "de aprovação humana."
        ),
    )

    recommended_next_step: str = Field(
        ...,
        min_length=1,
        description="Próximo passo recomendado pelo sistema.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "reason",
        "recommended_next_step",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """
        Impede campos obrigatórios vazios.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "A decisão precisa possuir justificativa e próximo passo."
            )

        return cleaned_value