"""
Configuração oficial da integração Asset / CMDB.

Fase 4.4 do Agentic SOC N1 Lab.

Esta configuração representa uma integração genérica e
somente leitura para consulta de contexto de ativos.

Nenhuma operação de escrita, alteração, exclusão,
isolamento ou contenção é permitida nesta fase.

Princípios:

- nenhuma credencial é gravada no código;
- nenhum segredo aparece no repr;
- nenhum segredo aparece no safe_summary;
- somente URLs HTTP/HTTPS são aceitas;
- integração exclusivamente READ_ONLY;
- configuração imutável após criação.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit


DEFAULT_ASSET_TIMEOUT_SECONDS = 15
MIN_ASSET_TIMEOUT_SECONDS = 1
MAX_ASSET_TIMEOUT_SECONDS = 60

DEFAULT_ASSET_PROVIDER = "GENERIC"

OFFICIAL_ASSET_OPERATIONS: tuple[str, ...] = (
    "get_asset",
    "get_ip_context",
    "get_criticality",
    "get_edr_status",
)


def _parse_boolean(
    value: str | None,
    *,
    default: bool,
) -> bool:
    """
    Converte variável textual de ambiente para booleano.
    """

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "sim",
        "s",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "n",
        "off",
        "nao",
        "não",
    }:
        return False

    raise ValueError(
        "Valor booleano inválido para configuração Asset: "
        f"{value!r}."
    )


def _parse_timeout(
    value: str | None,
) -> int:
    """
    Converte e valida timeout da integração Asset.
    """

    if value is None:
        return DEFAULT_ASSET_TIMEOUT_SECONDS

    try:
        timeout = int(
            value.strip()
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "ASSET_TIMEOUT_SECONDS precisa ser "
            "um número inteiro."
        ) from exc

    if not (
        MIN_ASSET_TIMEOUT_SECONDS
        <= timeout
        <= MAX_ASSET_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "ASSET_TIMEOUT_SECONDS precisa estar entre "
            f"{MIN_ASSET_TIMEOUT_SECONDS} e "
            f"{MAX_ASSET_TIMEOUT_SECONDS} segundos."
        )

    return timeout


def _normalize_url(
    value: str,
) -> str:
    """
    Normaliza e valida a URL base da integração Asset.
    """

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "ASSET_URL precisa ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            "ASSET_URL não pode estar vazia."
        )

    parsed = urlsplit(
        cleaned
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "ASSET_URL precisa utilizar http ou https."
        )

    if not parsed.hostname:
        raise ValueError(
            "ASSET_URL precisa possuir um host válido."
        )

    if parsed.username is not None:
        raise ValueError(
            "ASSET_URL não pode conter usuário embutido."
        )

    if parsed.password is not None:
        raise ValueError(
            "ASSET_URL não pode conter senha embutida."
        )

    if parsed.query:
        raise ValueError(
            "ASSET_URL não pode conter query string."
        )

    if parsed.fragment:
        raise ValueError(
            "ASSET_URL não pode conter fragmento."
        )

    normalized_path = (
        parsed.path.rstrip("/")
    )

    if normalized_path:
        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"{normalized_path}"
        )

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )


def _normalize_provider(
    value: str | None,
) -> str:
    """
    Normaliza o identificador do provedor Asset / CMDB.
    """

    if value is None:
        return DEFAULT_ASSET_PROVIDER

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "ASSET_PROVIDER precisa ser uma string."
        )

    cleaned = value.strip().upper()

    if not cleaned:
        return DEFAULT_ASSET_PROVIDER

    if len(cleaned) > 64:
        raise ValueError(
            "ASSET_PROVIDER não pode possuir "
            "mais de 64 caracteres."
        )

    return cleaned


@dataclass(
    frozen=True,
    slots=True,
)
class AssetConfig:
    """
    Configuração imutável da integração Asset / CMDB.
    """

    base_url: str

    api_token: str = field(
        repr=False,
    )

    provider: str = (
        DEFAULT_ASSET_PROVIDER
    )

    verify_ssl: bool = True

    timeout_seconds: int = (
        DEFAULT_ASSET_TIMEOUT_SECONDS
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida também configurações criadas
        diretamente pelo código.
        """

        normalized_url = _normalize_url(
            self.base_url
        )

        object.__setattr__(
            self,
            "base_url",
            normalized_url,
        )

        if not isinstance(
            self.api_token,
            str,
        ):
            raise TypeError(
                "api_token precisa ser uma string."
            )

        normalized_token = (
            self.api_token.strip()
        )

        if not normalized_token:
            raise ValueError(
                "api_token não pode estar vazio."
            )

        object.__setattr__(
            self,
            "api_token",
            normalized_token,
        )

        normalized_provider = (
            _normalize_provider(
                self.provider
            )
        )

        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )

        if not isinstance(
            self.verify_ssl,
            bool,
        ):
            raise TypeError(
                "verify_ssl precisa ser booleano."
            )

        if not isinstance(
            self.timeout_seconds,
            int,
        ) or isinstance(
            self.timeout_seconds,
            bool,
        ):
            raise TypeError(
                "timeout_seconds precisa ser inteiro."
            )

        if not (
            MIN_ASSET_TIMEOUT_SECONDS
            <= self.timeout_seconds
            <= MAX_ASSET_TIMEOUT_SECONDS
        ):
            raise ValueError(
                "timeout_seconds precisa estar entre "
                f"{MIN_ASSET_TIMEOUT_SECONDS} e "
                f"{MAX_ASSET_TIMEOUT_SECONDS} segundos."
            )

    @classmethod
    def from_env(
        cls,
    ) -> "AssetConfig":
        """
        Carrega configuração Asset a partir do ambiente.
        """

        raw_url = os.getenv(
            "ASSET_URL"
        )

        if raw_url is None:
            raise ValueError(
                "ASSET_URL não foi configurada."
            )

        raw_token = os.getenv(
            "ASSET_API_TOKEN"
        )

        if raw_token is None:
            raise ValueError(
                "ASSET_API_TOKEN não foi configurado."
            )

        return cls(
            base_url=_normalize_url(
                raw_url
            ),
            api_token=raw_token.strip(),
            provider=_normalize_provider(
                os.getenv(
                    "ASSET_PROVIDER"
                )
            ),
            verify_ssl=_parse_boolean(
                os.getenv(
                    "ASSET_VERIFY_SSL"
                ),
                default=True,
            ),
            timeout_seconds=_parse_timeout(
                os.getenv(
                    "ASSET_TIMEOUT_SECONDS"
                )
            ),
        )

    @property
    def authorization_headers(
        self,
    ) -> dict[str, str]:
        """
        Headers utilizados pelo cliente Asset.

        O token não deve ser registrado em logs.
        """

        return {
            "Authorization": (
                f"Bearer {self.api_token}"
            ),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @property
    def allowed_operations(
        self,
    ) -> tuple[str, ...]:
        """
        Operações oficiais permitidas nesta integração.
        """

        return OFFICIAL_ASSET_OPERATIONS

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna informações seguras para
        diagnóstico e auditoria.

        Nenhum segredo é retornado.
        """

        return {
            "integration": "ASSET",
            "provider": self.provider,
            "base_url": self.base_url,
            "verify_ssl": self.verify_ssl,
            "timeout_seconds": (
                self.timeout_seconds
            ),
            "api_token_configured": True,
            "access_mode": "READ_ONLY",
            "allowed_operations": (
                self.allowed_operations
            ),
        }