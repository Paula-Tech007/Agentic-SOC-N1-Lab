"""
Configuração segura da integração MISP
do Agentic SOC N1 Lab.

Fase 4.1 — Threat Intelligence / MISP.

As informações sensíveis não ficam gravadas
no código-fonte.

Variáveis de ambiente utilizadas:

- MISP_URL
- MISP_API_KEY
- MISP_VERIFY_SSL
- MISP_TIMEOUT_SECONDS

Princípios:

- nenhuma API key hardcoded;
- fail-closed para configuração inválida;
- SSL habilitado por padrão;
- timeout limitado;
- representação do objeto não expõe a API key.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlparse


DEFAULT_MISP_TIMEOUT_SECONDS = 15

MIN_MISP_TIMEOUT_SECONDS = 1

MAX_MISP_TIMEOUT_SECONDS = 60


def _parse_boolean(
    value: str | None,
    *,
    default: bool,
) -> bool:
    """
    Converte variável de ambiente textual
    em valor booleano.

    Valores aceitos como True:

    - 1
    - true
    - yes
    - y
    - on

    Valores aceitos como False:

    - 0
    - false
    - no
    - n
    - off
    """

    if value is None:
        return default

    normalized = value.strip().lower()

    true_values = {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

    false_values = {
        "0",
        "false",
        "no",
        "n",
        "off",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise ValueError(
        "Valor booleano inválido para configuração "
        f"do MISP: {value!r}."
    )


def _parse_timeout(
    value: str | None,
) -> int:
    """
    Converte e valida o timeout do MISP.
    """

    if value is None:
        return DEFAULT_MISP_TIMEOUT_SECONDS

    try:
        timeout = int(
            value.strip()
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "MISP_TIMEOUT_SECONDS precisa ser "
            "um número inteiro."
        ) from error

    if not (
        MIN_MISP_TIMEOUT_SECONDS
        <= timeout
        <= MAX_MISP_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "MISP_TIMEOUT_SECONDS precisa estar "
            f"entre {MIN_MISP_TIMEOUT_SECONDS} "
            f"e {MAX_MISP_TIMEOUT_SECONDS} segundos."
        )

    return timeout


def _normalize_url(
    value: str,
) -> str:
    """
    Normaliza e valida a URL base do MISP.
    """

    normalized = value.strip().rstrip("/")

    if not normalized:
        raise ValueError(
            "MISP_URL não pode ser vazia."
        )

    parsed = urlparse(
        normalized
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "MISP_URL precisa utilizar "
            "http:// ou https://."
        )

    if not parsed.netloc:
        raise ValueError(
            "MISP_URL precisa possuir "
            "um host válido."
        )

    return normalized


@dataclass(
    frozen=True,
    slots=True,
)
class MISPConfig:
    """
    Configuração imutável da integração MISP.
    """

    base_url: str

    api_key: str = field(
        repr=False,
    )

    verify_ssl: bool = True

    timeout_seconds: int = (
        DEFAULT_MISP_TIMEOUT_SECONDS
    )

    @classmethod
    def from_env(
        cls,
    ) -> "MISPConfig":
        """
        Monta a configuração usando
        variáveis de ambiente.

        Fail-closed:
        MISP_URL e MISP_API_KEY são obrigatórias.
        """

        raw_url = os.getenv(
            "MISP_URL"
        )

        raw_api_key = os.getenv(
            "MISP_API_KEY"
        )

        if raw_url is None:
            raise ValueError(
                "Variável de ambiente "
                "MISP_URL não configurada."
            )

        if raw_api_key is None:
            raise ValueError(
                "Variável de ambiente "
                "MISP_API_KEY não configurada."
            )

        api_key = raw_api_key.strip()

        if not api_key:
            raise ValueError(
                "MISP_API_KEY não pode ser vazia."
            )

        base_url = _normalize_url(
            raw_url
        )

        verify_ssl = _parse_boolean(
            os.getenv(
                "MISP_VERIFY_SSL"
            ),
            default=True,
        )

        timeout_seconds = _parse_timeout(
            os.getenv(
                "MISP_TIMEOUT_SECONDS"
            )
        )

        return cls(
            base_url=base_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            timeout_seconds=timeout_seconds,
        )

    @property
    def authorization_headers(
        self,
    ) -> dict[str, str]:
        """
        Retorna os headers necessários
        para autenticação na API do MISP.

        O valor nunca deve ser registrado
        diretamente em logs.
        """

        return {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna somente informações seguras
        para diagnóstico e logs.

        A API key nunca é incluída.
        """

        return {
            "base_url": self.base_url,
            "verify_ssl": self.verify_ssl,
            "timeout_seconds": self.timeout_seconds,
            "api_key_configured": bool(
                self.api_key
            ),
        }