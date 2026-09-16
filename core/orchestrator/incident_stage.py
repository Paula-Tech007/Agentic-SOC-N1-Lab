"""
Orquestração do Incident Analyst
do Agentic SOC N1 Lab.

Fase 7.4 — Investigação controlada AG-09.

Fluxo:

    enriquecimentos concluídos
        ↓
    AG-01 Supervisor
        ↓
    AG-09 Incident Analyst
        ↓
    investigação registrada no CaseState
        ↓
    parar antes do AG-10

Esta camada:

- executa somente AG-09;
- exige AG-09 como próximo agente;
- usa o Supervisor da Fase 7.2;
- não executa AG-10 automaticamente;
- não executa Case Management;
- não executa Escalation;
- não chama tools diretamente;
- não contorna Runtime;
- mantém fail-closed.

Princípio:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


INCIDENT_AGENT_ID = "AG-09"


@dataclass(
    frozen=True,
    slots=True,
)
class IncidentStageResult:
    """
    Resultado imutável da etapa AG-09.
    """

    case_id: str
    correlation_id: str

    supervisor_result: AgentExecutionResult
    incident_result: AgentExecutionResult

    next_pending_agent: str | None

    @property
    def executed_agent_id(
        self,
    ) -> str:
        """
        Agente efetivamente executado.
        """

        return self.incident_result.agent_id

    @property
    def completed(
        self,
    ) -> bool:
        """
        Indica conclusão válida
        da etapa AG-09.
        """

        return (
            self.incident_result.success
            and self.incident_result.agent_id
            == INCIDENT_AGENT_ID
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
            "executed_agent_id": (
                self.executed_agent_id
            ),
            "completed": self.completed,
            "next_pending_agent": (
                self.next_pending_agent
            ),
        }


class IncidentE2EController:
    """
    Controlador da Fase 7.4.

    Executa exatamente:

        AG-01 Supervisor
             ↓
        AG-09 Incident Analyst

    e encerra esta etapa.

    AG-10 pertence à Fase 7.5.
    """

    def __init__(
        self,
        orchestrator: SOCOrchestrator
        | None = None,
    ) -> None:
        """
        Inicializa o controller.
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

        self._orchestrator = (
            orchestrator
            if orchestrator is not None
            else SOCOrchestrator()
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

    def ready(
        self,
        case_state: CaseState,
    ) -> bool:
        """
        Indica se AG-09 é exatamente
        o próximo agente do workflow.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        snapshot = self._e2e.snapshot(
            case_state
        )

        if snapshot.terminal:
            return False

        return (
            snapshot.next_pending_agent
            == INCIDENT_AGENT_ID
        )

    def run(
        self,
        case_state: CaseState,
    ) -> IncidentStageResult:
        """
        Executa a investigação AG-09.

        Regras:

        - caso não pode estar final;
        - AG-09 precisa ser o próximo;
        - Supervisor precisa selecionar AG-09;
        - somente um especialista é executado;
        - resultado precisa pertencer ao AG-09;
        - AG-09 não pode permanecer pendente;
        - AG-10 não é executado aqui.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        before = self._e2e.snapshot(
            case_state
        )

        if before.terminal:
            raise RuntimeError(
                "Caso já está em estado final: "
                f"{before.case_status}."
            )

        if (
            before.next_pending_agent
            != INCIDENT_AGENT_ID
        ):
            raise RuntimeError(
                "AG-09 Incident Analyst "
                "não é o próximo agente "
                "do workflow."
            )

        step: SupervisedStepResult = (
            self._supervised
            .execute_supervised_step(
                case_state
            )
        )

        if step.stopped:
            raise RuntimeError(
                "Supervisor interrompeu "
                "a execução antes do AG-09."
            )

        if (
            step.decision.next_agent_id
            != INCIDENT_AGENT_ID
        ):
            raise RuntimeError(
                "Supervisor não selecionou "
                "AG-09 para investigação."
            )

        incident_result = (
            step.specialist_result
        )

        if incident_result is None:
            raise RuntimeError(
                "Execução do AG-09 não "
                "produziu resultado."
            )

        if (
            incident_result.agent_id
            != INCIDENT_AGENT_ID
        ):
            raise RuntimeError(
                "Especialista executado não "
                "corresponde ao AG-09."
            )

        if not incident_result.success:
            raise RuntimeError(
                "AG-09 Incident Analyst "
                "não concluiu com sucesso."
            )

        after = self._e2e.snapshot(
            case_state
        )

        if (
            INCIDENT_AGENT_ID
            in after.pending_agents
        ):
            raise RuntimeError(
                "AG-09 permaneceu pendente "
                "após sua execução."
            )

        return IncidentStageResult(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            supervisor_result=(
                step.supervisor_result
            ),
            incident_result=(
                incident_result
            ),
            next_pending_agent=(
                after.next_pending_agent
            ),
        )


__all__ = [
    "INCIDENT_AGENT_ID",
    "IncidentE2EController",
    "IncidentStageResult",
]