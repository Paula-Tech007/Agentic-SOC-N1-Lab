"""
Registry MCP controlado
do Agentic SOC N1 Lab.

Fase 6.0 — Fundação MCP.

Este módulo NÃO cria um catálogo paralelo
de ferramentas.

A fonte oficial continua sendo:

    core.permissions.tool_policy.TOOL_CATALOG

O MCP apenas cria uma visão segura das tools
que podem ser expostas.

Regras:

- somente tools oficiais;
- somente READ_ONLY;
- nenhuma tool proibida;
- nenhuma ação crítica;
- deny-by-default;
- allowed_agents preservado;
- descrição preservada;
- política central continua soberana.

Fluxo:

TOOL_CATALOG
    ↓
MCPToolRegistry
    ↓
validação
    ↓
MCPToolDescriptor
    ↓
servidor MCP
"""

from __future__ import annotations

from types import (
    MappingProxyType,
)
from typing import (
    Any,
    Mapping,
)

from core.permissions.tool_policy import (
    FORBIDDEN_TOOL_IDS,
    TOOL_CATALOG,
    ToolAccessMode,
    ToolDefinition,
)

from soc_mcp.contracts import (
    MCPToolDescriptor,
)


DEFAULT_INPUT_SCHEMA: Mapping[
    str,
    Any,
] = MappingProxyType(
    {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }
)


class MCPRegistryError(
    RuntimeError
):
    """
    Erro base do registry MCP.
    """


class MCPToolNotFoundError(
    MCPRegistryError
):
    """
    Tool MCP não encontrada.
    """


class MCPToolNotAllowedError(
    MCPRegistryError
):
    """
    Tool existe, mas não pode
    ser exposta pelo MCP.
    """


def _normalize_tool_id(
    value: object,
) -> str:
    """
    Valida tool_id.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            "tool_id precisa "
            "ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            "tool_id não pode "
            "ser vazio."
        )

    return cleaned


def _normalize_agent_id(
    value: object,
) -> str:
    """
    Valida agent_id.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            "agent_id precisa "
            "ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            "agent_id não pode "
            "ser vazio."
        )

    return cleaned


def _tool_is_read_only(
    definition: ToolDefinition,
) -> bool:
    """
    Confirma READ_ONLY utilizando
    o enum oficial.
    """

    return (
        definition.access_mode
        is ToolAccessMode.READ_ONLY
    )


def _tool_is_forbidden(
    tool_id: str,
) -> bool:
    """
    Confirma se a tool pertence
    ao catálogo explícito de bloqueios.
    """

    return (
        tool_id
        in FORBIDDEN_TOOL_IDS
    )


def _tool_can_be_exposed(
    definition: ToolDefinition,
) -> bool:
    """
    Política mínima para exposição MCP.

    Nesta fase:

    - precisa ser READ_ONLY;
    - não pode estar na lista proibida.
    """

    if not _tool_is_read_only(
        definition
    ):
        return False

    if _tool_is_forbidden(
        definition.tool_id
    ):
        return False

    return True


def _build_title(
    definition: ToolDefinition,
) -> str:
    """
    Gera título humano sem alterar
    o identificador oficial.
    """

    integration = (
        str(
            definition.integration
        )
        .strip()
        .upper()
    )

    operation = (
        str(
            definition.operation
        )
        .strip()
        .replace(
            "_",
            " ",
        )
        .title()
    )

    return (
        f"{integration} — {operation}"
    )


def _build_descriptor(
    definition: ToolDefinition,
    *,
    input_schema: (
        Mapping[str, Any] | None
    ) = None,
) -> MCPToolDescriptor:
    """
    Converte ToolDefinition oficial
    em MCPToolDescriptor.

    A conversão não modifica permissões.
    """

    if not _tool_can_be_exposed(
        definition
    ):
        raise MCPToolNotAllowedError(
            "A ferramenta não atende "
            "à política de exposição MCP: "
            f"{definition.tool_id}"
        )

    schema = (
        DEFAULT_INPUT_SCHEMA
        if input_schema is None
        else input_schema
    )

    return MCPToolDescriptor(
        tool_id=(
            definition.tool_id
        ),
        title=_build_title(
            definition
        ),
        description=(
            definition.description
        ),
        allowed_agents=tuple(
            definition.allowed_agents
        ),
        input_schema=schema,
        read_only=True,
        local_only=True,
        critical_action=False,
    )


