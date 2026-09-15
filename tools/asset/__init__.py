"""
Camada Asset / CMDB
do Agentic SOC N1 Lab.

Fase 4.4 — Asset / CMDB read-only.

Este pacote fornece:

- configuração segura da integração Asset / CMDB;
- cliente HTTP estritamente read-only;
- handlers oficiais para ToolRuntime.

Ferramentas implementadas:

- asset.get_asset;
- asset.get_ip_context;
- asset.get_criticality;
- asset.get_edr_status.

Nenhuma operação de alteração de ativo,
inventário, criticidade ou EDR é disponibilizada.
"""

from tools.asset.asset_client import (
    AssetClient,
    AssetClientError,
    AssetConnectionError,
    AssetHTTPError,
    AssetResponseError,
    AssetTimeoutError,
)
from tools.asset.asset_config import (
    DEFAULT_ASSET_PROVIDER,
    DEFAULT_ASSET_TIMEOUT_SECONDS,
    MAX_ASSET_TIMEOUT_SECONDS,
    MIN_ASSET_TIMEOUT_SECONDS,
    AssetConfig,
)
from tools.asset.asset_handlers import (
    AssetToolHandlers,
)


__all__ = [
    "AssetClient",
    "AssetClientError",
    "AssetConfig",
    "AssetConnectionError",
    "AssetHTTPError",
    "AssetResponseError",
    "AssetTimeoutError",
    "AssetToolHandlers",
    "DEFAULT_ASSET_PROVIDER",
    "DEFAULT_ASSET_TIMEOUT_SECONDS",
    "MAX_ASSET_TIMEOUT_SECONDS",
    "MIN_ASSET_TIMEOUT_SECONDS",
]