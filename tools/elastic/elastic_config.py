"""
Configuração segura da integração Elastic / Elasticsearch
do Agentic SOC N1 Lab.

Fase 4.2 — Elastic / Elasticsearch read-only.

Variáveis de ambiente utilizadas:

- ELASTIC_URL
- ELASTIC_API_KEY
- ELASTIC_VERIFY_SSL
- ELASTIC_TIMEOUT_SECONDS
- ELASTIC_ALERTS_INDEX
- ELASTIC_EVENTS_INDEX

Princípios:

- nenhuma credencial hardcoded;
- configuração imutável;
- SSL habilitado por padrão;
- timeout limitado;
- índices definidos explicitamente;
- nenhuma API key aparece em repr ou logs;
- fail-closed para configuração inválida.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlparse


DEFAULT_ELASTIC_TIMEOUT_SECONDS = 20

MIN_ELASTIC_TIMEOUT_SECONDS = 1

MAX_ELASTIC_TIMEOUT_SECONDS = 60


def _parse_boolean(
    value: str | None,
    *,
    default: bool,
) -> bool:
    """
    Converte variável textual para booleano.
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
        "Valor booleano inválido para "
        f"configuração do Elastic: {value!r}."
    )


def _parse_timeout(
    value: str | None,
) -> int:
    """
    Converte e valida o timeout do Elastic.
    """

    if value is None:
        return DEFAULT_ELASTIC_TIMEOUT_SECONDS

    try:
        timeout = int(
            value.strip()
        )

    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "ELASTIC_TIMEOUT_SECONDS precisa "
            "ser um número inteiro."
        ) from error

    if not (
        MIN_ELASTIC_TIMEOUT_SECONDS
        <= timeout
        <= MAX_ELASTIC_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "ELASTIC_TIMEOUT_SECONDS precisa estar "
            f"entre {MIN_ELASTIC_TIMEOUT_SECONDS} "
            f"e {MAX_ELASTIC_TIMEOUT_SECONDS} segundos."
        )

    return timeout


def _normalize_url(
    value: str,
) -> str:
    """
    Normaliza e valida a URL base do Elastic.
    """

    normalized = value.strip().rstrip("/")

    if not normalized:
        raise ValueError(
            "ELASTIC_URL não pode ser vazia."
        )

    parsed = urlparse(
        normalized
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "ELASTIC_URL precisa utilizar "
            "http:// ou https://."
        )

    if not parsed.netloc:
        raise ValueError(
            "ELASTIC_URL precisa possuir "
            "um host válido."
        )

    return normalized


def _normalize_index(
    value: str,
    *,
    field_name: str,
) -> str:
    """
    Valida um índice ou padrão de índice
    utilizado exclusivamente para leitura.
    """

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} não pode ser vazio."
        )

    if len(normalized) > 255:
        raise ValueError(
            f"{field_name} excede o tamanho "
            "máximo permitido."
        )

    forbidden_fragments = (
        "/",
        "\\",
        "..",
        "?",
        "#",
    )

    if any(
        fragment in normalized
        for fragment in forbidden_fragments
    ):
        raise ValueError(
            f"{field_name} contém caracteres "
            "não permitidos."
        )

    return normalized


@dataclass(
    frozen=True,
    slots=True,
)
class ElasticConfig:
    """
    Configuração imutável da integração Elastic.
    """

    base_url: str

    api_key: str = field(
        repr=False,
    )

    alerts_index: str

    events_index: str

    verify_ssl: bool = True

    timeout_seconds: int = (
        DEFAULT_ELASTIC_TIMEOUT_SECONDS
    )

    @classmethod
    def from_env(
        cls,
    ) -> "ElasticConfig":
        """
        Monta a configuração pelas
        variáveis de ambiente.

        Fail-closed:
        URL, API key e índices são obrigatórios.
        """

        raw_url = os.getenv(
            "ELASTIC_URL"
        )

        raw_api_key = os.getenv(
            "ELASTIC_API_KEY"
        )

        raw_alerts_index = os.getenv(
            "ELASTIC_ALERTS_INDEX"
        )

        raw_events_index = os.getenv(
            "ELASTIC_EVENTS_INDEX"
        )

        if raw_url is None:
            raise ValueError(
                "Variável de ambiente "
                "ELASTIC_URL não configurada."
            )

        if raw_api_key is None:
            raise ValueError(
                "Variável de ambiente "
                "ELASTIC_API_KEY não configurada."
            )

        if raw_alerts_index is None:
            raise ValueError(
                "Variável de ambiente "
                "ELASTIC_ALERTS_INDEX não configurada."
            )

        if raw_events_index is None:
            raise ValueError(
                "Variável de ambiente "
                "ELASTIC_EVENTS_INDEX não configurada."
            )

        api_key = raw_api_key.strip()

        if not api_key:
            raise ValueError(
                "ELASTIC_API_KEY não pode ser vazia."
            )

        base_url = _normalize_url(
            raw_url
        )

        alerts_index = _normalize_index(
            raw_alerts_index,
            field_name=(
                "ELASTIC_ALERTS_INDEX"
            ),
        )

        events_index = _normalize_index(
            raw_events_index,
            field_name=(
                "ELASTIC_EVENTS_INDEX"
            ),
        )

        verify_ssl = _parse_boolean(
            os.getenv(
                "ELASTIC_VERIFY_SSL"
            ),
            default=True,
        )

        timeout_seconds = _parse_timeout(
            os.getenv(
                "ELASTIC_TIMEOUT_SECONDS"
            )
        )

        return cls(
            base_url=base_url,
            api_key=api_key,
            alerts_index=alerts_index,
            events_index=events_index,
            verify_ssl=verify_ssl,
            timeout_seconds=timeout_seconds,
        )

    @property
    def authorization_headers(
        self,
    ) -> dict[str, str]:
        """
        Headers usados na autenticação.

        A API key não deve ser registrada em logs.
        """

        return {
            "Authorization": (
                f"ApiKey {self.api_key}"
            ),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @property
    def allowed_indices(
        self,
    ) -> tuple[str, ...]:
        """
        Índices autorizados para leitura.
        """

        return (
            self.alerts_index,
            self.events_index,
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna somente informações seguras
        para diagnóstico.

        Nunca inclui a API key.
        """

        return {
            "base_url": self.base_url,
            "alerts_index": self.alerts_index,
            "events_index": self.events_index,
            "verify_ssl": self.verify_ssl,
            "timeout_seconds": self.timeout_seconds,
            "api_key_configured": bool(
                self.api_key
            ),
            "mode": "READ_ONLY",
        }