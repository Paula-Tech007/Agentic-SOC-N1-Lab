"""
Camada de permissões do Agentic SOC N1 Lab.

Este pacote centraliza as políticas de autorização
para ferramentas utilizadas pelos agentes SOC.

Princípios:

- deny-by-default;
- least privilege;
- somente operações defensivas;
- ferramentas comprovam, LLM interpreta;
- nenhuma ação crítica real é autorizada;
- integrações operacionais iniciais são read-only.
"""

from core.permissions.tool_policy import (
    FORBIDDEN_TOOL_IDS,
    OFFICIAL_AGENT_IDS,
    TOOL_CATALOG,
    ToolAccessMode,
    ToolDefinition,
    ToolRiskLevel,
    allowed_tools_for_agent,
    get_tool_definition,
    is_tool_allowed,
    validate_tool_access,
    validate_tool_catalog,
)


__all__ = [
    "FORBIDDEN_TOOL_IDS",
    "OFFICIAL_AGENT_IDS",
    "TOOL_CATALOG",
    "ToolAccessMode",
    "ToolDefinition",
    "ToolRiskLevel",
    "allowed_tools_for_agent",
    "get_tool_definition",
    "is_tool_allowed",
    "validate_tool_access",
    "validate_tool_catalog",
]