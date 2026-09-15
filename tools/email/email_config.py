"""
Configuração da integração Email / Phishing da Fase 4.5.

Esta integração é estritamente defensiva e somente leitura.

Variáveis de ambiente suportadas:

EMAIL_URL
EMAIL_API_TOKEN
EMAIL_PROVIDER
EMAIL_VERIFY_SSL
EMAIL_TIMEOUT_SECONDS

Princípios:

- credenciais nunca aparecem em repr;
- credenciais nunca aparecem em safe_summary;
- somente HTTP/HTTPS é permitido;
- URLs com credenciais embutidas são rejeitadas;
- query string e fragment são rejeitados na URL base;
- timeout possui limites explícitos;
- somente operações oficiais da Fase 4.5 são expostas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlparse


DEFAULT_EMAIL_TIMEOUT_SECONDS = 15
MIN_EMAIL_TIMEOUT_SECONDS = 1
MAX_EMAIL_TIMEOUT_SECONDS = 60
DEFAULT_EMAIL_PROVIDER = "GENERIC"


OFFICIAL_EMAIL_OPERATIONS: tuple[str, ...] = (
    "get_message_metadata",
    "get_headers",
    "get_authentication_results",
    "get_attachment_metadata",
)


def _parse_boolean(
    value: str | bool | None,
    *,
    default: bool,
) -> bool:
    """
    Converte valor textual de ambiente para bool.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise ValueError(
            "Valor booleano precisa ser string, bool ou None."
        )

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
        "Valor booleano inválido."
    )


def _parse_timeout(
    value: str | int | None,
) -> int:
    """
    Converte e valida timeout em segundos.
    """

    if value is None:
        return DEFAULT_EMAIL_TIMEOUT_SECONDS

    if isinstance(value, bool):
        raise ValueError(
            "EMAIL_TIMEOUT_SECONDS precisa ser inteiro."
        )

    if isinstance(value, int):
        timeout = value

    elif isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "EMAIL_TIMEOUT_SECONDS não pode ser vazio."
            )

        try:
            timeout = int(cleaned)

        except ValueError as exc:
            raise ValueError(
                "EMAIL_TIMEOUT_SECONDS precisa ser inteiro."
            ) from exc

    else:
        raise ValueError(
            "EMAIL_TIMEOUT_SECONDS precisa ser inteiro."
        )

    if (
        timeout < MIN_EMAIL_TIMEOUT_SECONDS
        or timeout > MAX_EMAIL_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "EMAIL_TIMEOUT_SECONDS precisa estar entre "
            f"{MIN_EMAIL_TIMEOUT_SECONDS} e "
            f"{MAX_EMAIL_TIMEOUT_SECONDS} segundos."
        )

    return timeout


def _normalize_url(
    value: str,
) -> str:
    """
    Valida e normaliza a URL base da integração.
    """

    if not isinstance(value, str):
        raise ValueError(
            "EMAIL_URL precisa ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            "EMAIL_URL não pode ser vazia."
        )

    parsed = urlparse(cleaned)

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "EMAIL_URL deve usar http ou https."
        )

    if not parsed.hostname:
        raise ValueError(
            "EMAIL_URL precisa possuir hostname válido."
        )

    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "EMAIL_URL não pode conter credenciais embutidas."
        )

    if parsed.query:
        raise ValueError(
            "EMAIL_URL não pode conter query string."
        )

    if parsed.fragment:
        raise ValueError(
            "EMAIL_URL não pode conter fragment."
        )

    return cleaned.rstrip("/")


def _normalize_token(
    value: str,
) -> str:
    """
    Valida o token utilizado na integração.
    """

    if not isinstance(value, str):
        raise ValueError(
            "EMAIL_API_TOKEN precisa ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            "EMAIL_API_TOKEN não pode ser vazio."
        )

    return cleaned


def _normalize_provider(
    value: str | None,
) -> str:
    """
    Normaliza o identificador do provedor de e-mail.
    """

    if value is None:
        return DEFAULT_EMAIL_PROVIDER

    if not isinstance(value, str):
        raise ValueError(
            "EMAIL_PROVIDER precisa ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        return DEFAULT_EMAIL_PROVIDER

    if len(cleaned) > 64:
        raise ValueError(
            "EMAIL_PROVIDER não pode exceder 64 caracteres."
        )

    return cleaned.upper()


@dataclass(
    frozen=True,
    slots=True,
)
class EmailConfig:
    """
    Configuração imutável da integração Email / Phishing.
    """

    base_url: str

    api_token: str = field(
        repr=False
    )

    provider: str = DEFAULT_EMAIL_PROVIDER

    verify_ssl: bool = True

    timeout_seconds: int = (
        DEFAULT_EMAIL_TIMEOUT_SECONDS
    )

    def __post_init__(self) -> None:
        """
        Valida também construções diretas da dataclass.
        """

        object.__setattr__(
            self,
            "base_url",
            _normalize_url(
                self.base_url
            ),
        )

        object.__setattr__(
            self,
            "api_token",
            _normalize_token(
                self.api_token
            ),
        )

        object.__setattr__(
            self,
            "provider",
            _normalize_provider(
                self.provider
            ),
        )

        if not isinstance(
            self.verify_ssl,
            bool,
        ):
            raise ValueError(
                "verify_ssl precisa ser bool."
            )

        object.__setattr__(
            self,
            "timeout_seconds",
            _parse_timeout(
                self.timeout_seconds
            ),
        )

    @classmethod
    def from_env(
        cls,
    ) -> "EmailConfig":
        """
        Carrega configuração das variáveis de ambiente.
        """

        base_url = os.getenv(
            "EMAIL_URL"
        )

        api_token = os.getenv(
            "EMAIL_API_TOKEN"
        )

        provider = os.getenv(
            "EMAIL_PROVIDER",
            DEFAULT_EMAIL_PROVIDER,
        )

        verify_ssl = _parse_boolean(
            os.getenv(
                "EMAIL_VERIFY_SSL"
            ),
            default=True,
        )

        timeout_seconds = _parse_timeout(
            os.getenv(
                "EMAIL_TIMEOUT_SECONDS"
            )
        )

        if base_url is None:
            raise ValueError(
                "EMAIL_URL não configurada."
            )

        if api_token is None:
            raise ValueError(
                "EMAIL_API_TOKEN não configurado."
            )

        return cls(
            base_url=base_url,
            api_token=api_token,
            provider=provider,
            verify_ssl=verify_ssl,
            timeout_seconds=timeout_seconds,
        )

    @property
    def authorization_headers(
        self,
    ) -> dict[str, str]:
        """
        Headers padrão de autenticação.
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
        Operações defensivas oficialmente suportadas.
        """

        return OFFICIAL_EMAIL_OPERATIONS

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro sem expor token.
        """

        return {
            "integration": "EMAIL",
            "provider": self.provider,
            "base_url": self.base_url,
            "verify_ssl": self.verify_ssl,
            "timeout_seconds": (
                self.timeout_seconds
            ),
            "api_token_configured": True,
            "access_mode": "READ_ONLY",
            "operations": (
                self.allowed_operations
            ),
        }