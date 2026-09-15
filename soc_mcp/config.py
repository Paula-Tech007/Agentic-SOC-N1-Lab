"""
Configuração da camada MCP
do Agentic SOC N1 Lab.

Fase 6.0 — Fundação MCP.

Esta configuração controla exclusivamente
a implementação MCP do projeto.

O pacote oficial do SDK utiliza:

    mcp

A implementação própria utiliza:

    soc_mcp

Objetivos desta fase:

- manter o MCP local;
- utilizar transporte STDIO;
- impedir exposição de rede por padrão;
- manter política defensiva;
- preservar fail-closed;
- não executar ações críticas;
- preparar integração futura com ToolRuntime.

O MCP não substitui as políticas existentes
do Agentic SOC N1 Lab.

A autorização continua pertencendo às
camadas de governança e ToolRuntime.
"""

from __future__ import annotations

import os

from dataclasses import (
    dataclass,
)


DEFAULT_MCP_SERVER_NAME = (
    "agentic-soc-n1-lab"
)

DEFAULT_MCP_SERVER_VERSION = (
    "0.1.0"
)

DEFAULT_MCP_TRANSPORT = (
    "stdio"
)

DEFAULT_MCP_TIMEOUT_SECONDS = 30

MIN_MCP_TIMEOUT_SECONDS = 1

MAX_MCP_TIMEOUT_SECONDS = 120

SUPPORTED_MCP_TRANSPORTS = (
    "stdio",
)


def _required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Normaliza e valida uma string
    obrigatória.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{field_name} não pode "
            "ser vazio."
        )

    return cleaned


def _normalize_server_name(
    value: object,
) -> str:
    """
    Valida o nome lógico do servidor.
    """

    cleaned = _required_string(
        value,
        field_name="server_name",
    )

    if len(cleaned) > 128:
        raise ValueError(
            "server_name não pode "
            "exceder 128 caracteres."
        )

    return cleaned


def _normalize_server_version(
    value: object,
) -> str:
    """
    Valida a versão lógica
    do servidor MCP.
    """

    cleaned = _required_string(
        value,
        field_name="server_version",
    )

    if len(cleaned) > 64:
        raise ValueError(
            "server_version não pode "
            "exceder 64 caracteres."
        )

    return cleaned


def _normalize_transport(
    value: object,
) -> str:
    """
    Aceita somente transportes
    explicitamente autorizados.

    A Fase 6 inicia somente com STDIO.
    """

    cleaned = _required_string(
        value,
        field_name="transport",
    ).lower()

    if (
        cleaned
        not in SUPPORTED_MCP_TRANSPORTS
    ):
        raise ValueError(
            "Transporte MCP não autorizado. "
            "Nesta fase somente 'stdio' "
            "é permitido."
        )

    return cleaned


def _normalize_timeout(
    value: object,
) -> int:
    """
    Valida timeout do MCP.
    """

    if isinstance(
        value,
        bool,
    ):
        raise ValueError(
            "timeout_seconds precisa "
            "ser inteiro."
        )

    if isinstance(
        value,
        str,
    ):
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "timeout_seconds não pode "
                "ser vazio."
            )

        try:
            normalized = int(
                cleaned
            )
        except ValueError as exc:
            raise ValueError(
                "timeout_seconds precisa "
                "ser inteiro."
            ) from exc

    elif isinstance(
        value,
        int,
    ):
        normalized = value

    else:
        raise ValueError(
            "timeout_seconds precisa "
            "ser inteiro."
        )

    if (
        normalized
        < MIN_MCP_TIMEOUT_SECONDS
        or normalized
        > MAX_MCP_TIMEOUT_SECONDS
    ):
        raise ValueError(
            "timeout_seconds precisa estar "
            f"entre {MIN_MCP_TIMEOUT_SECONDS} "
            f"e {MAX_MCP_TIMEOUT_SECONDS}."
        )

    return normalized


