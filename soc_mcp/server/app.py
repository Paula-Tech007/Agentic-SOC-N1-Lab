"""
Servidor MCP oficial
do Agentic SOC N1 Lab.

Fase 6.0 — Fundação MCP.

Este módulo utiliza o SDK oficial MCP 2.x:

    from mcp.server import MCPServer

Arquitetura:

MCP Client
    ↓
MCPServer
    ↓
tool vinculada ao agente atual
    ↓
MCPToolRuntimeBridge
    ↓
ToolRuntime
    ↓
ToolAuthorization
    ↓
ToolRegistry
    ↓
Handler defensivo

Regras de segurança:

- servidor local;
- STDIO;
- agente vinculado no servidor;
- caso vinculado no servidor;
- correlation_id vinculado no servidor;
- cliente não escolhe agent_id;
- cliente não escolhe case_id;
- cliente não escolhe correlation_id;
- somente tools autorizadas ao agente
  são registradas;
- nenhuma ação crítica;
- ToolRuntime permanece soberano;
- fail-closed.
"""

from __future__ import annotations

from typing import (
    Any,
)

from uuid import (
    uuid4,
)

from mcp.server import (
    MCPServer,
)

from soc_mcp.config import (
    MCPConfig,
)

from soc_mcp.contracts import (
    MCPToolCallRequest,
)

from soc_mcp.registry import (
    MCPToolRegistry,
)

from soc_mcp.server.bridge import (
    MCPRuntimeProtocol,
    MCPToolRuntimeBridge,
)


def _required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Valida string obrigatória.
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


def _plain_value(
    value: Any,
) -> Any:
    """
    Converte estruturas internas
    para objetos serializáveis.
    """

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _plain_value(
                item
            )
            for key, item
            in value.items()
        }

    if hasattr(
        value,
        "items",
    ):
        return {
            str(key): _plain_value(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        tuple,
    ):
        return [
            _plain_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        frozenset,
    ):
        return [
            _plain_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        list,
    ):
        return [
            _plain_value(
                item
            )
            for item in value
        ]

    return value


def _result_to_payload(
    result: object,
) -> dict[str, Any]:
    """
    Serializa MCPToolCallResult.

    A função exige os atributos esperados
    e falha fechado em resultado inválido.
    """

    required_attributes = (
        "request_id",
        "execution_id",
        "agent_id",
        "case_id",
        "correlation_id",
        "tool_id",
        "status",
        "success",
        "output",
        "evidence",
        "error_code",
        "error_message",
        "attempts",
        "duration_ms",
    )

    for attribute in required_attributes:
        if not hasattr(
            result,
            attribute,
        ):
            raise RuntimeError(
                "Resultado MCP inválido: "
                f"campo ausente {attribute}."
            )

    status = getattr(
        result,
        "status",
    )

    status_value = getattr(
        status,
        "value",
        str(status),
    )

    return {
        "request_id": getattr(
            result,
            "request_id",
        ),
        "execution_id": getattr(
            result,
            "execution_id",
        ),
        "agent_id": getattr(
            result,
            "agent_id",
        ),
        "case_id": getattr(
            result,
            "case_id",
        ),
        "correlation_id": getattr(
            result,
            "correlation_id",
        ),
        "tool_id": getattr(
            result,
            "tool_id",
        ),
        "status": status_value,
        "success": getattr(
            result,
            "success",
        ),
        "output": _plain_value(
            getattr(
                result,
                "output",
            )
        ),
        "evidence": _plain_value(
            getattr(
                result,
                "evidence",
            )
        ),
        "error_code": getattr(
            result,
            "error_code",
        ),
        "error_message": getattr(
            result,
            "error_message",
        ),
        "attempts": getattr(
            result,
            "attempts",
        ),
        "duration_ms": getattr(
            result,
            "duration_ms",
        ),
    }


def _build_tool_callable(
    *,
    tool_id: str,
    agent_id: str,
    case_id: str,
    correlation_id: str,
    bridge: MCPToolRuntimeBridge,
    timeout_seconds: int,
):
    """
    Cria a função MCP ligada
    a uma tool oficial específica.

    O cliente informa somente
    os argumentos funcionais da tool.

    Contexto de segurança fica
    vinculado pelo servidor.
    """

    def execute_tool(
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executa uma ferramenta defensiva
        pelo ToolRuntime oficial.
        """

        request = MCPToolCallRequest(
            request_id=(
                "MCP-REQ-"
                + uuid4().hex.upper()
            ),
            execution_id=(
                "MCP-EXEC-"
                + uuid4().hex.upper()
            ),
            agent_id=agent_id,
            case_id=case_id,
            correlation_id=(
                correlation_id
            ),
            tool_id=tool_id,
            arguments=arguments,
            timeout_seconds=(
                timeout_seconds
            ),
        )

        result = bridge.execute(
            request
        )

        return _result_to_payload(
            result
        )

    return execute_tool


def create_mcp_server(
    *,
    runtime: MCPRuntimeProtocol,
    agent_id: str,
    case_id: str,
    correlation_id: str,
    config: MCPConfig | None = None,
    registry: MCPToolRegistry | None = None,
) -> MCPServer:
    """
    Cria servidor MCP seguro
    para um agente e um caso.

    O servidor registra somente
    ferramentas que o agente já possui
    permissão para utilizar.
    """

    normalized_agent_id = (
        _required_string(
            agent_id,
            field_name="agent_id",
        )
    )

    normalized_case_id = (
        _required_string(
            case_id,
            field_name="case_id",
        )
    )

    normalized_correlation_id = (
        _required_string(
            correlation_id,
            field_name=(
                "correlation_id"
            ),
        )
    )

    active_config = (
        MCPConfig()
        if config is None
        else config
    )

    if not isinstance(
        active_config,
        MCPConfig,
    ):
        raise TypeError(
            "config precisa ser MCPConfig."
        )

    active_registry = (
        MCPToolRegistry()
        if registry is None
        else registry
    )

    if not isinstance(
        active_registry,
        MCPToolRegistry,
    ):
        raise TypeError(
            "registry precisa ser "
            "MCPToolRegistry."
        )

    bridge = MCPToolRuntimeBridge(
        runtime=runtime,
        registry=active_registry,
    )

    allowed_tools = (
        active_registry.allowed_for_agent(
            normalized_agent_id
        )
    )

    if not allowed_tools:
        raise ValueError(
            "O agente informado não possui "
            "tools MCP autorizadas."
        )

    server = MCPServer(
        name=(
            active_config.server_name
        ),
        title=(
            "Agentic SOC N1 Lab"
        ),
        description=(
            "Servidor MCP local e defensivo "
            "do Agentic SOC N1 Lab."
        ),
        instructions=(
            "Utilize somente ferramentas "
            "defensivas autorizadas. "
            "Ações críticas autônomas "
            "não são permitidas."
        ),
        version=(
            active_config.server_version
        ),
    )

    for descriptor in allowed_tools:
        callable_tool = (
            _build_tool_callable(
                tool_id=(
                    descriptor.tool_id
                ),
                agent_id=(
                    normalized_agent_id
                ),
                case_id=(
                    normalized_case_id
                ),
                correlation_id=(
                    normalized_correlation_id
                ),
                bridge=bridge,
                timeout_seconds=(
                    active_config.timeout_seconds
                ),
            )
        )

        server.add_tool(
            callable_tool,
            name=(
                descriptor.tool_id
            ),
            title=(
                descriptor.title
            ),
            description=(
                descriptor.description
            ),
            structured_output=True,
        )

    return server