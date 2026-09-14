"""
Camada oficial de ferramentas
do Agentic SOC N1 Lab.

Fase 4 — Ferramentas e Integrações de Segurança.

Este pacote fornece:

- contratos ToolRequest e ToolResult;
- autorização de chamadas;
- registro de implementações;
- runtime controlado de ferramentas.

Princípios:

- deny-by-default;
- least privilege;
- ferramentas comprovam, LLM interpreta;
- nenhuma ação crítica real é executada;
- integrações iniciais operam em read-only;
- falhas são tratadas de forma fail-closed.
"""

from tools.authorization import (
    ToolAuthorizationDecision,
    authorize_tool_request,
    require_tool_authorization,
)
from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from tools.registry import (
    ToolHandler,
    ToolRegistry,
)
from tools.runtime import ToolRuntime


__all__ = [
    "ToolAuthorizationDecision",
    "ToolExecutionStatus",
    "ToolHandler",
    "ToolRegistry",
    "ToolRequest",
    "ToolResult",
    "ToolRuntime",
    "authorize_tool_request",
    "require_tool_authorization",
]