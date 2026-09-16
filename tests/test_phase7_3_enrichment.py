"""
Testes formais da Fase 7.3
do Agentic SOC N1 Lab.

Valida a camada controlada de
enriquecimento automático.

Escopo:

- catálogo AG-04..AG-08;
- filtragem dos agentes pendentes;
- preservação da ordem do workflow;
- fail-closed em caso final;
- fail-closed sem enriquecimento;
- execução sequencial controlada;
- parada antes de AG-09;
- imutabilidade do resultado;
- summary seguro.

Os agentes reais já possuem testes
próprios nas fases anteriores.

Aqui validamos especificamente
a lógica de orquestração da Fase 7.3.
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

from core.orchestrator.enrichment import (
    ENRICHMENT_AGENT_IDS,
    EnrichmentE2EController,
    EnrichmentRunResult,
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
    Resultado mínimo utilizado
    exclusivamente para testar
    a coordenação da Fase 7.3.
    """

    agent_id: str
    success: bool = True


class FakeSupervisedController:
    """
    Simula a camada supervisionada
    já validada na Fase 7.2.

    Não simula ferramentas externas.

    Sua responsabilidade aqui é apenas
    permitir testar o loop restrito de
    enriquecimento da Fase 7.3.
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
        Executa logicamente o primeiro
        agente pendente e atualiza o
        workflow como um especialista
        concluído.
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

        agent_id = (
            case_state
            .workflow
            .pending_agents[0]
        )

        self.calls.append(
            agent_id
        )

        case_state.workflow.pending_agents = [
            value
            for value
            in case_state.workflow.pending_agents
            if value != agent_id
        ]

        if (
            agent_id
            not in case_state
            .workflow
            .completed_agents
        ):
            case_state.workflow.completed_agents.append(
                agent_id
            )

        case_state.workflow.step_count += 1

        return SimpleNamespace(
            supervisor_result=(
                FakeExecutionResult(
                    agent_id="AG-01"
                )
            ),
            specialist_result=(
                FakeExecutionResult(
                    agent_id=agent_id
                )
            ),
            stopped=False,
        )


def create_case(
    *,
    case_status: CaseStatus = (
        CaseStatus.ENRICHING
    ),
) -> CaseState:
    """
    Cria um caso defensivo de
    laboratório para a Fase 7.3.
    """

    alert = Alert(
        alert_id="ALT-P7-3-0001",
        correlation_id=(
            "CORR-P7-3-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.3 Enrichment Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Evento defensivo simulado "
                "para enriquecimento."
            ),
            raw_event={
                "username": "lab.user",
                "source_ip": (
                    "203.0.113.10"
                ),
                "hostname": (
                    "LAB-WKS-001"
                ),
            },
        ),
        initial_severity=(
            Severity.HIGH
        ),
    )

    case = CaseState(
        case_id="CASE-P7-3-0001",
        correlation_id=(
            "CORR-P7-3-0001"
        ),
        alert=alert,
    )

    case.workflow.case_status = (
        case_status
    )

    case.workflow.completed_agents = [
        "AG-02",
        "AG-03",
    ]

    case.workflow.step_count = 2

    return case


def create_controller(
    case_state: CaseState,
) -> tuple[
    EnrichmentE2EController,
    FakeSupervisedController,
]:
    """
    Cria controller oficial da 7.3
    com a camada supervisionada
    substituída por uma fake somente
    para este teste unitário.
    """

    controller = (
        EnrichmentE2EController(
            SOCOrchestrator()
        )
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


def test_phase7_3_enrichment_catalog() -> None:
    """
    Catálogo da etapa deve conter
    somente AG-04 até AG-08.
    """

    assert ENRICHMENT_AGENT_IDS == (
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-07",
        "AG-08",
    )

    assert (
        "AG-03"
        not in ENRICHMENT_AGENT_IDS
    )

    assert (
        "AG-09"
        not in ENRICHMENT_AGENT_IDS
    )

    assert (
        "AG-12"
        not in ENRICHMENT_AGENT_IDS
    )


def test_phase7_3_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        EnrichmentE2EController(
            object()
        )


def test_phase7_3_filters_pending_enrichment_agents() -> None:
    """
    Somente AG-04..AG-08 devem
    aparecer na seleção.

    Ordem original deve ser mantida.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-04",
        "AG-06",
        "AG-08",
        "AG-09",
    ]

    controller = (
        EnrichmentE2EController()
    )

    result = (
        controller
        .pending_enrichment_agents(
            case
        )
    )

    assert result == (
        "AG-04",
        "AG-06",
        "AG-08",
    )


def test_phase7_3_terminal_case_is_blocked() -> None:
    """
    Caso final não pode entrar
    novamente no enriquecimento.
    """

    case = create_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = [
        "AG-04",
    ]

    controller = (
        EnrichmentE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="estado final",
    ):
        controller.run(
            case
        )


def test_phase7_3_requires_pending_enrichment() -> None:
    """
    Se somente AG-09 estiver
    pendente, a Fase 7.3 não
    pode executar nada.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-09",
    ]

    controller = (
        EnrichmentE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "não possui agentes "
            "de enriquecimento"
        ),
    ):
        controller.run(
            case
        )


def test_phase7_3_executes_enrichment_in_workflow_order() -> None:
    """
    Deve executar os enriquecimentos
    exatamente na ordem existente
    no WorkflowState.

    Ao chegar no AG-09, deve parar.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-09",
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
        EnrichmentRunResult,
    )

    assert (
        result.requested_agents
        == (
            "AG-04",
            "AG-05",
            "AG-06",
        )
    )

    assert (
        result.executed_agents
        == (
            "AG-04",
            "AG-05",
            "AG-06",
        )
    )

    assert (
        fake_supervised.calls
        == [
            "AG-04",
            "AG-05",
            "AG-06",
        ]
    )

    assert (
        result.execution_count
        == 3
    )

    assert (
        result.completed
        is True
    )

    assert (
        result.stopped_before_non_enrichment
        is True
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-09",
        ]
    )

    assert (
        case.workflow.step_count
        == 5
    )


def test_phase7_3_never_executes_non_enrichment_agent() -> None:
    """
    AG-09 deve permanecer intacto.

    A camada 7.3 nunca deve
    atravessar para investigação.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-04",
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

    assert (
        fake_supervised.calls
        == [
            "AG-04",
        ]
    )

    assert (
        result.executed_agents
        == (
            "AG-04",
        )
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-09",
            "AG-10",
        ]
    )

    assert (
        "AG-09"
        not in result.executed_agents
    )

    assert (
        "AG-10"
        not in result.executed_agents
    )


def test_phase7_3_result_is_immutable_and_summary_is_safe() -> None:
    """
    Resultado deve ser imutável
    e possuir summary operacional.
    """

    result = EnrichmentRunResult(
        case_id="CASE-P7-3-0001",
        correlation_id=(
            "CORR-P7-3-0001"
        ),
        requested_agents=(
            "AG-04",
            "AG-05",
        ),
        executed_agents=(
            "AG-04",
            "AG-05",
        ),
        supervisor_results=(),
        specialist_results=(),
        stopped_before_non_enrichment=(
            True
        ),
    )

    assert (
        result.execution_count
        == 2
    )

    assert (
        result.completed
        is True
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-3-0001"
            ),
            "correlation_id": (
                "CORR-P7-3-0001"
            ),
            "requested_agents": [
                "AG-04",
                "AG-05",
            ],
            "executed_agents": [
                "AG-04",
                "AG-05",
            ],
            "execution_count": 2,
            "completed": True,
            "stopped_before_non_enrichment": (
                True
            ),
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )