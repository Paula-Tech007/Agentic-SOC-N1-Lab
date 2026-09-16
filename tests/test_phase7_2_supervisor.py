"""
Testes da Fase 7.2.

Valida execução automática controlada:

AG-01 Supervisor
    ↓
um especialista

Ainda não existe loop E2E completo.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from agents.supervisor import (
    SOCSupervisorAgent,
)
from agents.triage import (
    TriageAnalystAgent,
)

from core.orchestrator import (
    AgentRegistry,
    AgentRuntime,
    SOCOrchestrator,
)

from core.orchestrator.supervised import (
    SupervisedE2EController,
    SupervisedStepResult,
    SupervisorRoutingDecision,
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


def create_case(
    *,
    case_status: CaseStatus = (
        CaseStatus.TRIAGING
    ),
) -> CaseState:
    """
    Cria caso defensivo de laboratório.
    """

    alert = Alert(
        alert_id="ALT-P7-2-0001",
        correlation_id=(
            "CORR-P7-2-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.2 Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Falhas de autenticação "
                "simuladas."
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
        case_id="CASE-P7-2-0001",
        correlation_id=(
            "CORR-P7-2-0001"
        ),
        alert=alert,
    )

    case.workflow.case_status = (
        case_status
    )

    return case


def create_supervised_orchestrator(
    *,
    include_triage: bool = True,
) -> SOCOrchestrator:
    """
    Runtime controlado da Fase 7.2.
    """

    registry = AgentRegistry()

    registry.register(
        SOCSupervisorAgent()
    )

    if include_triage:
        registry.register(
            TriageAnalystAgent()
        )

    return SOCOrchestrator(
        AgentRuntime(
            registry
        )
    )


def test_phase7_2_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        SupervisedE2EController(
            object()
        )


def test_phase7_2_decision_is_immutable() -> None:
    """
    Decisão do Supervisor deve
    permanecer imutável.
    """

    decision = (
        SupervisorRoutingDecision(
            case_id="CASE-1",
            case_status="TRIAGING",
            next_agent_id="AG-03",
            should_continue=True,
            reason="Teste.",
            routing_source=(
                "PENDING_AGENTS"
            ),
        )
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        decision.next_agent_id = (
            "AG-12"
        )


def test_phase7_2_supervisor_routes_pending_agent() -> None:
    """
    AG-01 deve escolher AG-03
    quando ele está pendente.
    """

    orchestrator = (
        create_supervised_orchestrator()
    )

    controller = (
        SupervisedE2EController(
            orchestrator
        )
    )

    case = create_case()

    case.workflow.completed_agents = [
        "AG-02",
    ]

    case.workflow.pending_agents = [
        "AG-03",
    ]

    case.workflow.step_count = 1

    decision, result = (
        controller.route(
            case
        )
    )

    assert result.success is True

    assert result.agent_id == "AG-01"

    assert (
        decision.should_continue
        is True
    )

    assert (
        decision.next_agent_id
        == "AG-03"
    )

    assert (
        decision.routing_source
        == "PENDING_AGENTS"
    )

    assert (
        case.workflow.pending_agents[
            0
        ]
        == "AG-03"
    )

    assert (
        case.workflow.step_count
        == 1
    )


def test_phase7_2_executes_selected_specialist() -> None:
    """
    Um ciclo supervisionado deve
    executar AG-01 e depois AG-03.

    O Supervisor roteia, mas não
    incrementa step_count.

    O especialista AG-03 é quem
    incrementa o passo do workflow.
    """

    orchestrator = (
        create_supervised_orchestrator()
    )

    controller = (
        SupervisedE2EController(
            orchestrator
        )
    )

    case = create_case()

    case.workflow.completed_agents = [
        "AG-02",
    ]

    case.workflow.pending_agents = [
        "AG-03",
    ]

    case.workflow.step_count = 1

    result = (
        controller
        .execute_supervised_step(
            case
        )
    )

    assert isinstance(
        result,
        SupervisedStepResult,
    )

    assert (
        result.decision.next_agent_id
        == "AG-03"
    )

    assert (
        result.executed_agent_id
        == "AG-03"
    )

    assert (
        result.supervisor_result.agent_id
        == "AG-01"
    )

    assert (
        result.specialist_result
        is not None
    )

    assert (
        result.specialist_result.agent_id
        == "AG-03"
    )

    assert case.triage is not None

    assert (
        "AG-01"
        in case.workflow.completed_agents
    )

    assert (
        "AG-03"
        in case.workflow.completed_agents
    )

    assert (
        case.workflow.step_count
        == 2
    )

    assert (
        case.workflow.case_status
        == CaseStatus.ENRICHING
    )


def test_phase7_2_terminal_case_stops() -> None:
    """
    Caso final deve fazer o Supervisor
    interromper sem especialista.
    """

    orchestrator = (
        create_supervised_orchestrator(
            include_triage=False
        )
    )

    controller = (
        SupervisedE2EController(
            orchestrator
        )
    )

    case = create_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = []

    result = (
        controller
        .execute_supervised_step(
            case
        )
    )

    assert result.stopped is True

    assert (
        result.executed_agent_id
        is None
    )

    assert (
        result.specialist_result
        is None
    )

    assert (
        result.decision.should_continue
        is False
    )

    assert (
        result.decision.next_agent_id
        is None
    )


def test_phase7_2_supervisor_does_not_execute_specialist_in_route() -> None:
    """
    route() deve executar somente AG-01.
    """

    orchestrator = (
        create_supervised_orchestrator()
    )

    controller = (
        SupervisedE2EController(
            orchestrator
        )
    )

    case = create_case()

    case.workflow.completed_agents = [
        "AG-02",
    ]

    case.workflow.pending_agents = [
        "AG-03",
    ]

    case.workflow.step_count = 1

    controller.route(
        case
    )

    assert case.triage is None

    assert (
        "AG-03"
        not in case.workflow.completed_agents
    )

    assert (
        case.workflow.step_count
        == 1
    )


def test_phase7_2_summary_is_safe() -> None:
    """
    Summary da decisão deve
    preservar somente roteamento.
    """

    decision = (
        SupervisorRoutingDecision(
            case_id="CASE-1",
            case_status="TRIAGING",
            next_agent_id="AG-03",
            should_continue=True,
            reason=(
                "Agente pendente."
            ),
            routing_source=(
                "PENDING_AGENTS"
            ),
        )
    )

    summary = (
        decision.safe_summary()
    )

    assert summary == {
        "case_id": "CASE-1",
        "case_status": "TRIAGING",
        "next_agent_id": "AG-03",
        "should_continue": True,
        "reason": "Agente pendente.",
        "routing_source": (
            "PENDING_AGENTS"
        ),
    }