"""
Schema oficial de Threat Intelligence do Agentic SOC N1 Lab.

Representa a saída estruturada produzida pelo
AG-04 Threat Intelligence Agent.

O agente poderá enriquecer indicadores como:

- IP
- domínio
- URL
- hash
- e-mail

Neste momento estamos apenas definindo a estrutura dos dados.
As integrações reais com fontes de Threat Intelligence serão
implementadas em fases posteriores.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import IndicatorType


class ThreatIntelFinding(BaseModel):
    """
    Resultado de enriquecimento de um único IOC.
    """

    model_config = ConfigDict(extra="forbid")

    ioc_id: str = Field(
        ...,
        min_length=1,
        description="IOC relacionado ao resultado de Threat Intelligence.",
    )

    indicator_type: IndicatorType = Field(
        ...,
        description="Tipo do indicador analisado.",
    )

    value: str = Field(
        ...,
        min_length=1,
        description="Valor do indicador consultado.",
    )

    provider: str = Field(
        ...,
        min_length=1,
        description="Fonte ou provedor que retornou a informação.",
    )

    reputation: str | None = Field(
        default=None,
        description="Reputação retornada pela fonte.",
    )

    malicious_confirmed: bool | None = Field(
        default=None,
        description=(
            "True quando a fonte confirma o IOC como malicioso. "
            "False quando confirma como não malicioso. "
            "None quando não foi possível determinar."
        ),
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança atribuída ao resultado.",
    )

    score: float | None = Field(
        default=None,
        description="Score retornado pela fonte, quando disponível.",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags associadas ao indicador.",
    )

    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Informações adicionais retornadas pela fonte.",
    )

    queried_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("value", "provider")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """
        Remove espaços extras e impede campos vazios.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Valor e provider não podem estar vazios."
            )

        return cleaned_value


class ThreatIntelResult(BaseModel):
    """
    Resultado consolidado do AG-04 Threat Intelligence Agent.
    """

    model_config = ConfigDict(extra="forbid")

    threat_intel_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da execução de Threat Intelligence.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta associado à investigação.",
    )

    findings: list[ThreatIntelFinding] = Field(
        default_factory=list,
        description="Resultados obtidos para os IOCs consultados.",
    )

    queried_sources: list[str] = Field(
        default_factory=list,
        description="Fontes consultadas durante o enriquecimento.",
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="Evidências geradas a partir da consulta.",
    )

    summary: str = Field(
        ...,
        min_length=1,
        description="Resumo objetivo do enriquecimento realizado.",
    )

    errors: list[str] = Field(
        default_factory=list,
        description=(
            "Erros de consulta que ocorreram sem invalidar "
            "todo o resultado."
        ),
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
                "O resumo de Threat Intelligence não pode estar vazio."
            )

        return cleaned_value