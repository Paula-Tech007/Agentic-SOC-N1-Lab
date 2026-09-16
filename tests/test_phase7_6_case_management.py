"""
Testes formais da Fase 7.6.

Valida:

- AG-11 Case Management;
- execução via Supervisor;
- fail-closed;
- caso final bloqueado;
- AG-11 precisa ser o próximo;
- AG-12 nunca é executado aqui;
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

from core.orchestrator.case_management_stage import (
    CASE_MANAGEMENT_AGENT_ID,
    CaseManagementE2EController,
    CaseManagementStageResult,
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
    Simula Supervisor + AG-11.
    """

    def __init__(
        self,
        case_state: CaseState,
    ) -> None:
        self._case_state = (
            case_state
        )

        self.calls: list[str] = []

    def execute_supervised_step(
        self,
        case_state: CaseState,
    ):
        """
        Simula execução exclusiva
        do AG-11.
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
            == CASE_MANAGEMENT_AGENT_ID
        )

        self.calls.append(
            selected_agent
        )

        case_state.workflow.pending_agents = [
            value
            for value
            in case_state
            .workflow
            .pending_agents
            if value
            != selected_agent
        ]

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

        return SimpleNamespace(
            decision=SimpleNamespace(
                next_agent_id=(
                    CASE_MANAGEMENT_AGENT_ID
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
                        CASE_MANAGEMENT_AGENT_ID
                    )
                )
            ),
            stopped=False,
        )


def create_case(
    *,
    case_status: CaseStatus = (
        CaseStatus.INVESTIGATING
    ),
) -> CaseState:
    """
    Cria caso defensivo da 7.6.
    """

    alert = Alert(
        alert_id="ALT-P7-6-0001",
        correlation_id=(
            "CORR-P7-6-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.6 Case Management"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Caso simulado aguardando "
                "documentação."
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
        case_id="CASE-P7-6-0001",
        correlation_id=(
            "CORR-P7-6-0001"
        ),
        alert=alert,
    )

    case.workflow.case_status = (
        case_status
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
    ]

    case.workflow.step_count = 8

    return case


def create_controller(
    case_state: CaseState,
) -> tuple[
    CaseManagementE2EController,
    FakeSupervisedController,
]:
    """
    Controller da 7.6 com
    Supervisor fake.
    """

    controller = (
        CaseManagementE2EController(
            SOCOrchestrator()
        )
    )

    fake = FakeSupervisedController(
        case_state
    )

    controller._supervised = fake

    return (
        controller,
        fake,
    )


def test_phase7_6_agent_id() -> None:
    """
    Fase 7.6 é exclusiva do AG-11.
    """

    assert (
        CASE_MANAGEMENT_AGENT_ID
        == "AG-11"
    )


def test_phase7_6_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        CaseManagementE2EController(
            object()
        )


def test_phase7_6_ready_only_for_ag11() -> None:
    """
    ready() só retorna True
    quando AG-11 é o primeiro.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-11",
        "AG-12",
    ]

    controller = (
        CaseManagementE2EController()
    )

    assert (
        controller.ready(
            case
        )
        is True
    )

    case.workflow.pending_agents = [
        "AG-12",
    ]

    assert (
        controller.ready(
            case
        )
        is False
    )


def test_phase7_6_blocks_terminal_case() -> None:
    """
    Caso final não executa AG-11.
    """

    case = create_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = [
        "AG-11",
    ]

    controller = (
        CaseManagementE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="estado final",
    ):
        controller.run(
            case
        )


def test_phase7_6_requires_ag11_as_next_agent() -> None:
    """
    Etapa não pode saltar
    diretamente para AG-12.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-12",
    ]

    controller = (
        CaseManagementE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="não é o próximo agente",
    ):
        controller.run(
            case
        )


def test_phase7_6_executes_only_ag11() -> None:
    """
    Executa AG-11 e deixa
    AG-12 pendente.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-11",
        "AG-12",
    ]

    (
        controller,
        fake,
    ) = create_controller(
        case
    )

    result = controller.run(
        case
    )

    assert isinstance(
        result,
        CaseManagementStageResult,
    )

    assert fake.calls == [
        "AG-11",
    ]

    assert (
        result.executed_agent_id
        == "AG-11"
    )

    assert (
        result.completed
        is True
    )

    assert (
        result.next_pending_agent
        == "AG-12"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-12",
        ]
    )

    assert (
        "AG-11"
        in case
        .workflow
        .completed_agents
    )

    assert (
        "AG-12"
        not in case
        .workflow
        .completed_agents
    )

    assert (
        case.workflow.step_count
        == 9
    )


def test_phase7_6_never_executes_ag12() -> None:
    """
    AG-12 pertence à Fase 7.7.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-11",
        "AG-12",
    ]

    (
        controller,
        fake,
    ) = create_controller(
        case
    )

    result = controller.run(
        case
    )

    assert fake.calls == [
        "AG-11",
    ]

    assert (
        result.next_pending_agent
        == "AG-12"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-12",
        ]
    )


def test_phase7_6_result_is_immutable_and_safe() -> None:
    """
    Resultado deve ser imutável
    e possuir summary seguro.
    """

    supervisor_result = (
        FakeExecutionResult(
            agent_id="AG-01"
        )
    )

    case_management_result = (
        FakeExecutionResult(
            agent_id="AG-11"
        )
    )

    result = CaseManagementStageResult(
        case_id="CASE-P7-6-0001",
        correlation_id=(
            "CORR-P7-6-0001"
        ),
        supervisor_result=(
            supervisor_result
        ),
        case_management_result=(
            case_management_result
        ),
        next_pending_agent="AG-12",
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-6-0001"
            ),
            "correlation_id": (
                "CORR-P7-6-0001"
            ),
            "executed_agent_id": (
                "AG-11"
            ),
            "completed": True,
            "next_pending_agent": (
                "AG-12"
            ),
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )