"""
Testes formais da Fase 7.5.

Valida:

- AG-10 Reflection/QA;
- execução via Supervisor;
- retry_required;
- retry_targets;
- bloqueio de retry proibido;
- confirmação de reentrada no workflow;
- parada antes de AG-11;
- fail-closed;
- imutabilidade do resultado.

Importante:

CaseState é um modelo Pydantic e seu
campo qa aceita QAResult real.

Por isso estes testes utilizam o schema
QAResult do próprio projeto em vez de
objetos fake incompatíveis.
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

from core.orchestrator.reflection_stage import (
    REFLECTION_AGENT_ID,
    RETRYABLE_AGENT_IDS,
    ReflectionE2EController,
    ReflectionStageResult,
)

from core.schemas import (
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    CaseStatus,
    QAResult,
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
    Resultado mínimo de execução
    utilizado somente para testar
    a coordenação da Fase 7.5.
    """

    agent_id: str
    success: bool = True


def create_qa_result(
    *,
    retry_required: bool,
    retry_targets: tuple[
        str,
        ...,
    ],
) -> QAResult:
    """
    Cria uma instância do schema
    QAResult oficial do projeto.

    model_construct é usado porque
    este teste valida somente a camada
    de orquestração da Fase 7.5.

    Os testes próprios do schema e do
    AG-10 já validam a construção
    completa do QAResult.
    """

    return QAResult.model_construct(
        qa_id="QA-P7-5-0001",
        case_id="CASE-P7-5-0001",
        status=(
            "REJECTED"
            if retry_required
            else "APPROVED"
        ),
        confidence=95,
        severity="HIGH",
        summary=(
            "QA defensivo simulado "
            "para teste da Fase 7.5."
        ),
        issues=(
            [
                "Evidência adicional necessária."
            ]
            if retry_required
            else []
        ),
        missing_evidence=(
            [
                "Validação adicional."
            ]
            if retry_required
            else []
        ),
        retry_required=(
            retry_required
        ),
        retry_targets=list(
            retry_targets
        ),
    )


class FakeSupervisedController:
    """
    Simula Supervisor + AG-10.

    Também simula a aplicação do
    retry ao WorkflowState.

    Não substitui testes do AG-10
    nem do SOCOrchestrator.

    Serve apenas para isolar a lógica
    da camada Fase 7.5.
    """

    def __init__(
        self,
        case_state: CaseState,
        *,
        retry_required: bool = False,
        retry_targets: tuple[
            str,
            ...,
        ] = (),
    ) -> None:
        self._case_state = (
            case_state
        )

        self._retry_required = (
            retry_required
        )

        self._retry_targets = (
            retry_targets
        )

        self.calls: list[str] = []

    def execute_supervised_step(
        self,
        case_state: CaseState,
    ):
        """
        Simula execução exclusiva
        do AG-10.
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
            == REFLECTION_AGENT_ID
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

        if self._retry_required:
            for target in reversed(
                self._retry_targets
            ):
                if (
                    target
                    not in case_state
                    .workflow
                    .pending_agents
                ):
                    case_state.workflow.pending_agents.insert(
                        0,
                        target,
                    )

        case_state.qa = create_qa_result(
            retry_required=(
                self._retry_required
            ),
            retry_targets=(
                self._retry_targets
            ),
        )

        return SimpleNamespace(
            decision=SimpleNamespace(
                next_agent_id=(
                    REFLECTION_AGENT_ID
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
                        REFLECTION_AGENT_ID
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
    Cria caso defensivo da 7.5.
    """

    alert = Alert(
        alert_id="ALT-P7-5-0001",
        correlation_id=(
            "CORR-P7-5-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Phase 7.5 QA Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category="authentication",
            message=(
                "Investigação simulada "
                "aguardando QA."
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
        case_id="CASE-P7-5-0001",
        correlation_id=(
            "CORR-P7-5-0001"
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
    ]

    case.workflow.step_count = 7

    return case


def create_controller(
    case_state: CaseState,
    *,
    retry_required: bool = False,
    retry_targets: tuple[
        str,
        ...,
    ] = (),
) -> tuple[
    ReflectionE2EController,
    FakeSupervisedController,
]:
    """
    Controller da 7.5 com camada
    supervisionada fake.
    """

    controller = (
        ReflectionE2EController(
            SOCOrchestrator()
        )
    )

    fake = FakeSupervisedController(
        case_state,
        retry_required=retry_required,
        retry_targets=retry_targets,
    )

    controller._supervised = fake

    return (
        controller,
        fake,
    )


def test_phase7_5_agent_catalog() -> None:
    """
    AG-10 é exclusivo da etapa e
    retries são limitados a AG-03..09.
    """

    assert (
        REFLECTION_AGENT_ID
        == "AG-10"
    )

    assert RETRYABLE_AGENT_IDS == (
        "AG-03",
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-07",
        "AG-08",
        "AG-09",
    )

    assert (
        "AG-01"
        not in RETRYABLE_AGENT_IDS
    )

    assert (
        "AG-02"
        not in RETRYABLE_AGENT_IDS
    )

    assert (
        "AG-10"
        not in RETRYABLE_AGENT_IDS
    )

    assert (
        "AG-11"
        not in RETRYABLE_AGENT_IDS
    )

    assert (
        "AG-12"
        not in RETRYABLE_AGENT_IDS
    )


def test_phase7_5_rejects_invalid_orchestrator() -> None:
    """
    Controller aceita somente
    SOCOrchestrator.
    """

    with pytest.raises(
        TypeError,
        match="SOCOrchestrator",
    ):
        ReflectionE2EController(
            object()
        )


def test_phase7_5_ready_only_for_ag10() -> None:
    """
    ready() só aceita AG-10
    como primeiro pendente.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-10",
        "AG-11",
    ]

    controller = (
        ReflectionE2EController()
    )

    assert (
        controller.ready(
            case
        )
        is True
    )

    case.workflow.pending_agents = [
        "AG-11",
    ]

    assert (
        controller.ready(
            case
        )
        is False
    )


def test_phase7_5_blocks_terminal_case() -> None:
    """
    Caso final não entra em QA.
    """

    case = create_case(
        case_status=(
            CaseStatus.CLOSED_N1
        )
    )

    case.workflow.pending_agents = [
        "AG-10",
    ]

    controller = (
        ReflectionE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="estado final",
    ):
        controller.run(
            case
        )


def test_phase7_5_requires_ag10_as_next_agent() -> None:
    """
    Etapa não pode saltar AG-10.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-11",
    ]

    controller = (
        ReflectionE2EController()
    )

    with pytest.raises(
        RuntimeError,
        match="não é o próximo agente",
    ):
        controller.run(
            case
        )


def test_phase7_5_approved_qa_continues_to_ag11() -> None:
    """
    QA aprovado não deve criar retry.

    AG-11 permanece como próximo.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-10",
        "AG-11",
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
        "AG-10",
    ]

    assert isinstance(
        result,
        ReflectionStageResult,
    )

    assert (
        result.qa_status
        == "APPROVED"
    )

    assert (
        result.retry_required
        is False
    )

    assert (
        result.retry_targets
        == ()
    )

    assert (
        result.has_retry
        is False
    )

    assert (
        result.next_pending_agent
        == "AG-11"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-11",
        ]
    )

    assert (
        "AG-10"
        in case
        .workflow
        .completed_agents
    )

    assert (
        "AG-11"
        not in case
        .workflow
        .completed_agents
    )

    assert (
        case.workflow.step_count
        == 8
    )


def test_phase7_5_rejected_qa_requeues_target() -> None:
    """
    QA rejeitado deve preservar
    retry target no workflow.

    Cenário:
    AG-05 precisa ser repetido.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-10",
        "AG-11",
    ]

    (
        controller,
        fake,
    ) = create_controller(
        case,
        retry_required=True,
        retry_targets=(
            "AG-05",
        ),
    )

    result = controller.run(
        case
    )

    assert fake.calls == [
        "AG-10",
    ]

    assert (
        result.qa_status
        == "REJECTED"
    )

    assert (
        result.retry_required
        is True
    )

    assert (
        result.retry_targets
        == (
            "AG-05",
        )
    )

    assert (
        result.has_retry
        is True
    )

    assert (
        result.next_pending_agent
        == "AG-05"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-05",
            "AG-11",
        ]
    )

    assert (
        "AG-11"
        not in case
        .workflow
        .completed_agents
    )

    assert (
        case.workflow.step_count
        == 8
    )


def test_phase7_5_retry_never_executes_target_here() -> None:
    """
    A 7.5 somente prepara e valida
    o retry.

    O alvo será executado depois
    pelo Supervisor no loop E2E.
    """

    case = create_case()

    case.workflow.pending_agents = [
        "AG-10",
        "AG-11",
    ]

    (
        controller,
        fake,
    ) = create_controller(
        case,
        retry_required=True,
        retry_targets=(
            "AG-09",
        ),
    )

    result = controller.run(
        case
    )

    assert fake.calls == [
        "AG-10",
    ]

    assert (
        result.next_pending_agent
        == "AG-09"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-09",
            "AG-11",
        ]
    )

    assert (
        "AG-09"
        in case
        .workflow
        .pending_agents
    )


def test_phase7_5_result_is_immutable_and_safe() -> None:
    """
    Resultado deve ser imutável
    e possuir resumo seguro.
    """

    supervisor_result = (
        FakeExecutionResult(
            agent_id="AG-01"
        )
    )

    reflection_result = (
        FakeExecutionResult(
            agent_id="AG-10"
        )
    )

    result = ReflectionStageResult(
        case_id="CASE-P7-5-0001",
        correlation_id=(
            "CORR-P7-5-0001"
        ),
        qa_status="REJECTED",
        retry_required=True,
        retry_targets=(
            "AG-05",
        ),
        supervisor_result=(
            supervisor_result
        ),
        reflection_result=(
            reflection_result
        ),
        next_pending_agent="AG-05",
    )

    assert (
        result.safe_summary()
        == {
            "case_id": (
                "CASE-P7-5-0001"
            ),
            "correlation_id": (
                "CORR-P7-5-0001"
            ),
            "qa_status": (
                "REJECTED"
            ),
            "retry_required": True,
            "retry_targets": [
                "AG-05",
            ],
            "executed_agent_id": (
                "AG-10"
            ),
            "completed": True,
            "has_retry": True,
            "next_pending_agent": (
                "AG-05"
            ),
        }
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        result.case_id = (
            "CASE-ALTERADO"
        )