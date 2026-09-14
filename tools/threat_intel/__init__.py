"""
Camada de Threat Intelligence
do Agentic SOC N1 Lab.

Fase 4.1 — Integração MISP.

Este pacote fornece:

- configuração segura do MISP;
- cliente HTTP read-only;
- handlers oficiais para ToolRuntime.

Operações autorizadas:

- misp.search_ioc;
- misp.get_event;
- misp.get_attribute.

Nenhuma operação de escrita no MISP
é disponibilizada por este pacote.
"""

from tools.threat_intel.misp_client import (
    MISPClient,
    MISPClientError,
    MISPConnectionError,
    MISPHTTPError,
    MISPResponseError,
    MISPTimeoutError,
)
from tools.threat_intel.misp_config import (
    DEFAULT_MISP_TIMEOUT_SECONDS,
    MAX_MISP_TIMEOUT_SECONDS,
    MIN_MISP_TIMEOUT_SECONDS,
    MISPConfig,
)
from tools.threat_intel.misp_handlers import (
    MISPToolHandlers,
)


__all__ = [
    "DEFAULT_MISP_TIMEOUT_SECONDS",
    "MAX_MISP_TIMEOUT_SECONDS",
    "MIN_MISP_TIMEOUT_SECONDS",
    "MISPClient",
    "MISPClientError",
    "MISPConfig",
    "MISPConnectionError",
    "MISPHTTPError",
    "MISPResponseError",
    "MISPTimeoutError",
    "MISPToolHandlers",
]