"""
Composition root completo das Tools
de enriquecimento da Fase 7.3.

Esta camada estende a composição já
validada em enrichment_tool_bootstrap.py.

Ela preserva:

- MISP;
- Identity / IAM;
- Asset / CMDB;

e acrescenta:

- Email / Phishing.

Nenhuma Tool é executada durante
a construção do Runtime.

Todas as integrações continuam:

- read-only;
- deny-by-default;
- least privilege;
- fail-closed;
- subordinadas ao ToolRuntime;
- sem abertura de URLs;
- sem download de anexos;
- sem execução de anexos.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.enrichment_tool_bootstrap import (
    build_enrichment_tool_registry,
)

from tools import (
    ToolRegistry,
    ToolRuntime,
)

from tools.email import (
    EmailClient,
    EmailConfig,
    EmailToolHandlers,
)


def build_full_enrichment_tool_registry(
    *,
    env: Mapping[str, str] | None = None,
    misp_transport: Any | None = None,
    identity_transport: Any | None = None,
    asset_transport: Any | None = None,
    email_transport: Any | None = None,
    email_config: EmailConfig | None = None,
) -> ToolRegistry:
    """
    Cria Registry completo para
    AG-04, AG-05, AG-06 e AG-07.

    MISP/IAM/Asset são reutilizados
    da composição já validada.

    EmailConfig pode ser injetada
    pelos testes.

    Quando não for fornecida,
    utiliza EmailConfig.from_env().
    """

    if (
        email_config is not None
        and not isinstance(
            email_config,
            EmailConfig,
        )
    ):
        raise TypeError(
            "email_config precisa ser "
            "EmailConfig ou None."
        )

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

    resolved_email_config = (
        email_config
        if email_config is not None
        else EmailConfig.from_env()
    )

    email_client = EmailClient(
        resolved_email_config,
        transport=email_transport,
    )

    email_handlers = (
        EmailToolHandlers(
            email_client
        )
    )

    email_handlers.register(
        registry
    )

    return registry


def build_full_enrichment_tool_runtime(
    *,
    env: Mapping[str, str] | None = None,
    misp_transport: Any | None = None,
    identity_transport: Any | None = None,
    asset_transport: Any | None = None,
    email_transport: Any | None = None,
    email_config: EmailConfig | None = None,
) -> ToolRuntime:
    """
    Cria ToolRuntime completo
    da etapa de enriquecimento.

    Ferramentas disponíveis:

    AG-04
        misp.*

    AG-05
        iam.*

    AG-06
        asset.*

    AG-07
        email.get_message_metadata
        email.get_headers
        email.get_authentication_results
        email.get_attachment_metadata

    Nenhum estado global é alterado.
    """

    registry = (
        build_full_enrichment_tool_registry(
            env=env,
            misp_transport=misp_transport,
            identity_transport=(
                identity_transport
            ),
            asset_transport=(
                asset_transport
            ),
            email_transport=(
                email_transport
            ),
            email_config=(
                email_config
            ),
        )
    )

    return ToolRuntime(
        registry
    )


__all__ = [
    "build_full_enrichment_tool_registry",
    "build_full_enrichment_tool_runtime",
]