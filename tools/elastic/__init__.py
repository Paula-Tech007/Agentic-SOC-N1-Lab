"""
Camada Elastic / Elasticsearch
do Agentic SOC N1 Lab.

Fase 4.2 — Integração Elastic read-only.

Este pacote fornece:

- configuração segura do Elastic;
- cliente HTTP read-only;
- handlers oficiais para ToolRuntime.

Operações autorizadas:

- elastic.search_alerts;
- elastic.search_events;
- elastic.get_document.

Nenhuma operação de escrita, exclusão,
indexação ou administração do Elastic
é disponibilizada por este pacote.
"""

from tools.elastic.elastic_client import (
    ElasticClient,
    ElasticClientError,
    ElasticConnectionError,
    ElasticHTTPError,
    ElasticResponseError,
    ElasticTimeoutError,
)
from tools.elastic.elastic_config import (
    DEFAULT_ELASTIC_TIMEOUT_SECONDS,
    MAX_ELASTIC_TIMEOUT_SECONDS,
    MIN_ELASTIC_TIMEOUT_SECONDS,
    ElasticConfig,
)
from tools.elastic.elastic_handlers import (
    ElasticToolHandlers,
)


__all__ = [
    "DEFAULT_ELASTIC_TIMEOUT_SECONDS",
    "ElasticClient",
    "ElasticClientError",
    "ElasticConfig",
    "ElasticConnectionError",
    "ElasticHTTPError",
    "ElasticResponseError",
    "ElasticTimeoutError",
    "ElasticToolHandlers",
    "MAX_ELASTIC_TIMEOUT_SECONDS",
    "MIN_ELASTIC_TIMEOUT_SECONDS",
]