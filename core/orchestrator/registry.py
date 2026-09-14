"""
Registry oficial dos agentes do Agentic SOC N1 Lab.

O Registry funciona como catálogo central dos agentes
disponíveis para o Orchestrator.

Responsabilidades:

- conhecer os 12 agentes oficiais;
- registrar instâncias de agentes;
- impedir IDs duplicados;
- rejeitar agentes não oficiais;
- recuperar agentes por agent_id;
- listar agentes disponíveis;
- fornecer metadados do catálogo oficial.

O Registry não executa agentes.
A execução será responsabilidade do Runtime.
"""

from dataclasses import dataclass

from core.orchestrator.base_agent import BaseAgent


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """
    Metadados oficiais de um agente do SOC.
    """

    agent_id: str
    name: str
    responsibility: str


OFFICIAL_AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        agent_id="AG-01",
        name="SOC Supervisor Agent",
        responsibility=(
            "Coordenar o fluxo e decidir quais agentes "
            "especializados devem atuar no caso."
        ),
    ),
    AgentDefinition(
        agent_id="AG-02",
        name="Alert Intake Agent",
        responsibility=(
            "Receber, validar e normalizar alertas."
        ),
    ),
    AgentDefinition(
        agent_id="AG-03",
        name="Triage Analyst Agent",
        responsibility=(
            "Realizar triagem, classificação, severidade "
            "e identificação das próximas análises."
        ),
    ),
    AgentDefinition(
        agent_id="AG-04",
        name="Threat Intelligence Agent",
        responsibility=(
            "Enriquecer indicadores utilizando fontes "
            "de Threat Intelligence autorizadas."
        ),
    ),
    AgentDefinition(
        agent_id="AG-05",
        name="Identity Analyst Agent",
        responsibility=(
            "Analisar contas, autenticações, MFA, "
            "privilégios e contexto de identidade."
        ),
    ),
    AgentDefinition(
        agent_id="AG-06",
        name="Asset Context Agent",
        responsibility=(
            "Analisar ativos, criticidade, exposição "
            "e contexto operacional."
        ),
    ),
    AgentDefinition(
        agent_id="AG-07",
        name="Phishing Analyst Agent",
        responsibility=(
            "Realizar análise especializada de phishing."
        ),
    ),
    AgentDefinition(
        agent_id="AG-08",
        name="Knowledge / RAG Agent",
        responsibility=(
            "Recuperar playbooks, runbooks, políticas "
            "e conhecimento com rastreabilidade de fonte."
        ),
    ),
    AgentDefinition(
        agent_id="AG-09",
        name="Incident Analyst Agent",
        responsibility=(
            "Consolidar evidências, timeline, achados "
            "e investigação do incidente."
        ),
    ),
    AgentDefinition(
        agent_id="AG-10",
        name="Reflection / QA Agent",
        responsibility=(
            "Revisar qualidade, evidências, lacunas "
            "e inconsistências da investigação."
        ),
    ),
    AgentDefinition(
        agent_id="AG-11",
        name="Case Management Agent",
        responsibility=(
            "Manter documentação e registros do caso."
        ),
    ),
    AgentDefinition(
        agent_id="AG-12",
        name="Escalation Agent",
        responsibility=(
            "Aplicar regras de decisão, fechamento N1 "
            "e escalonamento N2 ou humano."
        ),
    ),
)


OFFICIAL_AGENT_IDS: frozenset[str] = frozenset(
    definition.agent_id
    for definition in OFFICIAL_AGENTS
)


OFFICIAL_AGENT_MAP: dict[str, AgentDefinition] = {
    definition.agent_id: definition
    for definition in OFFICIAL_AGENTS
}


class AgentRegistry:
    """
    Catálogo de instâncias disponíveis para execução.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(
        self,
        agent: BaseAgent,
    ) -> None:
        """
        Registra um agente oficial.

        O mesmo agent_id não pode ser registrado duas vezes.
        """

        if not isinstance(agent, BaseAgent):
            raise TypeError(
                "Somente instâncias de BaseAgent podem "
                "ser registradas."
            )

        if agent.agent_id not in OFFICIAL_AGENT_IDS:
            raise ValueError(
                f"Agente não oficial: {agent.agent_id}"
            )

        if agent.agent_id in self._agents:
            raise ValueError(
                f"Agente já registrado: {agent.agent_id}"
            )

        self._agents[agent.agent_id] = agent

    def unregister(
        self,
        agent_id: str,
    ) -> BaseAgent:
        """
        Remove um agente do Registry.

        Retorna a instância removida.
        """

        if agent_id not in self._agents:
            raise KeyError(
                f"Agente não registrado: {agent_id}"
            )

        return self._agents.pop(agent_id)

    def get(
        self,
        agent_id: str,
    ) -> BaseAgent:
        """
        Recupera uma instância registrada.
        """

        if agent_id not in OFFICIAL_AGENT_IDS:
            raise KeyError(
                f"agent_id não pertence ao catálogo oficial: "
                f"{agent_id}"
            )

        if agent_id not in self._agents:
            raise KeyError(
                f"Agente oficial ainda não registrado: {agent_id}"
            )

        return self._agents[agent_id]

    def contains(
        self,
        agent_id: str,
    ) -> bool:
        """
        Verifica se uma instância está registrada.
        """

        return agent_id in self._agents

    def registered_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Retorna os IDs registrados em ordem.
        """

        return tuple(
            sorted(self._agents)
        )

    def registered_count(
        self,
    ) -> int:
        """
        Retorna a quantidade de agentes registrados.
        """

        return len(self._agents)

    def official_count(
        self,
    ) -> int:
        """
        Retorna a quantidade de agentes oficiais.
        """

        return len(OFFICIAL_AGENTS)

    def missing_official_agents(
        self,
    ) -> tuple[str, ...]:
        """
        Lista os agentes oficiais ainda não registrados.
        """

        return tuple(
            sorted(
                OFFICIAL_AGENT_IDS
                - self._agents.keys()
            )
        )

    def definition(
        self,
        agent_id: str,
    ) -> AgentDefinition:
        """
        Recupera os metadados oficiais de um agente.
        """

        if agent_id not in OFFICIAL_AGENT_MAP:
            raise KeyError(
                f"Agente não oficial: {agent_id}"
            )

        return OFFICIAL_AGENT_MAP[agent_id]

    def clear(self) -> None:
        """
        Remove todas as instâncias registradas.

        Útil principalmente para testes.
        """

        self._agents.clear()


agent_registry = AgentRegistry()