"""
Configuração segura da integração Identity / IAM
do Agentic SOC N1 Lab.

Fase 4.3 — Identity / IAM read-only.

Este módulo centraliza:

- URL do serviço IAM;
- token de autenticação;
- identificação do provedor;
- verificação SSL;
- timeout HTTP;
- headers de autenticação;
- resumo seguro da configuração.

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
from urllib.parse import urlparse


DEFAULT_IAM_TIMEOUT_SECONDS = 15
MIN_IAM_TIMEOUT_SECONDS = 1
MAX_IAM_TIMEOUT_SECONDS = 60

DEFAULT_IAM_PROVIDER = "GENERIC"


def _parse_boolean(
    value: str | None,
    *,
    default: bool,
) -> bool:
    """
    Converte valor textual de variável de ambiente
    para booleano.

    Valores verdadeiros:

    - true
    - 1
    - yes
    - y
    - on

    Valores falsos:

    - false
    - 0
    - no
    - n
    - off
    """

    if value is None:
        return default

    normalized = value.strip().lower()

    true_values = {
        "true",
        "1",
        "yes",
        "y",
        "on",
    }

    false_values = {
        "false",
        "0",
        "no",
        "n",
        "off",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise ValueError(
        "Valor booleano inválido: "
        f"{value!r}."
    )


def _parse_timeout(
    value: str | None,
) -> int:
    """
    Converte e valida o timeout da integração IAM.
    """

    if value is None:
        return DEFAULT_IAM_TIMEOUT_SECONDS

    try:
        timeout = int(
            value.strip()
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "IAM_TIMEOUT_SECONDS precisa "
            "ser um número inteiro."
        ) from exc

    if not (
        MIN_IAM_TIMEOUT_SECONDS
        <= timeout
        <= MAX_IAM_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "IAM_TIMEOUT_SECONDS precisa estar "
            f"entre {MIN_IAM_TIMEOUT_SECONDS} "
            f"e {MAX_IAM_TIMEOUT_SECONDS} segundos."
        )

    return timeout


def _normalize_url(
    value: str,
) -> str:
    """
    Normaliza e valida a URL base do serviço IAM.
    """

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "IAM_URL precisa ser string."
        )

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            "IAM_URL não pode ser vazia."
        )

    parsed = urlparse(
        normalized
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "IAM_URL precisa utilizar "
            "http ou https."
        )

    if not parsed.netloc:
        raise ValueError(
            "IAM_URL precisa possuir "
            "host válido."
        )

    if (
        parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError(
            "IAM_URL não pode conter "
            "credenciais embutidas."
        )

    if parsed.query:
        raise ValueError(
            "IAM_URL não pode conter "
            "query string."
        )

    if parsed.fragment:
        raise ValueError(
            "IAM_URL não pode conter fragmento."
        )

    return normalized.rstrip("/")


def _normalize_provider(
    value: str | None,
) -> str:
    """
    Normaliza o nome lógico do provedor IAM.
    """

    if value is None:
        return DEFAULT_IAM_PROVIDER

    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "IAM_PROVIDER precisa ser string."
        )

    normalized = value.strip().upper()

    if not normalized:
        return DEFAULT_IAM_PROVIDER

    if len(normalized) > 64:
        raise ValueError(
            "IAM_PROVIDER não pode possuir "
            "mais de 64 caracteres."
        )

    return normalized


@dataclass(
    frozen=True,
    slots=True,
)
class IdentityConfig:
    """
    Configuração imutável da integração IAM.

    O token é marcado com repr=False para impedir
    exposição acidental em logs e debugging.
    """

    base_url: str

    api_token: str = field(
        repr=False
    )

    provider: str = (
        DEFAULT_IAM_PROVIDER
    )

    verify_ssl: bool = True

    timeout_seconds: int = (
        DEFAULT_IAM_TIMEOUT_SECONDS
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
                "api_token precisa ser string."
            )

        normalized_token = (
            self.api_token.strip()
        )

        if not normalized_token:
            raise ValueError(
                "api_token não pode ser vazio."
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
        ):
            raise TypeError(
                "timeout_seconds precisa "
                "ser inteiro."
            )

        if not (
            MIN_IAM_TIMEOUT_SECONDS
            <= self.timeout_seconds
            <= MAX_IAM_TIMEOUT_SECONDS
        ):
            raise ValueError(
                "timeout_seconds precisa estar "
                f"entre {MIN_IAM_TIMEOUT_SECONDS} "
                f"e {MAX_IAM_TIMEOUT_SECONDS}."
            )

    @classmethod
    def from_env(
        cls,
    ) -> "IdentityConfig":
        """
        Cria configuração a partir de
        variáveis de ambiente.

        Variáveis obrigatórias:

        IAM_URL
        IAM_API_TOKEN

        Variáveis opcionais:

        IAM_PROVIDER
        IAM_VERIFY_SSL
        IAM_TIMEOUT_SECONDS
        """

        raw_url = os.getenv(
            "IAM_URL"
        )

        raw_token = os.getenv(
            "IAM_API_TOKEN"
        )

        if (
            raw_url is None
            or not raw_url.strip()
        ):
            raise ValueError(
                "Variável de ambiente "
                "IAM_URL não configurada."
            )

        if (
            raw_token is None
            or not raw_token.strip()
        ):
            raise ValueError(
                "Variável de ambiente "
                "IAM_API_TOKEN não configurada."
            )

        return cls(
            base_url=_normalize_url(
                raw_url
            ),
            api_token=raw_token.strip(),
            provider=_normalize_provider(
                os.getenv(
                    "IAM_PROVIDER"
                )
            ),
            verify_ssl=_parse_boolean(
                os.getenv(
                    "IAM_VERIFY_SSL"
                ),
                default=True,
            ),
            timeout_seconds=_parse_timeout(
                os.getenv(
                    "IAM_TIMEOUT_SECONDS"
                )
            ),
        )

    @property
    def authorization_headers(
        self,
    ) -> dict[str, str]:
        """
        Headers HTTP utilizados pelo futuro
        IdentityClient.

        O token nunca deve ser registrado
        em logs ou evidências.
        """

        return {
            "Authorization": (
                f"Bearer {self.api_token}"
            ),
            "Accept": "application/json",
            "Content-Type": (
                "application/json"
            ),
        }

    @property
    def allowed_operations(
        self,
    ) -> tuple[str, ...]:
        """
        Operações IAM permitidas nesta fase.

        Todas são estritamente read-only.
        """

        return (
            "get_user",
            "get_account_status",
            "get_mfa_status",
            "get_group_membership",
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna informações seguras para
        diagnóstico e auditoria.

        Nenhum segredo é retornado.
        """

        return {
            "integration": "IAM",
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