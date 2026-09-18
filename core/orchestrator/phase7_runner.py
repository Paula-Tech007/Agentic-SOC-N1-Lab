"""
Runner E2E da Fase 7
do Agentic SOC N1 Lab.

Fase 7.8 — Integração ponta a ponta.

Fluxo controlado:

    AG-03 Triage
        ↓
    AG-04..AG-08 Enrichment
        ↓
    AG-09 Incident Analyst
        ↓
    AG-10 Reflection/QA
        ↓
    retry controlado, quando aplicável
        ↓
    AG-11 Case Management
        ↓
    AG-12 Escalation
        ↓
    estado terminal

Estados finais:

- CLOSED_N1;
- ESCALATED_N2;
- WAITING_HUMAN.

Este runner não substitui:

- SOCOrchestrator;
- AgentRuntime;
- Supervisor;
- ToolRuntime;
- ToolPolicy;
- permissões;
- guardrails existentes.

Ele apenas integra as camadas já
validadas nas Fases 7.1 até 7.7.

O provider de payload de enriquecimento
é opcional e injetado pela camada de
aplicação.

Isso preserva a direção arquitetural:

app
    ↓
core

e impede dependência:

core
    ✕
app

Princípio:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.orchestrator.case_management_stage import (
    CASE_MANAGEMENT_AGENT_ID,
    CaseManagementE2EController,
)
from core.orchestrator.e2e import (
    E2EExecutionController,
)
from core.orchestrator.enrichment import (
    ENRICHMENT_AGENT_IDS,
    EnrichmentE2EController,
    EnrichmentPayloadProviderProtocol,
)
from core.orchestrator.escalation_stage import (
    ESCALATION_AGENT_ID,
    EscalationE2EController,
)
from core.orchestrator.incident_stage import (
    INCIDENT_AGENT_ID,
    IncidentE2EController,
)
from core.orchestrator.orchestrator import (
    SOCOrchestrator,
)
from core.orchestrator.reflection_stage import (
    REFLECTION_AGENT_ID,
    ReflectionE2EController,
)
from core.orchestrator.supervised import (
    SupervisedE2EController,
)
from core.state import (
    CaseState,
)


TRIAGE_AGENT_ID = "AG-03"


@dataclass(
    frozen=True,
    slots=True,
)
class Phase7RunResult:
    """
    Resultado imutável da execução
    integrada da Fase 7.
    """

    case_id: str
    correlation_id: str

    initial_case_status: str
    final_case_status: str

    executed_agents: tuple[str, ...]

    cycles: int
    terminal: bool

    @property
    def execution_count(
        self,
    ) -> int:
        """
        Quantidade de especialistas
        executados pelo runner.
        """

        return len(
            self.executed_agents
        )

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo operacional seguro.
        """

        return {
            "case_id": self.case_id,
            "correlation_id": (
                self.correlation_id
            ),
            "initial_case_status": (
                self.initial_case_status
            ),
            "final_case_status": (
                self.final_case_status
            ),
            "executed_agents": list(
                self.executed_agents
            ),
            "execution_count": (
                self.execution_count
            ),
            "cycles": self.cycles,
            "terminal": self.terminal,
        }


class Phase7E2ERunner:
    """
    Integra as etapas 7.1 até 7.7.

    Toda decisão continua passando
    pelas camadas oficiais existentes.

    O runner nunca chama um agente
    diretamente.

    Quando um payload_provider é
    configurado, ele é entregue
    exclusivamente ao controller
    oficial de enriquecimento.
    """

    def __init__(
        self,
        orchestrator: SOCOrchestrator
        | None = None,
        *,
        max_cycles: int = 32,
        payload_provider: (
            EnrichmentPayloadProviderProtocol
            | None
        ) = None,
    ) -> None:
        """
        Inicializa o runner.

        max_cycles é um guardrail
        adicional contra loops.

        payload_provider é opcional
        para preservar compatibilidade
        com consumidores antigos.

        Quando fornecido, precisa possuir
        build_payload().
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
            isinstance(
                max_cycles,
                bool,
            )
            or not isinstance(
                max_cycles,
                int,
            )
        ):
            raise TypeError(
                "max_cycles precisa ser int."
            )

        if (
            max_cycles < 1
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

        self._orchestrator = (
            orchestrator
            if orchestrator is not None
            else SOCOrchestrator()
        )

        self._max_cycles = (
            max_cycles
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

        self._enrichment = (
            EnrichmentE2EController(
                self._orchestrator,
                payload_provider=(
                    self._payload_provider
                ),
            )
        )

        self._incident = (
            IncidentE2EController(
                self._orchestrator
            )
        )

        self._reflection = (
            ReflectionE2EController(
                self._orchestrator
            )
        )

        self._case_management = (
            CaseManagementE2EController(
                self._orchestrator
            )
        )

        self._escalation = (
            EscalationE2EController(
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
    def max_cycles(
        self,
    ) -> int:
        """
        Guardrail máximo do runner.
        """

        return self._max_cycles

    @property
    def payload_provider(
        self,
    ) -> (
        EnrichmentPayloadProviderProtocol
        | None
    ):
        """
        Retorna o provider configurado
        para a etapa de enriquecimento.
        """

        return self._payload_provider

    def run(
        self,
        case_state: CaseState,
    ) -> Phase7RunResult:
        """
        Executa o workflow até atingir
        estado terminal.

        O próximo agente sempre é
        obtido do WorkflowState.

        O runner falha fechado para
        qualquer agente inesperado.
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

        initial_case_status = (
            initial_snapshot.case_status
        )

        executed_agents: list[str] = []

        cycles = 0

        while True:
            snapshot = self._e2e.snapshot(
                case_state
            )

            if snapshot.terminal:
                return Phase7RunResult(
                    case_id=(
                        case_state.case_id
                    ),
                    correlation_id=(
                        case_state.correlation_id
                    ),
                    initial_case_status=(
                        initial_case_status
                    ),
                    final_case_status=(
                        snapshot.case_status
                    ),
                    executed_agents=tuple(
                        executed_agents
                    ),
                    cycles=cycles,
                    terminal=True,
                )

            if cycles >= self._max_cycles:
                raise RuntimeError(
                    "Limite defensivo de ciclos "
                    "da Fase 7 excedido."
                )

            next_agent = (
                snapshot.next_pending_agent
            )

            if next_agent is None:
                raise RuntimeError(
                    "Workflow não está terminal "
                    "e não possui agente pendente."
                )

            cycles += 1

            if (
                next_agent
                == TRIAGE_AGENT_ID
            ):
                step = (
                    self._supervised
                    .execute_supervised_step(
                        case_state
                    )
                )

                if step.stopped:
                    raise RuntimeError(
                        "Supervisor interrompeu "
                        "o workflow antes do AG-03."
                    )

                specialist = (
                    step.specialist_result
                )

                if specialist is None:
                    raise RuntimeError(
                        "AG-03 não produziu "
                        "resultado."
                    )

                if (
                    specialist.agent_id
                    != TRIAGE_AGENT_ID
                ):
                    raise RuntimeError(
                        "Especialista executado "
                        "não corresponde ao AG-03."
                    )

                executed_agents.append(
                    TRIAGE_AGENT_ID
                )

                continue

            if (
                next_agent
                in ENRICHMENT_AGENT_IDS
            ):
                result = (
                    self._enrichment.run(
                        case_state
                    )
                )

                if not result.executed_agents:
                    raise RuntimeError(
                        "Etapa de enriquecimento "
                        "não executou agentes."
                    )

                executed_agents.extend(
                    result.executed_agents
                )

                continue

            if (
                next_agent
                == INCIDENT_AGENT_ID
            ):
                result = (
                    self._incident.run(
                        case_state
                    )
                )

                if not result.completed:
                    raise RuntimeError(
                        "Etapa AG-09 não "
                        "foi concluída."
                    )

                executed_agents.append(
                    INCIDENT_AGENT_ID
                )

                continue

            if (
                next_agent
                == REFLECTION_AGENT_ID
            ):
                result = (
                    self._reflection.run(
                        case_state
                    )
                )

                if not result.completed:
                    raise RuntimeError(
                        "Etapa AG-10 não "
                        "foi concluída."
                    )

                executed_agents.append(
                    REFLECTION_AGENT_ID
                )

                continue

            if (
                next_agent
                == CASE_MANAGEMENT_AGENT_ID
            ):
                result = (
                    self._case_management.run(
                        case_state
                    )
                )

                if not result.completed:
                    raise RuntimeError(
                        "Etapa AG-11 não "
                        "foi concluída."
                    )

                executed_agents.append(
                    CASE_MANAGEMENT_AGENT_ID
                )

                continue

            if (
                next_agent
                == ESCALATION_AGENT_ID
            ):
                result = (
                    self._escalation.run(
                        case_state
                    )
                )

                if not result.completed:
                    raise RuntimeError(
                        "Etapa AG-12 não "
                        "foi concluída."
                    )

                executed_agents.append(
                    ESCALATION_AGENT_ID
                )

                continue

            raise RuntimeError(
                "Workflow contém agente "
                "não suportado pela Fase 7: "
                f"{next_agent}."
            )

    def bootstrap_and_run(
        self,
        raw_alert: Mapping[str, Any],
        *,
        case_id: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[
        CaseState,
        Phase7RunResult,
    ]:
        """
        Executa bootstrap AG-02
        e depois inicia o runner E2E.

        O AG-02 continua sendo executado
        exclusivamente pelo
        SOCOrchestrator.bootstrap_case().
        """

        if not isinstance(
            raw_alert,
            Mapping,
        ):
            raise TypeError(
                "raw_alert precisa ser "
                "Mapping."
            )

        case_state, bootstrap_result = (
            self._e2e.bootstrap(
                raw_alert,
                case_id=case_id,
                correlation_id=(
                    correlation_id
                ),
            )
        )

        if not bootstrap_result.success:
            raise RuntimeError(
                "Bootstrap AG-02 falhou."
            )

        if case_state is None:
            raise RuntimeError(
                "Bootstrap AG-02 concluiu "
                "sem criar CaseState."
            )

        result = self.run(
            case_state
        )

        return (
            case_state,
            result,
        )


__all__ = [
    "Phase7E2ERunner",
    "Phase7RunResult",
    "TRIAGE_AGENT_ID",
]