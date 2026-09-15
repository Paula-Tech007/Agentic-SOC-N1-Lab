"""
Camada MCP do Agentic SOC N1 Lab.

Fase 6 — Model Context Protocol.

Este pacote implementa a integração MCP
segura e governada do projeto.

Princípios:

- local-only;
- STDIO;
- read-only;
- deny-by-default;
- fail-closed;
- nenhuma ação crítica autônoma;
- ToolRuntime permanece soberano;
- permissões continuam definidas
  pelo catálogo oficial.
"""

from .config import (
    DEFAULT_MCP_SERVER_NAME,
    DEFAULT_MCP_SERVER_VERSION,
    DEFAULT_MCP_TIMEOUT_SECONDS,
    DEFAULT_MCP_TRANSPORT,
    MAX_MCP_TIMEOUT_SECONDS,
    MCPConfig,
    MIN_MCP_TIMEOUT_SECONDS,
    SUPPORTED_MCP_TRANSPORTS,
)

from .contracts import (
    DEFAULT_MCP_CALL_TIMEOUT_SECONDS,
    MAX_MCP_CALL_TIMEOUT_SECONDS,
    MCPCallStatus,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolDescriptor,
    MIN_MCP_CALL_TIMEOUT_SECONDS,
)

from .registry import (
    MCPRegistryError,
    MCPToolNotAllowedError,
    MCPToolNotFoundError,
    MCPToolRegistry,
    create_mcp_tool_registry,
)


__all__ = [
    "DEFAULT_MCP_CALL_TIMEOUT_SECONDS",
    "DEFAULT_MCP_SERVER_NAME",
    "DEFAULT_MCP_SERVER_VERSION",
    "DEFAULT_MCP_TIMEOUT_SECONDS",
    "DEFAULT_MCP_TRANSPORT",
    "MAX_MCP_CALL_TIMEOUT_SECONDS",
    "MAX_MCP_TIMEOUT_SECONDS",
    "MCPCallStatus",
    "MCPConfig",
    "MCPRegistryError",
    "MCPToolCallRequest",
    "MCPToolCallResult",
    "MCPToolDescriptor",
    "MCPToolNotAllowedError",
    "MCPToolNotFoundError",
    "MCPToolRegistry",
    "MIN_MCP_CALL_TIMEOUT_SECONDS",
    "MIN_MCP_TIMEOUT_SECONDS",
    "SUPPORTED_MCP_TRANSPORTS",
    "create_mcp_tool_registry",
]