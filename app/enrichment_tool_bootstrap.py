"""
Composition root das ferramentas de enriquecimento
da Fase 7.3 do Agentic SOC N1 Lab.

Responsabilidades:

- criar configurações read-only para MISP;
- criar configurações read-only para IAM;
- criar configurações read-only para Asset / CMDB;
- instanciar os clientes oficiais;
- registrar os handlers no ToolRegistry;
- criar um ToolRuntime isolado e completo
  para a etapa de enriquecimento.

Esta camada NÃO executa ferramentas.

Ela apenas conecta componentes já existentes.

Fluxo:

Configuração
    ↓
Clientes
    ↓
Handlers
    ↓
ToolRegistry
    ↓
ToolRuntime

Princípios preservados:

- deny-by-default;
- least privilege;
- fail-closed;
- somente integrações read-only;
- nenhuma credencial é registrada em logs;
- nenhuma ação crítica é executada;
- nenhum estado global de ToolRuntime é criado.
"""

from __future__ import annotations

from collections.abc import Mapping
from os import environ
from typing import Any

from tools import (
    ToolRegistry,
    ToolRuntime,
)

from tools.asset.asset_client import (
    AssetClient,
)
from tools.asset.asset_config import (
    AssetConfig,
)
from tools.asset.asset_handlers import (
    AssetToolHandlers,
)

from tools.identity.identity_client import (
    IdentityClient,
)
from tools.identity.identity_config import (
    IdentityConfig,
)
from tools.identity.identity_handlers import (
    IdentityToolHandlers,
)

from tools.threat_intel.misp_client import (
    MISPClient,
)
from tools.threat_intel.misp_config import (
    MISPConfig,
)
from tools.threat_intel.misp_handlers import (
    MISPToolHandlers,
)


def _required_value(
    source: Mapping[str, str],
    name: str,
) -> str:
    """
    Recupera uma configuração obrigatória.

    O valor nunca é incluído na mensagem
    de erro para evitar exposição acidental
    de credenciais.
    """

    value = source.get(
        name
    )

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            "Configuração obrigatória ausente: "
            f"{name}."
        )

    normalized = value.strip()

    if not normalized:
        raise RuntimeError(
            "Configuração obrigatória vazia: "
            f"{name}."
        )

    return normalized


def _optional_value(
    source: Mapping[str, str],
    name: str,
    default: str,
) -> str:
    """
    Recupera uma configuração textual opcional.
    """

    value = source.get(
        name
    )

    if value is None:
        return default

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            "Configuração precisa ser string: "
            f"{name}."
        )

    normalized = value.strip()

    if not normalized:
        return default

    return normalized


def _boolean_value(
    source: Mapping[str, str],
    name: str,
    default: bool,
) -> bool:
    """
    Converte configuração textual
    para booleano de forma explícita.
    """

    value = source.get(
        name
    )

    if value is None:
        return default

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            "Configuração booleana inválida: "
            f"{name}."
        )

    normalized = (
        value
        .strip()
        .lower()
    )

    if normalized in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "n",
        "off",
    }:
        return False

    raise RuntimeError(
        "Configuração booleana inválida: "
        f"{name}."
    )


def _positive_integer_value(
    source: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    """
    Recupera um inteiro positivo
    utilizado em timeout.
    """

    value = source.get(
        name
    )

    if value is None:
        return default

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            "Configuração numérica inválida: "
            f"{name}."
        )

    normalized = value.strip()

    try:
        parsed = int(
            normalized
        )

    except ValueError as exc:
        raise RuntimeError(
            "Configuração numérica inválida: "
            f"{name}."
        ) from exc

    if parsed < 1:
        raise RuntimeError(
            "Configuração precisa ser "
            "maior que zero: "
            f"{name}."
        )

    return parsed


