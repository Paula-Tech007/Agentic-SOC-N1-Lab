"""
Schema oficial de investigação do Agentic SOC N1 Lab.

Representa a análise consolidada produzida pelo
AG-09 Incident Analyst Agent.

O Incident Analyst deverá consolidar:

- triagem;
- indicadores;
- identidade;
- ativos;
- threat intelligence;
- evidências;
- contexto recuperado por RAG.

O agente deverá separar fatos observados de inferências.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import (
    FinalClassification,
    Severity,
)


class InvestigationFinding(BaseModel):
    """
    Representa um achado individual da investigação.
    """

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do achado.",
    )

    title: str = Field(
        ...,
        min_length=1,
        description="Título curto do achado.",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Descrição objetiva do achado.",
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="IDs das evidências que sustentam o achado.",
    )

    is_inference: bool = Field(
        default=False,
        description=(
            "True significa que o achado é uma inferência. "
            "False significa que representa fato observado."
        ),
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança atribuída ao achado.",
    )


class TimelineEntry(BaseModel):
    """
    Evento relevante na linha do tempo da investigação.
    """

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime

    description: str = Field(
        ...,
        min_length=1,
    )

    evidence_references: list[str] = Field(
        default_factory=list,
    )


class InvestigationResult(BaseModel):
    """
    Resultado consolidado produzido pelo Incident Analyst.
    """

    model_config = ConfigDict(extra="forbid")

    investigation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da investigação.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta associado à investigação.",
    )

    summary: str = Field(
        ...,
        min_length=1,
        description="Resumo executivo da investigação.",
    )

    findings: list[InvestigationFinding] = Field(
        default_factory=list,
        description="Achados consolidados.",
    )

    timeline: list[TimelineEntry] = Field(
        default_factory=list,
        description="Linha do tempo dos eventos relevantes.",
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="Todas as evidências usadas na investigação.",
    )

    gaps: list[str] = Field(
        default_factory=list,
        description="Informações faltantes ou ainda não confirmadas.",
    )

    final_severity: Severity = Field(
        ...,
        description="Severidade consolidada do caso.",
    )

    final_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confiança final da investigação.",
    )

    classification: FinalClassification = Field(
        ...,
        description="Classificação final proposta pelo Incident Analyst.",
    )

    recommended_action: str = Field(
        ...,
        min_length=1,
        description="Próxima ação recomendada.",
    )

    analyst_notes: list[str] = Field(
        default_factory=list,
        description="Observações adicionais da investigação.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "summary",
        "recommended_action",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """
        Impede campos textuais obrigatórios vazios.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Campos obrigatórios da investigação não podem estar vazios."
            )

        return cleaned_value