class MCPToolRegistry:
    """
    Registry MCP baseado exclusivamente
    no TOOL_CATALOG oficial.

    Ele não registra handlers.

    A execução real continuará sendo
    responsabilidade do ToolRuntime.
    """

    def __init__(
        self,
        *,
        input_schemas: (
            Mapping[
                str,
                Mapping[str, Any],
            ]
            | None
        ) = None,
    ) -> None:
        """
        Inicializa visão segura
        do catálogo oficial.
        """

        schemas = (
            {}
            if input_schemas is None
            else dict(
                input_schemas
            )
        )

        descriptors: dict[
            str,
            MCPToolDescriptor,
        ] = {}

        for (
            tool_id,
            definition,
        ) in TOOL_CATALOG.items():

            if not _tool_can_be_exposed(
                definition
            ):
                continue

            descriptor = (
                _build_descriptor(
                    definition,
                    input_schema=(
                        schemas.get(
                            tool_id
                        )
                    ),
                )
            )

            descriptors[
                tool_id
            ] = descriptor

        self._descriptors = (
            MappingProxyType(
                descriptors
            )
        )

    def __len__(
        self,
    ) -> int:
        """
        Quantidade de tools MCP
        disponíveis.
        """

        return len(
            self._descriptors
        )

    def __contains__(
        self,
        tool_id: object,
    ) -> bool:
        """
        Permite:

            "misp.search_ioc" in registry
        """

        if not isinstance(
            tool_id,
            str,
        ):
            return False

        return (
            tool_id
            in self._descriptors
        )

    @property
    def tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        IDs oficiais expostos.
        """

        return tuple(
            sorted(
                self._descriptors.keys()
            )
        )

    def get(
        self,
        tool_id: str,
    ) -> MCPToolDescriptor | None:
        """
        Consulta descriptor sem lançar erro.
        """

        normalized = (
            _normalize_tool_id(
                tool_id
            )
        )

        return (
            self._descriptors.get(
                normalized
            )
        )

    def require(
        self,
        tool_id: str,
    ) -> MCPToolDescriptor:
        """
        Consulta obrigatória.

        Falha fechado caso a tool
        não esteja autorizada.
        """

        normalized = (
            _normalize_tool_id(
                tool_id
            )
        )

        descriptor = (
            self._descriptors.get(
                normalized
            )
        )

        if descriptor is None:
            raise MCPToolNotFoundError(
                "Tool não disponível "
                "no registry MCP: "
                f"{normalized}"
            )

        return descriptor

    def allowed_for_agent(
        self,
        agent_id: str,
    ) -> tuple[MCPToolDescriptor, ...]:
        """
        Retorna somente as tools que
        o agente já possui autorização
        no catálogo oficial.
        """

        normalized = (
            _normalize_agent_id(
                agent_id
            )
        )

        descriptors = [
            descriptor
            for descriptor
            in self._descriptors.values()
            if normalized
            in descriptor.allowed_agents
        ]

        return tuple(
            sorted(
                descriptors,
                key=lambda item: (
                    item.tool_id
                ),
            )
        )

    def can_agent_use(
        self,
        *,
        agent_id: str,
        tool_id: str,
    ) -> bool:
        """
        Verificação simples de exposição.

        Isso NÃO substitui a autorização
        do ToolRuntime.
        """

        normalized_agent = (
            _normalize_agent_id(
                agent_id
            )
        )

        descriptor = self.get(
            tool_id
        )

        if descriptor is None:
            return False

        return (
            normalized_agent
            in descriptor.allowed_agents
        )

    def snapshot(
        self,
    ) -> Mapping[
        str,
        MCPToolDescriptor,
    ]:
        """
        Retorna snapshot imutável.
        """

        return self._descriptors

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Resumo seguro do registry.
        """

        return {
            "integration": "MCP",
            "source_catalog": (
                "TOOL_CATALOG"
            ),
            "tool_count": len(
                self
            ),
            "tool_ids": (
                self.tool_ids
            ),
            "read_only_only": True,
            "forbidden_tools_exposed": False,
            "critical_actions_exposed": False,
            "deny_by_default": True,
        }


def create_mcp_tool_registry(
    *,
    input_schemas: (
        Mapping[
            str,
            Mapping[str, Any],
        ]
        | None
    ) = None,
) -> MCPToolRegistry:
    """
    Factory pública do registry MCP.
    """

    return MCPToolRegistry(
        input_schemas=(
            input_schemas
        )
    )