"""
Camada de orquestraÃ§Ã£o do Agentic SOC N1 Lab.
"""

from .base_agent import (
    AgentWorkResult,
    BaseAgent,
)
from .contracts import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentRuntimeContext,
)
from .registry import (
    OFFICIAL_AGENTS,
    OFFICIAL_AGENT_IDS,
    AgentDefinition,
    AgentRegistry,
    agent_registry,
)
from .runtime import (
    AgentRuntime,
    agent_runtime,
)
from .orchestrator import (
    SOCOrchestrator,
    soc_orchestrator,
)

__all__ = [
    "AgentDefinition",
    "AgentExecutionRequest",
    "AgentExecutionResult",
    "AgentRegistry",
    "AgentRuntime",
    "AgentRuntimeContext",
    "AgentWorkResult",
    "BaseAgent",
    "OFFICIAL_AGENTS",
    "OFFICIAL_AGENT_IDS",
    "SOCOrchestrator",
    "agent_registry",
    "agent_runtime",
    "soc_orchestrator",
]
