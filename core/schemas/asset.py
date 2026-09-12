"""
Schema oficial de ativos do Agentic SOC N1 Lab.

Representa o contexto de um dispositivo, servidor, endpoint
ou outro ativo relacionado a uma investigação SOC.

Este schema será utilizado principalmente pelo
AG-06 Asset Context Agent.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.schemas.enums import Severity


class AssetContext(BaseModel):
    """
    Contexto de um ativo relacionado ao incidente.
    """

    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do ativo dentro do caso.",
    )

    hostname: str = Field(
        ...,
        min_length=1,
        description="Hostname do ativo investigado.",
    )

    asset_type: str | None = Field(
        default=None,
        description=(
            "Tipo do ativo, por exemplo endpoint, server, "
            "workstation ou cloud-instance."
        ),
    )

    operating_system: str | None = Field(
        default=None,
        description="Sistema operacional conhecido do ativo.",
    )

    criticality: Severity = Field(
        default=Severity.MEDIUM,
        description="Criticidade operacional do ativo.",
    )

    owner: str | None = Field(
        default=None,
        description="Responsável ou proprietário conhecido do ativo.",
    )

    department: str | None = Field(
        default=None,
        description="Departamento associado ao ativo.",
    )

    environment: str | None = Field(
        default=None,
        description=(
            "Ambiente do ativo, por exemplo production, "
            "development ou laboratory."
        ),
    )

    internet_exposed: bool | None = Field(
        default=None,
        description=(
            "Indica se o ativo possui exposição conhecida à Internet. "
            "None significa não verificado."
        ),
    )

    managed: bool | None = Field(
        default=None,
        description=(
            "Indica se o ativo é gerenciado pela organização. "
            "None significa não verificado."
        ),
    )

    edr_installed: bool | None = Field(
        default=None,
        description=(
            "Indica se há EDR confirmado no ativo. "
            "None significa não verificado."
        ),
    )

    ip_addresses: list[str] = Field(
        default_factory=list,
        description="Endereços IP associados ao ativo.",
    )

    source: str | None = Field(
        default=None,
        description="Fonte utilizada para consultar o ativo.",
    )

    confidence: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Confiança nas informações coletadas.",
    )

    risk_factors: list[str] = Field(
        default_factory=list,
        description="Fatores de risco encontrados no ativo.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais retornados pela fonte.",
    )

    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        """
        Remove espaços extras e impede hostname vazio.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "O hostname não pode estar vazio."
            )

        return cleaned_value