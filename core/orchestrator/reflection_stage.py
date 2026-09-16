"""
Orquestração de Reflection/QA
do Agentic SOC N1 Lab.

Fase 7.5 — Reflection/QA + retry controlado.

Fluxo:

    AG-09 concluído
        ↓
    AG-01 Supervisor
        ↓
    AG-10 Reflection/QA
        ↓
    QAResult
        ↓
    ┌─────────────────────────┐
    │ retry_required = False  │
    │ seguir workflow         │
    └─────────────────────────┘

        ou

    ┌─────────────────────────┐
    │ retry_required = True   │
    │ validar retry_targets   │
    │ confirmar reentrada     │
    │ no WorkflowState        │
    └─────────────────────────┘

Esta camada NÃO inventa retry.

O AG-10 produz a decisão de QA e o
SOCOrchestrator continua responsável
por aplicar essa decisão ao workflow.

A Fase 7.5 apenas:

- executa AG-10 pelo Supervisor;
- valida o resultado aplicado;
- confirma retry_targets;
- impede retry para agentes proibidos;
- impede loop sobre AG-01/AG-02/AG-10;
- preserva limites de workflow;
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


REFLECTION_AGENT_ID = "AG-10"


RETRYABLE_AGENT_IDS: tuple[str, ...] = (
    "AG-03",
    "AG-04",
    "AG-05",
    "AG-06",
    "AG-07",
    "AG-08",
    "AG-09",
)


def _enum_text(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Converte enum/string em texto
    obrigatório e normalizado.
    """

    raw_value = getattr(
        value,
        "value",
        value,
    )

    if not isinstance(
        raw_value,
        str,
    ):
        raise RuntimeError(
            f"{field_name} precisa possuir "
            "representação textual válida."
        )

    normalized = raw_value.strip()

    if not normalized:
        raise RuntimeError(
            f"{field_name} não pode ser vazio."
        )

    return normalized


def _retry_targets(
    value: object,
) -> tuple[str, ...]:
    """
    Valida coleção de retry_targets.

    Repetição ou agent_id proibido
    falha fechado.
    """

    if not isinstance(
        value,
        (list, tuple),
    ):
        raise RuntimeError(
            "qa.retry_targets precisa ser "
            "lista ou tupla."
        )

    normalized: list[str] = []

    for item in value:
        if not isinstance(
            item,
            str,
        ):
            raise RuntimeError(
                "qa.retry_targets contém "
                "agent_id inválido."
            )

        agent_id = item.strip()

        if not agent_id:
            raise RuntimeError(
                "qa.retry_targets contém "
                "agent_id vazio."
            )

        if (
            agent_id
            not in RETRYABLE_AGENT_IDS
        ):
            raise RuntimeError(
                "QA solicitou retry para "
                "agente não autorizado: "
                f"{agent_id}."
            )

        if agent_id in normalized:
            raise RuntimeError(
                "qa.retry_targets contém "
                "agent_id duplicado: "
                f"{agent_id}."
            )

        normalized.append(
            agent_id
        )

    return tuple(
        normalized
    )


@dataclass(
    frozen=True,
    slots=True,
)
class ReflectionStageResult:
    """
    Resultado imutável da etapa AG-10.
    """

    case_id: str
    correlation_id: str

    qa_status: str

    retry_required: bool
    retry_targets: tuple[str, ...]

    supervisor_result: AgentExecutionResult
    reflection_result: AgentExecutionResult

    next_pending_agent: str | None

    @property
    def executed_agent_id(
        self,
    ) -> str:
        """
        Agente executado nesta etapa.
        """

        return (
            self.reflection_result.agent_id
        )

    @property
    def completed(
        self,
    ) -> bool:
        """
        Indica conclusão técnica válida
        da execução do AG-10.
        """

        return (
            self.reflection_result.success
            and self.reflection_result.agent_id
            == REFLECTION_AGENT_ID
        )

    @property
    def has_retry(
        self,
    ) -> bool:
        """
        Indica existência de retry
        formal solicitado pelo QA.
        """

        return (
            self.retry_required
            and bool(
                self.retry_targets
            )
        )

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo operacional seguro.
        """

        return {
            "case_id": self.case_id,
            "correlation_id": (
                self.correlation_id
            ),
            "qa_status": self.qa_status,
            "retry_required": (
                self.retry_required
            ),
            "retry_targets": list(
                self.retry_targets
            ),
            "executed_agent_id": (
                self.executed_agent_id
            ),
            "completed": self.completed,
            "has_retry": self.has_retry,
            "next_pending_agent": (
                self.next_pending_agent
            ),
        }


class ReflectionE2EController:
    """
    Controlador da Fase 7.5.

    Executa exatamente:

        AG-01 Supervisor
             ↓
        AG-10 Reflection/QA

    Após AG-10, valida a decisão
    de retry já aplicada pelo
    SOCOrchestrator ao WorkflowState.
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
        Retorna True somente quando
        AG-10 é o próximo agente.
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
            == REFLECTION_AGENT_ID
        )

    def run(
        self,
        case_state: CaseState,
    ) -> ReflectionStageResult:
        """
        Executa AG-10 e valida
        Reflection/QA + retry.

        Não executa os retry_targets.

        Isso será coordenado posteriormente
        pelo loop E2E usando Supervisor.

        Nesta etapa verificamos apenas
        que a decisão de retry foi aplicada
        corretamente ao WorkflowState.
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
            != REFLECTION_AGENT_ID
        ):
            raise RuntimeError(
                "AG-10 Reflection/QA "
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
                "a execução antes do AG-10."
            )

        if (
            step.decision.next_agent_id
            != REFLECTION_AGENT_ID
        ):
            raise RuntimeError(
                "Supervisor não selecionou "
                "AG-10 Reflection/QA."
            )

        reflection_result = (
            step.specialist_result
        )

        if reflection_result is None:
            raise RuntimeError(
                "Execução do AG-10 não "
                "produziu resultado."
            )

        if (
            reflection_result.agent_id
            != REFLECTION_AGENT_ID
        ):
            raise RuntimeError(
                "Especialista executado não "
                "corresponde ao AG-10."
            )

        if not reflection_result.success:
            raise RuntimeError(
                "AG-10 Reflection/QA "
                "não concluiu com sucesso."
            )

        qa = getattr(
            case_state,
            "qa",
            None,
        )

        if qa is None:
            raise RuntimeError(
                "AG-10 concluiu sem QAResult "
                "registrado no CaseState."
            )

        qa_status = _enum_text(
            getattr(
                qa,
                "status",
                None,
            ),
            field_name="qa.status",
        )

        retry_required = getattr(
            qa,
            "retry_required",
            None,
        )

        if not isinstance(
            retry_required,
            bool,
        ):
            raise RuntimeError(
                "qa.retry_required precisa "
                "ser booleano."
            )

        retry_targets = _retry_targets(
            getattr(
                qa,
                "retry_targets",
                None,
            )
        )

        if (
            retry_required
            and not retry_targets
        ):
            raise RuntimeError(
                "QA solicitou retry sem "
                "retry_targets."
            )

        if (
            not retry_required
            and retry_targets
        ):
            raise RuntimeError(
                "QA possui retry_targets "
                "sem retry_required."
            )

        after = self._e2e.snapshot(
            case_state
        )

        if (
            REFLECTION_AGENT_ID
            in after.pending_agents
        ):
            raise RuntimeError(
                "AG-10 permaneceu pendente "
                "após sua execução."
            )

        if retry_required:
            for target in retry_targets:
                if (
                    target
                    not in after.pending_agents
                ):
                    raise RuntimeError(
                        "Retry target não foi "
                        "recolocado no workflow: "
                        f"{target}."
                    )

        return ReflectionStageResult(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            qa_status=qa_status,
            retry_required=(
                retry_required
            ),
            retry_targets=(
                retry_targets
            ),
            supervisor_result=(
                step.supervisor_result
            ),
            reflection_result=(
                reflection_result
            ),
            next_pending_agent=(
                after.next_pending_agent
            ),
        )


__all__ = [
    "REFLECTION_AGENT_ID",
    "RETRYABLE_AGENT_IDS",
    "ReflectionE2EController",
    "ReflectionStageResult",
]