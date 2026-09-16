"""
Orquestração de Escalation
do Agentic SOC N1 Lab.

Fase 7.7 — AG-12 Escalation e finalização.

Fluxo:

    AG-11 concluído
        ↓
    AG-01 Supervisor
        ↓
    AG-12 Escalation
        ↓
    decisão final
        ↓
    CLOSED_N1
    ou
    ESCALATED_N2
    ou
    WAITING_HUMAN

Esta camada:

- executa somente AG-12;
- exige AG-12 como próximo agente;
- usa o Supervisor da Fase 7.2;
- exige estado terminal após execução;
- exige fila pendente vazia;
- não executa ações críticas;
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
    TERMINAL_CASE_STATUSES,
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


ESCALATION_AGENT_ID = "AG-12"


@dataclass(
    frozen=True,
    slots=True,
)
class EscalationStageResult:
    """
    Resultado imutável da etapa final.
    """

    case_id: str
    correlation_id: str

    supervisor_result: AgentExecutionResult
    escalation_result: AgentExecutionResult

    final_case_status: str

    @property
    def executed_agent_id(
        self,
    ) -> str:
        """
        Agente executado na etapa.
        """

        return (
            self.escalation_result.agent_id
        )

    @property
    def completed(
        self,
    ) -> bool:
        """
        Confirma execução válida
        e estado terminal conhecido.
        """

        return (
            self.escalation_result.success
            and self.escalation_result.agent_id
            == ESCALATION_AGENT_ID
            and self.final_case_status
            in TERMINAL_CASE_STATUSES
        )

    @property
    def escalated_to_n2(
        self,
    ) -> bool:
        """
        Indica escalonamento para SOC N2.
        """

        return (
            self.final_case_status
            == "ESCALATED_N2"
        )

    @property
    def closed_n1(
        self,
    ) -> bool:
        """
        Indica encerramento no próprio N1.
        """

        return (
            self.final_case_status
            == "CLOSED_N1"
        )

    @property
    def waiting_human(
        self,
    ) -> bool:
        """
        Indica necessidade de decisão humana.
        """

        return (
            self.final_case_status
            == "WAITING_HUMAN"
        )

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo seguro da decisão final.
        """

        return {
            "case_id": self.case_id,
            "correlation_id": (
                self.correlation_id
            ),
            "executed_agent_id": (
                self.executed_agent_id
            ),
            "final_case_status": (
                self.final_case_status
            ),
            "completed": self.completed,
            "escalated_to_n2": (
                self.escalated_to_n2
            ),
            "closed_n1": (
                self.closed_n1
            ),
            "waiting_human": (
                self.waiting_human
            ),
        }


class EscalationE2EController:
    """
    Controlador da Fase 7.7.

    Executa exatamente:

        AG-01 Supervisor
             ↓
        AG-12 Escalation

    O resultado precisa finalizar
    formalmente o WorkflowState.
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
        True somente quando AG-12
        é exatamente o próximo agente.
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
            == ESCALATION_AGENT_ID
        )

    def run(
        self,
        case_state: CaseState,
    ) -> EscalationStageResult:
        """
        Executa AG-12 e exige
        finalização válida do caso.

        Regras:

        - caso ainda não pode estar final;
        - AG-12 deve ser o próximo;
        - Supervisor deve selecionar AG-12;
        - AG-12 deve concluir com sucesso;
        - workflow deve ficar terminal;
        - pending_agents deve ficar vazio.
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
            != ESCALATION_AGENT_ID
        ):
            raise RuntimeError(
                "AG-12 Escalation não é "
                "o próximo agente do workflow."
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
                "a execução antes do AG-12."
            )

        if (
            step.decision.next_agent_id
            != ESCALATION_AGENT_ID
        ):
            raise RuntimeError(
                "Supervisor não selecionou "
                "AG-12 Escalation."
            )

        escalation_result = (
            step.specialist_result
        )

        if escalation_result is None:
            raise RuntimeError(
                "Execução do AG-12 não "
                "produziu resultado."
            )

        if (
            escalation_result.agent_id
            != ESCALATION_AGENT_ID
        ):
            raise RuntimeError(
                "Especialista executado não "
                "corresponde ao AG-12."
            )

        if not escalation_result.success:
            raise RuntimeError(
                "AG-12 Escalation não "
                "concluiu com sucesso."
            )

        after = self._e2e.snapshot(
            case_state
        )

        if not after.terminal:
            raise RuntimeError(
                "AG-12 concluiu sem colocar "
                "o caso em estado final."
            )

        if after.pending_agents:
            raise RuntimeError(
                "Caso finalizado ainda possui "
                "agentes pendentes."
            )

        if (
            ESCALATION_AGENT_ID
            not in after.completed_agents
        ):
            raise RuntimeError(
                "AG-12 não foi registrado "
                "como concluído."
            )

        return EscalationStageResult(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            supervisor_result=(
                step.supervisor_result
            ),
            escalation_result=(
                escalation_result
            ),
            final_case_status=(
                after.case_status
            ),
        )


__all__ = [
    "ESCALATION_AGENT_ID",
    "EscalationE2EController",
    "EscalationStageResult",
]