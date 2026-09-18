"""
Orquestração de enriquecimento
do Agentic SOC N1 Lab.

Fase 7.3 — Enriquecimento automático controlado.

Esta camada coordena exclusivamente:

- AG-04 Threat Intelligence;
- AG-05 Identity Analyst;
- AG-06 Asset Context;
- AG-07 Phishing Analyst;
- AG-08 Knowledge/RAG.

A seleção dos agentes continua sendo
derivada do workflow já produzido
pelo Triage/SOCOrchestrator.

Este módulo não cria uma segunda
regra de decisão paralela.

Fluxo:

    CaseState após AG-03
        ↓
    pending_agents
        ↓
    Supervisor AG-01
        ↓
    próximo agente de enriquecimento
        ↓
    EnrichmentPayloadProvider
        ↓
    input_payload comprovado
        ↓
    execução controlada
        ↓
    CaseState atualizado
        ↓
    repetir somente enquanto houver
    agentes de enriquecimento pendentes

A camada permanece:

- defensiva;
- fail-closed;
- sem ações críticas;
- sem bypass do Runtime;
- sem bypass de permissões;
- sem acesso direto a ferramentas;
- sem dependência da camada app;
- sem execução de AG-09..AG-12 nesta etapa.

Princípio:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from core.orchestrator.contracts import (
    AgentExecutionResult,
)
from core.orchestrator.e2e import (
    E2EExecutionController,
)
from core.orchestrator.orchestrator import (
    SOCOrchestrator,
)
from core.orchestrator.supervised import (
    SupervisedE2EController,
    SupervisedStepResult,
)
from core.state import (
    CaseState,
)


ENRICHMENT_AGENT_IDS: tuple[str, ...] = (
    "AG-04",
    "AG-05",
    "AG-06",
    "AG-07",
    "AG-08",
)


class EnrichmentPayloadProviderProtocol(
    Protocol
):
    """
    Contrato mínimo esperado pela camada
    de enriquecimento.

    O core não conhece a implementação
    concreta do provider.

    Isso preserva a direção arquitetural:

        app
         ↓
        core

    e nunca:

        core
         ↓
        app
    """

    def build_payload(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
    ) -> Mapping[str, Any]:
        """
        Produz input_payload para exatamente
        um agente de enriquecimento.
        """

        ...


@dataclass(
    frozen=True,
    slots=True,
)
class EnrichmentRunResult:
    """
    Resultado imutável da execução
    controlada dos enriquecimentos.
    """

    case_id: str
    correlation_id: str

    requested_agents: tuple[str, ...]
    executed_agents: tuple[str, ...]

    supervisor_results: tuple[
        AgentExecutionResult,
        ...,
    ]

    specialist_results: tuple[
        AgentExecutionResult,
        ...,
    ]

    stopped_before_non_enrichment: bool

    @property
    def execution_count(
        self,
    ) -> int:
        """
        Quantidade de agentes de
        enriquecimento executados.
        """

        return len(
            self.executed_agents
        )

    @property
    def completed(
        self,
    ) -> bool:
        """
        Indica que todos os agentes de
        enriquecimento inicialmente
        solicitados foram executados.
        """

        return (
            self.executed_agents
            == self.requested_agents
        )

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo seguro da execução.
        """

        return {
            "case_id": self.case_id,
            "correlation_id": (
                self.correlation_id
            ),
            "requested_agents": list(
                self.requested_agents
            ),
            "executed_agents": list(
                self.executed_agents
            ),
            "execution_count": (
                self.execution_count
            ),
            "completed": self.completed,
            "stopped_before_non_enrichment": (
                self.stopped_before_non_enrichment
            ),
        }


class EnrichmentE2EController:
    """
    Controlador da Fase 7.3.

    Executa automaticamente somente
    a etapa de enriquecimento.

    O Supervisor continua responsável
    pelo roteamento entre os agentes.

    Quando um payload_provider é fornecido,
    o controller solicita a ele o payload
    correspondente ao especialista escolhido
    pelo Supervisor antes da execução.

    Esta classe nunca executa:

    - AG-02;
    - AG-03;
    - AG-09;
    - AG-10;
    - AG-11;
    - AG-12.

    Ela também nunca chama diretamente
    nenhum agente ou ferramenta.
    """

    def __init__(
        self,
        orchestrator: SOCOrchestrator
        | None = None,
        *,
        payload_provider: (
            EnrichmentPayloadProviderProtocol
            | None
        ) = None,
    ) -> None:
        """
        Inicializa a camada de
        enriquecimento.

        payload_provider é opcional para
        preservar compatibilidade com
        testes e consumidores anteriores.

        Quando presente, todo especialista
        de enriquecimento recebe payload
        produzido explicitamente pelo
        provider.
        """

        if (
            orchestrator is not None
            and not isinstance(
                orchestrator,
                SOCOrchestrator,
            )
        ):
            raise TypeError(
                "orchestrator precisa ser "
                "SOCOrchestrator."
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

        self._orchestrator = (
            orchestrator
            if orchestrator is not None
            else SOCOrchestrator()
        )

        self._payload_provider = (
            payload_provider
        )

        self._e2e = E2EExecutionController(
            self._orchestrator
        )

        self._supervised = (
            SupervisedE2EController(
                self._orchestrator
            )
        )

    @property
    def orchestrator(
        self,
    ) -> SOCOrchestrator:
        """
        Retorna o orquestrador oficial.
        """

        return self._orchestrator

    @property
    def payload_provider(
        self,
    ) -> (
        EnrichmentPayloadProviderProtocol
        | None
    ):
        """
        Retorna o provider configurado.

        None indica modo legado,
        preservado somente para
        compatibilidade.
        """

        return self._payload_provider

    def pending_enrichment_agents(
        self,
        case_state: CaseState,
    ) -> tuple[str, ...]:
        """
        Retorna somente agentes de
        enriquecimento atualmente
        pendentes no workflow.

        A ordem original do workflow
        é preservada.
        """

        snapshot = self._e2e.snapshot(
            case_state
        )

        return tuple(
            agent_id
            for agent_id
            in snapshot.pending_agents
            if agent_id
            in ENRICHMENT_AGENT_IDS
        )

    def _build_specialist_payload(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
    ) -> dict[str, Any] | None:
        """
        Prepara input_payload para o
        especialista selecionado.

        Quando nenhum provider foi
        configurado, retorna None para
        preservar o comportamento anterior.

        Quando existe provider:

        - o agente precisa pertencer
          ao enriquecimento;
        - build_payload precisa retornar
          Mapping;
        - o payload é copiado antes de
          ser enviado ao fluxo supervisionado.

        Qualquer inconsistência falha fechado.
        """

        if (
            agent_id
            not in ENRICHMENT_AGENT_IDS
        ):
            raise RuntimeError(
                "Payload solicitado para "
                "agente fora da etapa de "
                "enriquecimento: "
                f"{agent_id}."
            )

        provider = (
            self._payload_provider
        )

        if provider is None:
            return None

        payload = provider.build_payload(
            case_state=case_state,
            agent_id=agent_id,
        )

        if not isinstance(
            payload,
            Mapping,
        ):
            raise RuntimeError(
                "payload_provider retornou "
                "payload inválido para "
                f"{agent_id}: Mapping esperado."
            )

        return dict(
            payload
        )

    def run(
        self,
        case_state: CaseState,
    ) -> EnrichmentRunResult:
        """
        Executa automaticamente todos
        os enriquecimentos atualmente
        solicitados pelo workflow.

        Cada passo passa primeiro
        pelo AG-01 Supervisor.

        Depois da seleção do Supervisor:

        1. o agente escolhido é confirmado;
        2. o provider prepara o payload;
        3. o especialista é executado
           pelo fluxo supervisionado.

        A execução para imediatamente
        quando:

        - o caso se torna terminal;
        - não há mais enriquecimento;
        - o próximo agente não pertence
          à etapa de enriquecimento;
        - o Supervisor determina parada.

        Qualquer inconsistência falha
        fechado.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        initial_snapshot = (
            self._e2e.snapshot(
                case_state
            )
        )

        if initial_snapshot.terminal:
            raise RuntimeError(
                "Caso já está em estado final: "
                f"{initial_snapshot.case_status}."
            )

        requested_agents = (
            self.pending_enrichment_agents(
                case_state
            )
        )

        if not requested_agents:
            raise RuntimeError(
                "Workflow não possui agentes "
                "de enriquecimento pendentes."
            )

        executed_agents: list[str] = []

        supervisor_results: list[
            AgentExecutionResult
        ] = []

        specialist_results: list[
            AgentExecutionResult
        ] = []

        stopped_before_non_enrichment = False

        while True:
            snapshot = self._e2e.snapshot(
                case_state
            )

            if snapshot.terminal:
                break

            next_agent = (
                snapshot.next_pending_agent
            )

            if next_agent is None:
                break

            if (
                next_agent
                not in ENRICHMENT_AGENT_IDS
            ):
                stopped_before_non_enrichment = True
                break

            input_payload = (
                self._build_specialist_payload(
                    case_state=case_state,
                    agent_id=next_agent,
                )
            )

            step: SupervisedStepResult = (
                self._supervised
                .execute_supervised_step(
                    case_state,
                    input_payload=(
                        input_payload
                    ),
                )
            )

            supervisor_results.append(
                step.supervisor_result
            )

            if step.stopped:
                break

            specialist_result = (
                step.specialist_result
            )

            if specialist_result is None:
                raise RuntimeError(
                    "Supervisor permitiu "
                    "continuidade sem resultado "
                    "de especialista."
                )

            executed_agent = (
                specialist_result.agent_id
            )

            if (
                executed_agent
                not in ENRICHMENT_AGENT_IDS
            ):
                raise RuntimeError(
                    "Agente executado fora da "
                    "etapa de enriquecimento: "
                    f"{executed_agent}."
                )

            if (
                executed_agent
                != next_agent
            ):
                raise RuntimeError(
                    "Especialista executado "
                    "não corresponde ao agente "
                    "pendente preparado pelo "
                    "payload_provider: "
                    f"esperado={next_agent}, "
                    f"executado={executed_agent}."
                )

            if executed_agent in executed_agents:
                raise RuntimeError(
                    "Agente de enriquecimento "
                    "foi executado mais de uma vez "
                    "na mesma rodada: "
                    f"{executed_agent}."
                )

            executed_agents.append(
                executed_agent
            )

            specialist_results.append(
                specialist_result
            )

            if (
                len(executed_agents)
                > len(ENRICHMENT_AGENT_IDS)
            ):
                raise RuntimeError(
                    "Limite defensivo da etapa "
                    "de enriquecimento excedido."
                )

        return EnrichmentRunResult(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            requested_agents=(
                requested_agents
            ),
            executed_agents=tuple(
                executed_agents
            ),
            supervisor_results=tuple(
                supervisor_results
            ),
            specialist_results=tuple(
                specialist_results
            ),
            stopped_before_non_enrichment=(
                stopped_before_non_enrichment
            ),
        )


__all__ = [
    "ENRICHMENT_AGENT_IDS",
    "EnrichmentE2EController",
    "EnrichmentPayloadProviderProtocol",
    "EnrichmentRunResult",
]