@dataclass(
    frozen=True,
    slots=True,
)
class MCPConfig:
    """
    Configuração segura do MCP
    do Agentic SOC N1 Lab.

    A fundação da Fase 6 utiliza:

    - STDIO;
    - execução local;
    - política read-only;
    - fail-closed;
    - nenhuma exposição de rede.
    """

    server_name: str = (
        DEFAULT_MCP_SERVER_NAME
    )

    server_version: str = (
        DEFAULT_MCP_SERVER_VERSION
    )

    transport: str = (
        DEFAULT_MCP_TRANSPORT
    )

    timeout_seconds: int = (
        DEFAULT_MCP_TIMEOUT_SECONDS
    )

    local_only: bool = True

    read_only: bool = True

    fail_closed: bool = True

    allow_network_transport: bool = False

    allow_critical_actions: bool = False

    def __post_init__(
        self,
    ) -> None:
        """
        Valida inclusive construção direta.
        """

        object.__setattr__(
            self,
            "server_name",
            _normalize_server_name(
                self.server_name
            ),
        )

        object.__setattr__(
            self,
            "server_version",
            _normalize_server_version(
                self.server_version
            ),
        )

        object.__setattr__(
            self,
            "transport",
            _normalize_transport(
                self.transport
            ),
        )

        object.__setattr__(
            self,
            "timeout_seconds",
            _normalize_timeout(
                self.timeout_seconds
            ),
        )

        if self.local_only is not True:
            raise ValueError(
                "MCP precisa permanecer "
                "local nesta fase."
            )

        if self.read_only is not True:
            raise ValueError(
                "MCP precisa permanecer "
                "READ_ONLY nesta fase."
            )

        if self.fail_closed is not True:
            raise ValueError(
                "MCP precisa operar "
                "em fail-closed."
            )

        if (
            self.allow_network_transport
            is not False
        ):
            raise ValueError(
                "Transporte MCP de rede "
                "não está autorizado "
                "nesta fase."
            )

        if (
            self.allow_critical_actions
            is not False
        ):
            raise ValueError(
                "Ações críticas autônomas "
                "não estão autorizadas."
            )

    @classmethod
    def from_env(
        cls,
    ) -> "MCPConfig":
        """
        Carrega somente parâmetros
        não críticos do ambiente.

        Variáveis:

        SOC_MCP_SERVER_NAME
        SOC_MCP_SERVER_VERSION
        SOC_MCP_TRANSPORT
        SOC_MCP_TIMEOUT_SECONDS

        Flags de segurança não podem
        ser liberadas por variável
        de ambiente.
        """

        return cls(
            server_name=os.getenv(
                "SOC_MCP_SERVER_NAME",
                DEFAULT_MCP_SERVER_NAME,
            ),
            server_version=os.getenv(
                "SOC_MCP_SERVER_VERSION",
                DEFAULT_MCP_SERVER_VERSION,
            ),
            transport=os.getenv(
                "SOC_MCP_TRANSPORT",
                DEFAULT_MCP_TRANSPORT,
            ),
            timeout_seconds=os.getenv(
                "SOC_MCP_TIMEOUT_SECONDS",
                str(
                    DEFAULT_MCP_TIMEOUT_SECONDS
                ),
            ),
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna somente informações
        seguras da configuração.
        """

        return {
            "integration": "MCP",
            "implementation": (
                "AGENTIC_SOC_N1_LAB"
            ),
            "server_name": (
                self.server_name
            ),
            "server_version": (
                self.server_version
            ),
            "transport": (
                self.transport
            ),
            "timeout_seconds": (
                self.timeout_seconds
            ),
            "local_only": (
                self.local_only
            ),
            "read_only": (
                self.read_only
            ),
            "fail_closed": (
                self.fail_closed
            ),
            "network_transport": (
                self.allow_network_transport
            ),
            "critical_actions": (
                self.allow_critical_actions
            ),
        }