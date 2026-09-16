"""
Testes formais da Fase 7.7.

Valida:

- AG-12 Escalation;
- execução via Supervisor;
- estados finais permitidos;
- CLOSED_N1;
- ESCALATED_N2;
- WAITING_HUMAN;
- fail-closed;
- fila pendente vazia;
- resultado imutável;
- summary seguro.
"""

from __future__ import annotations

from dataclasses import (
    FrozenInstanceError,
    dataclass,
)
from types import SimpleNamespace

import pytest

from core.orchestrator import (
    SOCOrchestrator,
)

from core.orchestrator.escalation_stage import (
    ESCALATION_AGENT_ID,
    EscalationE2EController,
    EscalationStageResult,
)

from core.schemas import (
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    CaseStatus,
    Severity,
)

from core.state import (
    CaseState,
)


@dataclass(
    frozen=True,
    slots=True,
)
class FakeExecutionResult:
    """
    Resultado mínimo para teste
    de orquestração.
    """

    agent_id: str
    success: bool = True


class FakeSupervisedController:
    """
    Simula Supervisor + AG-12.
    """

    def __init__(
        self,
        case_state: CaseState,
        *,
        final_status: CaseStatus,
    ) -> None:
        self._case_state = (
            case_state
        )

        self._final_status = (
            final_status
        )

        self.calls: list[str] = []

    def execute_supervised_step(
        self,
        case_state: CaseState,
    ):
        """
        Simula execução do AG-12
        e finalização do workflow.
        """

        assert (
            case_state
            is self._case_state
        )

        assert (
            case_state
            .workflow
            .pending_agents
        )

        selected_agent = (
            case_state
            .workflow
            .pending_agents[0]
        )

        assert (
            selected_agent
            == ESCALATION_AGENT_ID
        )

        self.calls.append(
            selected_agent
        )

        case_state.workflow.pending_agents = []

        if (
            selected_agent
            not in case_state
            .workflow
            .completed_agents
        ):
            case_state.workflow.completed_agents.append(
                selected_agent
            )

        case_state.workflow.step_count += 1

        case_state.workflow.case_status = (
            self._final_status
        )

        return SimpleNamespace(
            decision=SimpleNamespace(
                next_agent_id=(
                    ESCALATION_AGENT_ID
                ),
                should_continue=True,
            ),
            supervisor_result=(
                FakeExecutionResult(
                    agent_id="AG-01"
                )
            ),
            specialist_result=(
                FakeExecutionResult(
                    agent_id=(
                        ESCALATION_AGENT_ID
                    )
                )
            ),
            stopped=False,
        )


def create_case() -> CaseState:
    """
    Cria caso defensivo da 7.7.
    """

    alert = Alert(
        alert_id="ALT-P7-7-0001",
        correlation_id=(
            "CORR-P7-7-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.7 Escalation"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Caso simulado aguardando "
                "decisão final."
            ),
            raw_event={
                "username": "lab.user",
                "source_ip": (
                    "203.0.113.10"
                ),
            },
        ),
        initial_severity=(
            Severity.HIGH
        ),
    )

    case = CaseState(
        case_id="CASE-P7-7-0001",
        correlation_id=(
            "CORR-P7-7-0001"
        ),
        alert=alert,
    )

    case.workflow.case_status = (
        CaseStatus.INVESTIGATING
    )

    case.workflow.completed_agents = [
        "AG-02",
        "AG-03",
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-08",
        "AG-09",
        "AG-10",
        "AG-11",
    ]

    case.workflow.step_count = 9

    return case


def create_controller(
    case_state: CaseState,
    *,
    final_status: CaseStatus,
) -> tuple[
    EscalationE2EController,
    FakeSupervisedController,
]:
    """
    Controller com camada
    supervisionada fake.
    """

    controller = (
        EscalationE2EController(
            SOCOrchestrator()
        )
    )

    fake = FakeSupervisedController(
        case_state,
        final_status=final_status,
    )

    controller._supervised = fake

    return (
        controller,
        fake,
    )


def test_phase7_7_agent_id() -> None:
    """
    Fase final é exclusiva do AG-12.
    """

    assert (
        ESCALATION_AGENT_ID
        == "AG-12"
    )


def test_phase7_7_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        EscalationE2EController(
            object()
        )


def test_phase7_7_ready_only_for_ag12() -> None:
    """
    ready() somente quando AG-12
    é o primeiro pendente.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    controller = (
        EscalationE2EController()
    )

    assert (
        controller.ready(
            case
        )
        is True
    )

    case.workflow.pending_agents = []

    assert (
        controller.ready(
            case
        )
        is False
    )


@pytest.mark.parametrize(
    "final_status",
    [
        CaseStatus.CLOSED_N1,
        CaseStatus.ESCALATED_N2,
        CaseStatus.WAITING_HUMAN,
    ],
)
def test_phase7_7_accepts_terminal_decisions(
    final_status: CaseStatus,
) -> None:
    """
    AG-12 pode produzir qualquer
    estado terminal conhecido.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    (
        controller,
        fake,
    ) = create_controller(
        case,
        final_status=final_status,
    )

    result = controller.run(
        case
    )

    assert fake.calls == [
        "AG-12",
    ]

    assert (
        result.executed_agent_id
        == "AG-12"
    )

    assert (
        result.completed
        is True
    )

    assert (
        result.final_case_status
        == final_status.value
    )

    assert (
        case.workflow.pending_agents
        == []
    )

    assert (
        "AG-12"
        in case
        .workflow
        .completed_agents
    )

    assert (
        case.workflow.step_count
        == 10
    )


def test_phase7_7_closed_n1_flag() -> None:
    """
    CLOSED_N1 deve ser identificado.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    controller, _ = create_controller(
        case,
        final_status=(
            CaseStatus.CLOSED_N1
        ),
    )

    result = controller.run(
        case
    )

    assert result.closed_n1 is True
    assert result.escalated_to_n2 is False
    assert result.waiting_human is False


def test_phase7_7_escalated_n2_flag() -> None:
    """
    ESCALATED_N2 deve ser identificado.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    controller, _ = create_controller(
        case,
        final_status=(
            CaseStatus.ESCALATED_N2
        ),
    )

    result = controller.run(
        case
    )

    assert result.closed_n1 is False
    assert result.escalated_to_n2 is True
    assert result.waiting_human is False


def test_phase7_7_waiting_human_flag() -> None:
    """
    WAITING_HUMAN deve ser identificado.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    controller, _ = create_controller(
        case,
        final_status=(
            CaseStatus.WAITING_HUMAN
        ),
    )

    result = controller.run(
        case
    )

    assert result.closed_n1 is False
    assert result.escalated_to_n2 is False
    assert result.waiting_human is True


def test_phase7_7_requires_ag12_as_next_agent() -> None:
    """
    Fase não pode ser executada
    sem AG-12 pendente.
    """

    case = create_case()

    case.workflow.pending_agents = []

    controller = (
        EscalationE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="não é o próximo agente",
    ):
        controller.run(
            case
        )


def test_phase7_7_result_is_immutable_and_safe() -> None:
    """
    Resultado final deve ser
    imutável e possuir summary.
    """

    supervisor_result = (
        FakeExecutionResult(
            agent_id="AG-01"
        )
    )

    escalation_result = (
        FakeExecutionResult(
            agent_id="AG-12"
        )
    )

    result = EscalationStageResult(
        case_id="CASE-P7-7-0001",
        correlation_id=(
            "CORR-P7-7-0001"
        ),
        supervisor_result=(
            supervisor_result
        ),
        escalation_result=(
            escalation_result
        ),
        final_case_status=(
            "ESCALATED_N2"
        ),
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-7-0001"
            ),
            "correlation_id": (
                "CORR-P7-7-0001"
            ),
            "executed_agent_id": (
                "AG-12"
            ),
            "final_case_status": (
                "ESCALATED_N2"
            ),
            "completed": True,
            "escalated_to_n2": True,
            "closed_n1": False,
            "waiting_human": False,
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )