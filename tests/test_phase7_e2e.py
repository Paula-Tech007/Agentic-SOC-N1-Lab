"""
Testes formais da Fase 7.1
do Agentic SOC N1 Lab.

Valida a fundação E2E controlada:

- snapshot imutável do workflow;
- identificação do próximo agente;
- reconhecimento de estados finais;
- bloqueio do AG-01 nesta etapa;
- bloqueio de reexecução do AG-02;
- fail-closed para agentes inesperados;
- bootstrap delegado ao SOCOrchestrator;
- execução controlada de um especialista;
- preservação do Runtime e do CaseState.

A Fase 7.1 NÃO implementa ainda
o loop automático do Supervisor.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from agents.alert_intake import AlertIntakeAgent
from agents.triage import TriageAnalystAgent

from core.orchestrator import (
    AgentRegistry,
    AgentRuntime,
    SOCOrchestrator,
)

from core.orchestrator.e2e import (
    E2EExecutionController,
    E2EWorkflowSnapshot,
    PHASE7_SPECIALIST_AGENT_IDS,
    TERMINAL_CASE_STATUSES,
)

from core.schemas import (
    AgentStatus,
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


def create_test_case(
    *,
    case_id: str = "CASE-PHASE7-0001",
    correlation_id: str = "CORR-PHASE7-0001",
    case_status: CaseStatus = CaseStatus.INVESTIGATING,
) -> CaseState:
    """
    Cria CaseState mínimo válido
    para os testes da Fase 7.1.
    """

    alert = Alert(
        alert_id="ALT-PHASE7-0001",
        correlation_id=correlation_id,
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name="Phase 7 Test Rule",
        ),
        event=AlertEvent(
            event_type=AlertType.AUTH_BRUTE_FORCE,
            category="authentication",
            message=(
                "Evento defensivo simulado "
                "para teste E2E."
            ),
            raw_event={
                "username": "lab.user",
                "source_ip": "203.0.113.10",
            },
        ),
        initial_severity=Severity.HIGH,
    )

    case = CaseState(
        case_id=case_id,
        correlation_id=correlation_id,
        alert=alert,
    )

    case.workflow.case_status = (
        case_status
    )

    return case


def create_triage_orchestrator() -> SOCOrchestrator:
    """
    Runtime controlado contendo
    somente AG-03.
    """

    registry = AgentRegistry()

    registry.register(
        TriageAnalystAgent()
    )

    return SOCOrchestrator(
        AgentRuntime(
            registry
        )
    )


def test_phase7_1_specialist_catalog() -> None:
    """
    Fase 7.1 permite somente
    AG-03 até AG-12.
    """

    assert PHASE7_SPECIALIST_AGENT_IDS == (
        "AG-03",
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-07",
        "AG-08",
        "AG-09",
        "AG-10",
        "AG-11",
        "AG-12",
    )

    assert (
        "AG-01"
        not in PHASE7_SPECIALIST_AGENT_IDS
    )

    assert (
        "AG-02"
        not in PHASE7_SPECIALIST_AGENT_IDS
    )


def test_phase7_1_terminal_status_catalog() -> None:
    """
    Estados finais conhecidos devem
    permanecer explícitos.
    """

    assert TERMINAL_CASE_STATUSES == {
        "CLOSED_N1",
        "ESCALATED_N2",
        "WAITING_HUMAN",
    }


def test_phase7_1_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator válido.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        E2EExecutionController(
            orchestrator=object()
        )


def test_phase7_1_snapshot_preserves_workflow() -> None:
    """
    Snapshot deve refletir o workflow
    sem alterar o CaseState.
    """

    case = create_test_case(
        case_status=(
            CaseStatus.ENRICHING
        )
    )

    case.workflow.current_agent = (
        "AG-04"
    )

    case.workflow.pending_agents = [
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-08",
    ]

    case.workflow.completed_agents = [
        "AG-02",
        "AG-03",
    ]

    case.workflow.failed_agents = []

    case.workflow.skipped_agents = [
        "AG-07",
    ]

    case.workflow.step_count = 2

    controller = (
        E2EExecutionController()
    )

    snapshot = controller.snapshot(
        case
    )

    assert isinstance(
        snapshot,
        E2EWorkflowSnapshot,
    )

    assert (
        snapshot.case_id
        == case.case_id
    )

    assert (
        snapshot.correlation_id
        == case.correlation_id
    )

    assert (
        snapshot.case_status
        == "ENRICHING"
    )

    assert (
        snapshot.current_agent
        == "AG-04"
    )

    assert snapshot.pending_agents == (
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-08",
    )

    assert snapshot.completed_agents == (
        "AG-02",
        "AG-03",
    )

    assert snapshot.skipped_agents == (
        "AG-07",
    )

    assert (
        snapshot.next_pending_agent
        == "AG-04"
    )

    assert (
        snapshot.terminal
        is False
    )


def test_phase7_1_snapshot_is_immutable() -> None:
    """
    Snapshot operacional não pode
    ser alterado posteriormente.
    """

    case = create_test_case()

    controller = (
        E2EExecutionController()
    )

    snapshot = controller.snapshot(
        case
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        snapshot.case_status = (
            "CLOSED_N1"
        )


def test_phase7_1_detects_terminal_case() -> None:
    """
    CLOSED_N1 deve interromper
    continuidade E2E.
    """

    case = create_test_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = []

    controller = (
        E2EExecutionController()
    )

    assert (
        controller.is_terminal(
            case
        )
        is True
    )

    assert (
        controller.next_pending_agent(
            case
        )
        is None
    )


def test_phase7_1_blocks_supervisor_auto_execution() -> None:
    """
    AG-01 pertence à Fase 7.2
    e não pode ser executado
    automaticamente na 7.1.
    """

    case = create_test_case()

    case.workflow.pending_agents = [
        "AG-01",
    ]

    controller = (
        E2EExecutionController()
    )

    with pytest.raises(
        RuntimeError,
        match="AG-01 Supervisor",
    ):
        controller.execute_next_pending(
            case
        )


def test_phase7_1_blocks_alert_intake_reexecution() -> None:
    """
    AG-02 é exclusivo do bootstrap.
    """

    case = create_test_case()

    case.workflow.pending_agents = [
        "AG-02",
    ]

    controller = (
        E2EExecutionController()
    )

    with pytest.raises(
        RuntimeError,
        match="AG-02 Alert Intake",
    ):
        controller.execute_next_pending(
            case
        )


def test_phase7_1_fails_closed_for_unknown_agent() -> None:
    """
    Agent ID inesperado deve
    falhar fechado.
    """

    case = create_test_case()

    case.workflow.pending_agents = [
        "AG-99",
    ]

    controller = (
        E2EExecutionController()
    )

    with pytest.raises(
        RuntimeError,
        match="não autorizado",
    ):
        controller.execute_next_pending(
            case
        )


def test_phase7_1_bootstrap_delegates_to_orchestrator() -> None:
    """
    Bootstrap E2E deve continuar
    utilizando o AG-02 oficial.
    """

    registry = AgentRegistry()

    registry.register(
        AlertIntakeAgent()
    )

    orchestrator = SOCOrchestrator(
        AgentRuntime(
            registry
        )
    )

    controller = (
        E2EExecutionController(
            orchestrator
        )
    )

    raw_alert = {
        "alert_id": "ALT-P7-BOOT-0001",
        "source": {
            "system": "SIEM",
            "product": "Lab-SIEM",
            "rule_name": (
                "Phase 7 Bootstrap Test"
            ),
        },
        "event": {
            "event_type": (
                "AUTH_BRUTE_FORCE"
            ),
            "category": (
                "authentication"
            ),
            "message": (
                "Falhas de autenticação "
                "simuladas no laboratório."
            ),
            "raw_event": {
                "username": "lab.user",
                "source_ip": (
                    "203.0.113.10"
                ),
            },
        },
        "initial_severity": "HIGH",
    }

    case, result = controller.bootstrap(
        raw_alert,
        case_id="CASE-P7-BOOT-0001",
        correlation_id=(
            "CORR-P7-BOOT-0001"
        ),
    )

    assert (
        result.status
        == AgentStatus.COMPLETED
    )

    assert (
        result.success
        is True
    )

    assert (
        case
        is not None
    )

    assert (
        case.case_id
        == "CASE-P7-BOOT-0001"
    )

    assert (
        case.correlation_id
        == "CORR-P7-BOOT-0001"
    )

    assert (
        case.workflow.completed_agents
        == ["AG-02"]
    )

    assert (
        case.workflow.step_count
        == 1
    )


def test_phase7_1_executes_one_pending_specialist() -> None:
    """
    Controller deve executar somente
    o primeiro especialista pendente.

    O Runtime e o SOCOrchestrator
    continuam responsáveis pela
    execução e aplicação do resultado.
    """

    orchestrator = (
        create_triage_orchestrator()
    )

    controller = (
        E2EExecutionController(
            orchestrator
        )
    )

    case = create_test_case(
        case_status=(
            CaseStatus.TRIAGING
        )
    )

    case.workflow.completed_agents = [
        "AG-02",
    ]

    case.workflow.pending_agents = [
        "AG-03",
    ]

    case.workflow.step_count = 1

    result = (
        controller
        .execute_next_pending(
            case
        )
    )

    assert (
        result.status
        == AgentStatus.COMPLETED
    )

    assert (
        result.success
        is True
    )

    assert (
        result.agent_id
        == "AG-03"
    )

    assert (
        case.triage
        is not None
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


def test_phase7_1_terminal_case_cannot_execute() -> None:
    """
    Caso finalizado não pode executar
    novo especialista.
    """

    case = create_test_case(
        case_status=(
            CaseStatus.ESCALATED_N2
        )
    )

    case.workflow.pending_agents = [
        "AG-03",
    ]

    controller = (
        E2EExecutionController()
    )

    with pytest.raises(
        RuntimeError,
        match="estado final",
    ):
        controller.execute_next_pending(
            case
        )