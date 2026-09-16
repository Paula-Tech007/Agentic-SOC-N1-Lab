"""
Testes formais da Fase 7.4.

Valida a camada de orquestração
do AG-09 Incident Analyst.

Escopo:

- somente AG-09;
- execução via Supervisor;
- fail-closed;
- estado final bloqueado;
- AG-09 precisa ser o próximo;
- AG-10 nunca é executado aqui;
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

from core.orchestrator.incident_stage import (
    INCIDENT_AGENT_ID,
    IncidentE2EController,
    IncidentStageResult,
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
    unitário de orquestração.
    """

    agent_id: str
    success: bool = True


class FakeSupervisedController:
    """
    Simula a camada supervisionada
    já validada na Fase 7.2.
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
        Simula Supervisor + AG-09.
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

        self.calls.append(
            selected_agent
        )

        case_state.workflow.pending_agents = [
            agent_id
            for agent_id
            in case_state
            .workflow
            .pending_agents
            if agent_id
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
                    selected_agent
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
                        selected_agent
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
    Cria caso defensivo da Fase 7.4.
    """

    alert = Alert(
        alert_id="ALT-P7-4-0001",
        correlation_id=(
            "CORR-P7-4-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.4 Incident Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Evento defensivo simulado "
                "para investigação."
            ),
            raw_event={
                "username": "lab.user",
                "source_ip": (
                    "203.0.113.10"
                ),
                "hostname": (
                    "LAB-SRV-001"
                ),
            },
        ),
        initial_severity=(
            Severity.HIGH
        ),
    )

    case = CaseState(
        case_id="CASE-P7-4-0001",
        correlation_id=(
            "CORR-P7-4-0001"
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
    ]

    case.workflow.step_count = 6

    return case


def create_controller(
    case_state: CaseState,
) -> tuple[
    IncidentE2EController,
    FakeSupervisedController,
]:
    """
    Cria controller da Fase 7.4
    com Supervisor fake somente
    para isolar esta camada.
    """

    controller = IncidentE2EController(
        SOCOrchestrator()
    )

    fake_supervised = (
        FakeSupervisedController(
            case_state
        )
    )

    controller._supervised = (
        fake_supervised
    )

    return (
        controller,
        fake_supervised,
    )


def test_phase7_4_incident_agent_id() -> None:
    """
    Etapa deve ser exclusiva do AG-09.
    """

    assert (
        INCIDENT_AGENT_ID
        == "AG-09"
    )


def test_phase7_4_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        IncidentE2EController(
            object()
        )


def test_phase7_4_ready_only_for_ag09() -> None:
    """
    ready() só pode retornar True
    quando AG-09 for o primeiro
    agente pendente.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-09",
        "AG-10",
    ]

    controller = (
        IncidentE2EController()
    )

    assert (
        controller.ready(
            case
        )
        is True
    )

    case.workflow.pending_agents = [
        "AG-10",
    ]

    assert (
        controller.ready(
            case
        )
        is False
    )


def test_phase7_4_blocks_terminal_case() -> None:
    """
    Caso final não pode executar AG-09.
    """

    case = create_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = [
        "AG-09",
    ]

    controller = (
        IncidentE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="estado final",
    ):
        controller.run(
            case
        )


def test_phase7_4_requires_ag09_as_next_agent() -> None:
    """
    A etapa não pode saltar
    diretamente sobre outro agente.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-10",
    ]

    controller = (
        IncidentE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="não é o próximo agente",
    ):
        controller.run(
            case
        )


def test_phase7_4_executes_only_ag09() -> None:
    """
    Executa AG-09 e deixa AG-10
    pendente para a Fase 7.5.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-09",
        "AG-10",
    ]

    (
        controller,
        fake_supervised,
    ) = create_controller(
        case
    )

    result = controller.run(
        case
    )

    assert isinstance(
        result,
        IncidentStageResult,
    )

    assert (
        fake_supervised.calls
        == [
            "AG-09",
        ]
    )

    assert (
        result.executed_agent_id
        == "AG-09"
    )

    assert (
        result.completed
        is True
    )

    assert (
        result.next_pending_agent
        == "AG-10"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-10",
        ]
    )

    assert (
        "AG-09"
        in case.workflow.completed_agents
    )

    assert (
        "AG-10"
        not in case.workflow.completed_agents
    )

    assert (
        case.workflow.step_count
        == 7
    )


def test_phase7_4_never_executes_ag10() -> None:
    """
    AG-10 pertence à Fase 7.5.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-09",
        "AG-10",
        "AG-11",
    ]

    (
        controller,
        fake_supervised,
    ) = create_controller(
        case
    )

    result = controller.run(
        case
    )

    assert (
        fake_supervised.calls
        == [
            "AG-09",
        ]
    )

    assert (
        result.next_pending_agent
        == "AG-10"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-10",
            "AG-11",
        ]
    )


def test_phase7_4_result_is_immutable_and_safe() -> None:
    """
    Resultado da etapa deve ser
    imutável e possuir summary seguro.
    """

    supervisor_result = (
        FakeExecutionResult(
            agent_id="AG-01"
        )
    )

    incident_result = (
        FakeExecutionResult(
            agent_id="AG-09"
        )
    )

    result = IncidentStageResult(
        case_id="CASE-P7-4-0001",
        correlation_id=(
            "CORR-P7-4-0001"
        ),
        supervisor_result=(
            supervisor_result
        ),
        incident_result=(
            incident_result
        ),
        next_pending_agent="AG-10",
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-4-0001"
            ),
            "correlation_id": (
                "CORR-P7-4-0001"
            ),
            "executed_agent_id": (
                "AG-09"
            ),
            "completed": True,
            "next_pending_agent": (
                "AG-10"
            ),
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )