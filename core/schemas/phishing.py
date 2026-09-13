"""
Schema oficial de análise de phishing do Agentic SOC N1 Lab.

Representa a saída estruturada produzida pelo
AG-07 Phishing Analyst Agent.

O agente poderá analisar contexto como:

- remetente;
- destinatários;
- assunto;
- URLs;
- anexos;
- hashes;
- autenticação de e-mail;
- indicadores suspeitos;
- evidências relacionadas.

O schema não executa ações sobre mensagens.
Ele apenas representa o resultado da análise defensiva.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import (
    FinalClassification,
    Severity,
)


class EmailAuthenticationResult(BaseModel):
    """
    Resultado das verificações de autenticação do e-mail.
    """

    model_config = ConfigDict(extra="forbid")

    spf: str | None = Field(
        default=None,
        description="Resultado SPF, quando disponível.",
    )

    dkim: str | None = Field(
        default=None,
        description="Resultado DKIM, quando disponível.",
    )

    dmarc: str | None = Field(
        default=None,
        description="Resultado DMARC, quando disponível.",
    )


class PhishingResult(BaseModel):
    """
    Resultado oficial produzido pelo AG-07 Phishing Analyst.
    """

    model_config = ConfigDict(extra="forbid")

    phishing_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da análise de phishing.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta associado à análise.",
    )

    sender: str | None = Field(
        default=None,
        description="Remetente identificado na mensagem.",
    )

    recipients: list[str] = Field(
        default_factory=list,
        description="Destinatários identificados.",
    )

    subject: str | None = Field(
        default=None,
        description="Assunto da mensagem.",
    )

    urls: list[str] = Field(
        default_factory=list,
        description="URLs identificadas na mensagem.",
    )

    attachment_names: list[str] = Field(
        default_factory=list,
        description="Nomes dos anexos identificados.",
    )

    attachment_hashes: list[str] = Field(
        default_factory=list,
        description="Hashes conhecidos dos anexos.",
    )

    authentication: EmailAuthenticationResult = Field(
        default_factory=EmailAuthenticationResult,
        description="Resultados SPF, DKIM e DMARC.",
    )

    suspicious_indicators: list[str] = Field(
        default_factory=list,
        description="Indicadores suspeitos identificados.",
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="Evidências que sustentam a análise.",
    )

    classification: FinalClassification = Field(
        ...,
        description="Classificação proposta pela análise.",
    )

    severity: Severity = Field(
        ...,
        description="Severidade atribuída ao caso.",
    )

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confiança da análise entre 0 e 100.",
    )

    summary: str = Field(
        ...,
        min_length=1,
        description="Resumo objetivo da análise de phishing.",
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
                "O resumo da análise de phishing não pode estar vazio."
            )

        return cleaned_value