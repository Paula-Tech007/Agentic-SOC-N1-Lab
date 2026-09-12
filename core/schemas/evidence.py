"""
Schema oficial de evidências do Agentic SOC N1 Lab.

Uma evidência representa um dado observável utilizado
durante uma investigação.

Cada evidência registra:

- o que foi observado;
- de onde veio;
- qual agente coletou;
- qual ferramenta foi utilizada;
- nível de confiança;
- referências relacionadas.

As evidências serão tratadas como registros imutáveis.
A política append-only será aplicada posteriormente
no Case State.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import EvidenceType


class Evidence(BaseModel):
    """
    Registro oficial de evidência de uma investigação SOC.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    evidence_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da evidência.",
    )

    evidence_type: EvidenceType = Field(
        ...,
        description="Categoria da evidência.",
    )

    title: str = Field(
        ...,
        min_length=1,
        description="Título curto da evidência.",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Descrição objetiva do que foi observado.",
    )

    source_agent: str | None = Field(
        default=None,
        description="Agente responsável pela coleta ou registro.",
    )

    source_tool: str | None = Field(
        default=None,
        description="Ferramenta utilizada para obter a evidência.",
    )

    source_system: str | None = Field(
        default=None,
        description="Sistema ou fonte externa de origem do dado.",
    )

    verified: bool | None = Field(
        default=None,
        description=(
            "True significa evidência verificada. "
            "False significa verificada como inválida. "
            "None significa ainda não verificada."
        ),
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança atribuída à evidência.",
    )

    observed_at: datetime | None = Field(
        default=None,
        description="Momento em que o evento ou fato foi observado.",
    )

    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Momento em que a evidência foi registrada no SOC.",
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Dados estruturados associados à evidência.",
    )

    references: list[str] = Field(
        default_factory=list,
        description=(
            "IDs relacionados, como IOC, usuário, ativo, alerta "
            "ou outra evidência."
        ),
    )

    @field_validator("title", "description")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        Remove espaços extras e impede texto vazio.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Título e descrição da evidência não podem estar vazios."
            )

        return cleaned_value