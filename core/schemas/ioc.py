"""
Schema oficial de Indicadores de Comprometimento (IOC)
do Agentic SOC N1 Lab.

Este módulo padroniza indicadores que circulam entre os
agentes durante uma investigação de segurança.

Tipos inicialmente suportados:

- IP
- domínio
- URL
- hash
- e-mail
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import IndicatorType


class IOC(BaseModel):
    """
    Representa um indicador identificado durante uma investigação.
    """

    model_config = ConfigDict(extra="forbid")

    ioc_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do IOC dentro do caso.",
    )

    indicator_type: IndicatorType = Field(
        ...,
        description="Tipo do indicador.",
    )

    value: str = Field(
        ...,
        min_length=1,
        description="Valor do indicador.",
    )

    source: str | None = Field(
        default=None,
        description="Origem que forneceu ou identificou o IOC.",
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança no indicador, entre 0 e 100.",
    )

    malicious_confirmed: bool = Field(
        default=False,
        description=(
            "Indica se alguma fonte autorizada confirmou "
            "o indicador como malicioso."
        ),
    )

    reputation: str | None = Field(
        default=None,
        description="Reputação retornada por fonte de Threat Intelligence.",
    )

    first_seen: datetime | None = Field(
        default=None,
        description="Primeiro momento conhecido de observação do indicador.",
    )

    last_seen: datetime | None = Field(
        default=None,
        description="Último momento conhecido de observação do indicador.",
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Tags associadas ao indicador.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais obtidos durante o enriquecimento.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        """
        Impede IOC vazio ou contendo somente espaços.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "O valor do IOC não pode estar vazio."
            )

        return cleaned_value