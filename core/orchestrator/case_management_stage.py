"""
Orquestração de Case Management
do Agentic SOC N1 Lab.

Fase 7.6 — Case Management controlado.

Fluxo:

    QA concluído
        ↓
    AG-01 Supervisor
        ↓
    AG-11 Case Management
        ↓
    documentação/auditoria
        ↓
    parar antes do AG-12

Esta camada:

- executa somente AG-11;
- exige AG-11 como próximo agente;
- usa o Supervisor da Fase 7.2;
- não executa AG-12 automaticamente;
- não chama tools diretamente;
- não contorna Runtime;
- não contorna permissões;
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


CASE_MANAGEMENT_AGENT_ID = "AG-11"


@dataclass(
    frozen=True,
    slots=True,
)
class CaseManagementStageResult:
    """
    Resultado imutável da etapa AG-11.
    """

    case_id: str
    correlation_id: str

    supervisor_result: AgentExecutionResult
    case_management_result: AgentExecutionResult

    next_pending_agent: str | None

    @property
    def executed_agent_id(
        self,
    ) -> str:
        """
        Agente executado nesta etapa.
        """

        return (
            self.case_management_result.agent_id
        )

    @property
    def completed(
        self,
    ) -> bool:
        """
        Indica conclusão válida
        do AG-11.
        """

        return (
            self.case_management_result.success
            and self.case_management_result.agent_id
            == CASE_MANAGEMENT_AGENT_ID
        )

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo seguro da etapa.
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


class CaseManagementE2EController:
    """
    Controlador da Fase 7.6.

    Executa:

        AG-01 Supervisor
             ↓
        AG-11 Case Management

    e encerra esta etapa.

    AG-12 pertence à Fase 7.7.
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
        True somente quando AG-11
        é o próximo agente.
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
            == CASE_MANAGEMENT_AGENT_ID
        )

    def run(
        self,
        case_state: CaseState,
    ) -> CaseManagementStageResult:
        """
        Executa exatamente AG-11.

        Regras:

        - caso não pode estar final;
        - AG-11 deve ser o próximo;
        - Supervisor deve selecionar AG-11;
        - somente um especialista é executado;
        - AG-11 não pode permanecer pendente;
        - AG-12 não é executado aqui.
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
            != CASE_MANAGEMENT_AGENT_ID
        ):
            raise RuntimeError(
                "AG-11 Case Management "
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
                "a execução antes do AG-11."
            )

        if (
            step.decision.next_agent_id
            != CASE_MANAGEMENT_AGENT_ID
        ):
            raise RuntimeError(
                "Supervisor não selecionou "
                "AG-11 Case Management."
            )

        case_management_result = (
            step.specialist_result
        )

        if case_management_result is None:
            raise RuntimeError(
                "Execução do AG-11 não "
                "produziu resultado."
            )

        if (
            case_management_result.agent_id
            != CASE_MANAGEMENT_AGENT_ID
        ):
            raise RuntimeError(
                "Especialista executado não "
                "corresponde ao AG-11."
            )

        if not case_management_result.success:
            raise RuntimeError(
                "AG-11 Case Management "
                "não concluiu com sucesso."
            )

        after = self._e2e.snapshot(
            case_state
        )

        if (
            CASE_MANAGEMENT_AGENT_ID
            in after.pending_agents
        ):
            raise RuntimeError(
                "AG-11 permaneceu pendente "
                "após sua execução."
            )

        return CaseManagementStageResult(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            supervisor_result=(
                step.supervisor_result
            ),
            case_management_result=(
                case_management_result
            ),
            next_pending_agent=(
                after.next_pending_agent
            ),
        )


__all__ = [
    "CASE_MANAGEMENT_AGENT_ID",
    "CaseManagementE2EController",
    "CaseManagementStageResult",
]