"""
Composition root oficial
do Agentic SOC N1 Lab.

Responsabilidades:

- instanciar os 12 agentes oficiais;
- registrar os agentes em um Registry próprio;
- criar o AgentRuntime oficial;
- criar o SOCOrchestrator oficial;
- criar o Phase7E2ERunner oficial;
- permitir composição explícita do
  provider de enriquecimento.

Esta camada NÃO contém lógica de negócio.

Ela apenas conecta componentes já existentes.

Fluxo:

12 agentes
    ↓
AgentRegistry
    ↓
AgentRuntime
    ↓
SOCOrchestrator
    ↓
Phase7E2ERunner
    ↓
EnrichmentPayloadProvider opcional

A construção de Tools, RAG e providers
permanece explícita.

Isso evita efeitos colaterais, acesso
involuntário à rede e dependência de
credenciais durante import/bootstrap.
"""

from agents.alert_intake import (
    AlertIntakeAgent,
)
from agents.asset import (
    AssetContextAgent,
)
from agents.case_management import (
    CaseManagementAgent,
)
from agents.escalation import (
    EscalationAgent,
)
from agents.identity import (
    IdentityAnalystAgent,
)
from agents.incident import (
    IncidentAnalystAgent,
)
from agents.knowledge import (
    KnowledgeRAGAgent,
)
from agents.phishing import (
    PhishingAnalystAgent,
)
from agents.reflection import (
    ReflectionQAAgent,
)
from agents.supervisor import (
    SOCSupervisorAgent,
)
from agents.threat_intel import (
    ThreatIntelligenceAgent,
)
from agents.triage import (
    TriageAnalystAgent,
)

from core.orchestrator import (
    AgentRegistry,
    AgentRuntime,
    SOCOrchestrator,
)
from core.orchestrator.enrichment import (
    EnrichmentPayloadProviderProtocol,
)
from core.orchestrator.phase7_runner import (
    Phase7E2ERunner,
)


OFFICIAL_AGENT_CLASSES = (
    SOCSupervisorAgent,
    AlertIntakeAgent,
    TriageAnalystAgent,
    ThreatIntelligenceAgent,
    IdentityAnalystAgent,
    AssetContextAgent,
    PhishingAnalystAgent,
    KnowledgeRAGAgent,
    IncidentAnalystAgent,
    ReflectionQAAgent,
    CaseManagementAgent,
    EscalationAgent,
)


def build_official_agent_registry(
) -> AgentRegistry:
    """
    Cria um Registry novo contendo
    exatamente os 12 agentes oficiais.

    O Registry global não é alterado.

    Isso evita estado compartilhado
    inesperado entre testes, execução
    local e outros consumidores.
    """

    registry = AgentRegistry()

    for agent_class in OFFICIAL_AGENT_CLASSES:
        registry.register(
            agent_class()
        )

    return registry


def build_official_agent_runtime(
) -> AgentRuntime:
    """
    Cria o Runtime oficial utilizando
    um Registry completamente inicializado.
    """

    registry = (
        build_official_agent_registry()
    )

    return AgentRuntime(
        registry
    )


def build_official_soc_orchestrator(
) -> SOCOrchestrator:
    """
    Cria o SOCOrchestrator oficial
    com Runtime e Registry completos.
    """

    runtime = (
        build_official_agent_runtime()
    )

    return SOCOrchestrator(
        runtime
    )


def build_phase7_runner(
    *,
    max_cycles: int = 32,
    payload_provider: (
        EnrichmentPayloadProviderProtocol
        | None
    ) = None,
) -> Phase7E2ERunner:
    """
    Cria o Runner E2E oficial
    utilizando a composição completa
    dos agentes da aplicação.

    Um provider de enriquecimento pode
    ser injetado explicitamente.

    Nenhum acesso à rede, RAG ou Tool
    ocorre durante esta função por conta
    própria.

    Nenhum guardrail é ignorado.
    """

    if (
        isinstance(
            max_cycles,
            bool,
        )
        or not isinstance(
            max_cycles,
            int,
        )
        or max_cycles < 1
        or max_cycles > 100
    ):
        raise ValueError(
            "max_cycles precisa estar "
            "entre 1 e 100."
        )

    if (
        payload_provider is not None
        and not callable(
            getattr(
                payload_provider,
                "build_payload",
                None,
            )
        )
    ):
        raise TypeError(
            "payload_provider precisa "
            "implementar build_payload()."
        )

    orchestrator = (
        build_official_soc_orchestrator()
    )

    return Phase7E2ERunner(
        orchestrator,
        max_cycles=max_cycles,
        payload_provider=(
            payload_provider
        ),
    )


__all__ = [
    "OFFICIAL_AGENT_CLASSES",
    "build_official_agent_registry",
    "build_official_agent_runtime",
    "build_official_soc_orchestrator",
    "build_phase7_runner",
]