def build_misp_config(
    *,
    env: Mapping[str, str] | None = None,
) -> MISPConfig:
    """
    Cria a configuração oficial
    da integração MISP.
    """

    source = (
        environ
        if env is None
        else env
    )

    return MISPConfig(
        base_url=_required_value(
            source,
            "MISP_URL",
        ),
        api_key=_required_value(
            source,
            "MISP_API_KEY",
        ),
        verify_ssl=_boolean_value(
            source,
            "MISP_VERIFY_SSL",
            True,
        ),
        timeout_seconds=(
            _positive_integer_value(
                source,
                "MISP_TIMEOUT_SECONDS",
                15,
            )
        ),
    )


def build_identity_config(
    *,
    env: Mapping[str, str] | None = None,
) -> IdentityConfig:
    """
    Cria a configuração oficial
    da integração Identity / IAM.
    """

    source = (
        environ
        if env is None
        else env
    )

    return IdentityConfig(
        base_url=_required_value(
            source,
            "IAM_URL",
        ),
        api_token=_required_value(
            source,
            "IAM_API_TOKEN",
        ),
        provider=_optional_value(
            source,
            "IAM_PROVIDER",
            "GENERIC",
        ),
        verify_ssl=_boolean_value(
            source,
            "IAM_VERIFY_SSL",
            True,
        ),
        timeout_seconds=(
            _positive_integer_value(
                source,
                "IAM_TIMEOUT_SECONDS",
                15,
            )
        ),
    )


def build_asset_config(
    *,
    env: Mapping[str, str] | None = None,
) -> AssetConfig:
    """
    Cria a configuração oficial
    da integração Asset / CMDB.
    """

    source = (
        environ
        if env is None
        else env
    )

    return AssetConfig(
        base_url=_required_value(
            source,
            "ASSET_URL",
        ),
        api_token=_required_value(
            source,
            "ASSET_API_TOKEN",
        ),
        provider=_optional_value(
            source,
            "ASSET_PROVIDER",
            "GENERIC",
        ),
        verify_ssl=_boolean_value(
            source,
            "ASSET_VERIFY_SSL",
            True,
        ),
        timeout_seconds=(
            _positive_integer_value(
                source,
                "ASSET_TIMEOUT_SECONDS",
                15,
            )
        ),
    )


def build_enrichment_tool_registry(
    *,
    env: Mapping[str, str] | None = None,
    misp_transport: Any | None = None,
    identity_transport: Any | None = None,
    asset_transport: Any | None = None,
) -> ToolRegistry:
    """
    Cria um ToolRegistry novo contendo
    as ferramentas necessárias para:

    - AG-04 Threat Intelligence;
    - AG-05 Identity Analyst;
    - AG-06 Asset Context.

    Os transports opcionais existem
    exclusivamente para permitir
    testes controlados sem rede real.
    """

    registry = ToolRegistry()

    misp_client = MISPClient(
        build_misp_config(
            env=env
        ),
        transport=misp_transport,
    )

    identity_client = IdentityClient(
        build_identity_config(
            env=env
        ),
        transport=identity_transport,
    )

    asset_client = AssetClient(
        build_asset_config(
            env=env
        ),
        transport=asset_transport,
    )

    misp_handlers = MISPToolHandlers(
        misp_client
    )

    identity_handlers = (
        IdentityToolHandlers(
            identity_client
        )
    )

    asset_handlers = AssetToolHandlers(
        asset_client
    )

    misp_handlers.register(
        registry
    )

    identity_handlers.register(
        registry
    )

    asset_handlers.register(
        registry
    )

    return registry


def build_enrichment_tool_runtime(
    *,
    env: Mapping[str, str] | None = None,
    misp_transport: Any | None = None,
    identity_transport: Any | None = None,
    asset_transport: Any | None = None,
) -> ToolRuntime:
    """
    Cria o ToolRuntime isolado
    utilizado pela etapa de enriquecimento.

    Nenhum estado global é alterado.
    """

    registry = (
        build_enrichment_tool_registry(
            env=env,
            misp_transport=misp_transport,
            identity_transport=(
                identity_transport
            ),
            asset_transport=(
                asset_transport
            ),
        )
    )

    return ToolRuntime(
        registry
    )


__all__ = [
    "build_asset_config",
    "build_enrichment_tool_registry",
    "build_enrichment_tool_runtime",
    "build_identity_config",
    "build_misp_config",
]