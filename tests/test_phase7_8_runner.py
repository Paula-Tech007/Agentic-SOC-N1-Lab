"""
Testes formais da Fase 7.8.

Valida o runner E2E integrado.

Escopo:

- dispatch por agent_id;
- fluxo AG-03 até AG-12;
- enriquecimento agrupado;
- retry;
- estado terminal;
- agente desconhecido;
- limite de ciclos;
- imutabilidade do resultado.

As etapas individuais já possuem
testes próprios nas Fases 7.1..7.7.
"""

from __future__ import annotations

from dataclasses import (
    FrozenInstanceError,
)
from types import SimpleNamespace

import pytest

from core.orchestrator import (
    SOCOrchestrator,
)

from core.orchestrator.phase7_runner import (
    Phase7E2ERunner,
    Phase7RunResult,
    TRIAGE_AGENT_ID,
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


def create_case() -> CaseState:
    """
    Cria caso mínimo para o runner.
    """

    alert = Alert(
        alert_id="ALT-P7-8-0001",
        correlation_id=(
            "CORR-P7-8-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.8 Runner Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Evento defensivo simulado "
                "para teste E2E."
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
        case_id="CASE-P7-8-0001",
        correlation_id=(
            "CORR-P7-8-0001"
        ),
        alert=alert,
    )

    case.workflow.case_status = (
        CaseStatus.TRIAGING
    )

    case.workflow.completed_agents = [
        "AG-02",
    ]

    case.workflow.pending_agents = [
        "AG-03",
        "AG-04",
        "AG-05",
        "AG-09",
        "AG-10",
        "AG-11",
        "AG-12",
    ]

    case.workflow.step_count = 1

    return case


class FakeSupervised:
    """
    Simula somente AG-03.
    """

    def execute_supervised_step(
        self,
        case_state: CaseState,
    ):
        agent_id = (
            case_state
            .workflow
            .pending_agents
            .pop(0)
        )

        assert agent_id == "AG-03"

        case_state.workflow.completed_agents.append(
            agent_id
        )

        case_state.workflow.step_count += 1
        case_state.workflow.case_status = (
            CaseStatus.ENRICHING
        )

        return SimpleNamespace(
            stopped=False,
            specialist_result=(
                SimpleNamespace(
                    agent_id="AG-03",
                    success=True,
                )
            ),
        )


class FakeEnrichment:
    """
    Simula AG-04 e AG-05.
    """

    def run(
        self,
        case_state: CaseState,
    ):
        executed = []

        while (
            case_state.workflow.pending_agents
            and case_state.workflow.pending_agents[0]
            in {
                "AG-04",
                "AG-05",
                "AG-06",
                "AG-07",
                "AG-08",
            }
        ):
            agent_id = (
                case_state
                .workflow
                .pending_agents
                .pop(0)
            )

            executed.append(
                agent_id
            )

            case_state.workflow.completed_agents.append(
                agent_id
            )

            case_state.workflow.step_count += 1

        case_state.workflow.case_status = (
            CaseStatus.INVESTIGATING
        )

        return SimpleNamespace(
            executed_agents=tuple(
                executed
            )
        )


class FakeIncident:
    """
    Simula AG-09.
    """

    def run(
        self,
        case_state: CaseState,
    ):
        agent_id = (
            case_state
            .workflow
            .pending_agents
            .pop(0)
        )

        assert agent_id == "AG-09"

        case_state.workflow.completed_agents.append(
            agent_id
        )

        case_state.workflow.step_count += 1

        return SimpleNamespace(
            completed=True
        )


class FakeReflection:
    """
    Simula AG-10.
    """

    def run(
        self,
        case_state: CaseState,
    ):
        agent_id = (
            case_state
            .workflow
            .pending_agents
            .pop(0)
        )

        assert agent_id == "AG-10"

        case_state.workflow.completed_agents.append(
            agent_id
        )

        case_state.workflow.step_count += 1

        return SimpleNamespace(
            completed=True,
            has_retry=False,
        )


class FakeCaseManagement:
    """
    Simula AG-11.
    """

    def run(
        self,
        case_state: CaseState,
    ):
        agent_id = (
            case_state
            .workflow
            .pending_agents
            .pop(0)
        )

        assert agent_id == "AG-11"

        case_state.workflow.completed_agents.append(
            agent_id
        )

        case_state.workflow.step_count += 1

        return SimpleNamespace(
            completed=True
        )


class FakeEscalation:
    """
    Simula AG-12 e finalização.
    """

    def run(
        self,
        case_state: CaseState,
    ):
        agent_id = (
            case_state
            .workflow
            .pending_agents
            .pop(0)
        )

        assert agent_id == "AG-12"

        case_state.workflow.completed_agents.append(
            agent_id
        )

        case_state.workflow.step_count += 1
        case_state.workflow.pending_agents = []

        case_state.workflow.case_status = (
            CaseStatus.ESCALATED_N2
        )

        return SimpleNamespace(
            completed=True
        )


def create_runner(
    *,
    max_cycles: int = 32,
) -> Phase7E2ERunner:
    """
    Runner com estágios fake
    para testar somente integração.
    """

    runner = Phase7E2ERunner(
        SOCOrchestrator(),
        max_cycles=max_cycles,
    )

    runner._supervised = FakeSupervised()
    runner._enrichment = FakeEnrichment()
    runner._incident = FakeIncident()
    runner._reflection = FakeReflection()
    runner._case_management = (
        FakeCaseManagement()
    )
    runner._escalation = (
        FakeEscalation()
    )

    return runner


def test_phase7_8_triage_agent_id() -> None:
    """
    Triage integrado continua AG-03.
    """

    assert TRIAGE_AGENT_ID == "AG-03"


def test_phase7_8_rejects_invalid_orchestrator() -> None:
    """
    Runner aceita somente
    SOCOrchestrator válido.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        Phase7E2ERunner(
            object()
        )


def test_phase7_8_validates_max_cycles() -> None:
    """
    Guardrail precisa estar
    entre 1 e 100.
    """

    with pytest.raises(
        ValueError,
        match="entre 1 e 100",
    ):
        Phase7E2ERunner(
            max_cycles=0
        )

    with pytest.raises(
        ValueError,
        match="entre 1 e 100",
    ):
        Phase7E2ERunner(
            max_cycles=101
        )


def test_phase7_8_runs_full_case_to_terminal() -> None:
    """
    Fluxo integrado deve percorrer
    todos os estágios e terminar.
    """

    case = create_case()

    runner = create_runner()

    result = runner.run(
        case
    )

    assert isinstance(
        result,
        Phase7RunResult,
    )

    assert (
        result.executed_agents
        == (
            "AG-03",
            "AG-04",
            "AG-05",
            "AG-09",
            "AG-10",
            "AG-11",
            "AG-12",
        )
    )

    assert (
        result.execution_count
        == 7
    )

    assert (
        result.terminal
        is True
    )

    assert (
        result.final_case_status
        == "ESCALATED_N2"
    )

    assert (
        case.workflow.pending_agents
        == []
    )

    assert (
        case.workflow.case_status
        == CaseStatus.ESCALATED_N2
    )


def test_phase7_8_accepts_already_terminal_case() -> None:
    """
    Caso já terminal retorna sem
    executar novos agentes.
    """

    case = create_case()

    case.workflow.case_status = (
        CaseStatus.CLOSED_N1
    )

    case.workflow.pending_agents = []

    runner = create_runner()

    result = runner.run(
        case
    )

    assert (
        result.executed_agents
        == ()
    )

    assert result.cycles == 0

    assert result.terminal is True

    assert (
        result.final_case_status
        == "CLOSED_N1"
    )


def test_phase7_8_unknown_agent_fails_closed() -> None:
    """
    Agent ID inesperado deve
    falhar fechado.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-99",
    ]

    runner = create_runner()

    with pytest.raises(
        RuntimeError,
        match="não suportado",
    ):
        runner.run(
            case
        )


def test_phase7_8_cycle_guardrail() -> None:
    """
    Runner deve possuir limite
    próprio de ciclos.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-03",
        "AG-04",
        "AG-09",
    ]

    runner = create_runner(
        max_cycles=1
    )

    with pytest.raises(
        RuntimeError,
        match="Limite defensivo",
    ):
        runner.run(
            case
        )


def test_phase7_8_result_is_immutable_and_safe() -> None:
    """
    Resultado integrado deve ser
    imutável e possuir summary.
    """

    result = Phase7RunResult(
        case_id="CASE-P7-8-0001",
        correlation_id=(
            "CORR-P7-8-0001"
        ),
        initial_case_status=(
            "TRIAGING"
        ),
        final_case_status=(
            "ESCALATED_N2"
        ),
        executed_agents=(
            "AG-03",
            "AG-12",
        ),
        cycles=2,
        terminal=True,
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-8-0001"
            ),
            "correlation_id": (
                "CORR-P7-8-0001"
            ),
            "initial_case_status": (
                "TRIAGING"
            ),
            "final_case_status": (
                "ESCALATED_N2"
            ),
            "executed_agents": [
                "AG-03",
                "AG-12",
            ],
            "execution_count": 2,
            "cycles": 2,
            "terminal": True,
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )