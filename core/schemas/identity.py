"""
Schema oficial de identidade do Agentic SOC N1 Lab.

Representa o contexto de uma conta ou usuário analisado
pelo Identity Analyst Agent.

Regra importante:

None  = informação ainda desconhecida.
False = informação verificada e negativa.
True  = informação verificada e positiva.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IdentityContext(BaseModel):
    """
    Contexto de identidade associado a uma investigação SOC.
    """

    model_config = ConfigDict(extra="forbid")

    identity_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da identidade dentro do caso.",
    )

    username: str = Field(
        ...,
        min_length=1,
        description="Nome de usuário da conta investigada.",
    )

    email: str | None = Field(
        default=None,
        description="E-mail associado à conta.",
    )

    display_name: str | None = Field(
        default=None,
        description="Nome de exibição do usuário.",
    )

    account_exists: bool | None = Field(
        default=None,
        description=(
            "True se a conta foi confirmada como existente, "
            "False se foi confirmada como inexistente e "
            "None se ainda não foi verificada."
        ),
    )

    account_enabled: bool | None = Field(
        default=None,
        description=(
            "Estado da conta. None significa que ainda não foi verificado."
        ),
    )

    privileged: bool | None = Field(
        default=None,
        description="Indica se a conta possui privilégios elevados.",
    )

    mfa_enabled: bool | None = Field(
        default=None,
        description="Indica se MFA está habilitado para a conta.",
    )

    department: str | None = Field(
        default=None,
        description="Departamento ou área associada ao usuário.",
    )

    role: str | None = Field(
        default=None,
        description="Função ou cargo associado à identidade.",
    )

    last_login: datetime | None = Field(
        default=None,
        description="Último login conhecido da conta.",
    )

    failed_login_count: int | None = Field(
        default=None,
        ge=0,
        description="Quantidade conhecida de tentativas de login falhas.",
    )

    source: str | None = Field(
        default=None,
        description="Fonte utilizada para consultar a identidade.",
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança nas informações coletadas.",
    )

    risk_factors: list[str] = Field(
        default_factory=list,
        description="Fatores de risco encontrados na identidade.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Informações adicionais retornadas pela fonte.",
    )

    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """
        Remove espaços extras e impede username vazio.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "O username não pode estar vazio."
            )

        return cleaned_value