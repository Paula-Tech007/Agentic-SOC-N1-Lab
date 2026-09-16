"""
Execução supervisionada do Agentic SOC N1 Lab.

Fase 7.2 — Supervisor automático controlado.

Fluxo desta etapa:

    CaseState
        ↓
    AG-01 SOC Supervisor
        ↓
    decisão de roteamento
        ↓
    exatamente um especialista
        ↓
    CaseState atualizado

Este módulo NÃO implementa ainda
o loop E2E completo.

Responsabilidades:

- executar o AG-01 através do SOCOrchestrator;
- validar novamente sua decisão;
- preservar fail-closed;
- executar somente o especialista selecionado;
- nunca permitir AG-01 ou AG-02 como especialista;
- não executar ação crítica;
- não substituir Runtime;
- não substituir políticas existentes;
- preservar CaseState e correlation_id.

Princípio:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from core.orchestrator.contracts import (
    AgentExecutionResult,
)
from core.orchestrator.e2e import (
    E2EExecutionController,
    PHASE7_SPECIALIST_AGENT_IDS,
)
from core.orchestrator.orchestrator import (
    SOCOrchestrator,
)
from core.state import (
    CaseState,
)


def _required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Valida string obrigatória.
    """

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            f"{field_name} precisa ser string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise RuntimeError(
            f"{field_name} não pode ser vazio."
        )

    return cleaned


def _optional_agent_id(
    value: object,
) -> str | None:
    """
    Valida next_agent_id opcional.
    """

    if value is None:
        return None

    return _required_string(
        value,
        field_name="next_agent_id",
    )


@dataclass(
    frozen=True,
    slots=True,
)
class SupervisorRoutingDecision:
    """
    Decisão imutável produzida
    pelo AG-01.
    """

    case_id: str
    case_status: str
    next_agent_id: str | None
    should_continue: bool
    reason: str
    routing_source: str

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Representação segura
        para observabilidade.
        """

        return {
            "case_id": self.case_id,
            "case_status": (
                self.case_status
            ),
            "next_agent_id": (
                self.next_agent_id
            ),
            "should_continue": (
                self.should_continue
            ),
            "reason": self.reason,
            "routing_source": (
                self.routing_source
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class SupervisedStepResult:
    """
    Resultado de um ciclo supervisionado.

    specialist_result é None quando
    o Supervisor determina parada.
    """

    decision: SupervisorRoutingDecision

    supervisor_result: AgentExecutionResult

    specialist_result: (
        AgentExecutionResult | None
    )

    @property
    def stopped(
        self,
    ) -> bool:
        """
        Indica que o Supervisor
        encerrou o ciclo.
        """

        return (
            not self.decision.should_continue
        )

    @property
    def executed_agent_id(
        self,
    ) -> str | None:
        """
        Retorna o especialista
        efetivamente executado.
        """

        if self.specialist_result is None:
            return None

        return (
            self.specialist_result.agent_id
        )


class SupervisedE2EController:
    """
    Controlador da Fase 7.2.

    Executa:

        AG-01
          ↓
        decisão
          ↓
        um especialista

    O SOCOrchestrator continua
    responsável por:

    - AgentExecutionRequest;
    - Runtime;
    - validação dos resultados;
    - aplicação no CaseState;
    - WorkflowState;
    - retry_count;
    - step_count;
    - max_steps.
    """

    def __init__(
        self,
        orchestrator: SOCOrchestrator
        | None = None,
    ) -> None:
        """
        Inicializa o controlador
        supervisionado.
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

        self._e2e = (
            E2EExecutionController(
                self._orchestrator
            )
        )

    @property
    def orchestrator(
        self,
    ) -> SOCOrchestrator:
        """
        Retorna o orquestrador
        oficial utilizado.
        """

        return self._orchestrator

    @property
    def e2e(
        self,
    ) -> E2EExecutionController:
        """
        Retorna a camada E2E
        controlada da Fase 7.1.
        """

        return self._e2e

    def route(
        self,
        case_state: CaseState,
    ) -> tuple[
        SupervisorRoutingDecision,
        AgentExecutionResult,
    ]:
        """
        Executa somente o AG-01
        e devolve sua decisão validada.

        Nenhum especialista é executado
        por este método.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        result = (
            self._orchestrator
            .execute_agent(
                case_state=case_state,
                agent_id="AG-01",
            )
        )

        if not result.success:
            raise RuntimeError(
                "AG-01 Supervisor falhou: "
                f"{result.error or 'erro não informado'}"
            )

        decision = (
            self._parse_supervisor_result(
                case_state=case_state,
                result=result,
            )
        )

        return (
            decision,
            result,
        )

    def execute_supervised_step(
        self,
        case_state: CaseState,
        input_payload: Mapping[
            str,
            Any,
        ]
        | None = None,
    ) -> SupervisedStepResult:
        """
        Executa um ciclo controlado:

        1. AG-01 analisa o workflow;
        2. decisão é validada;
        3. se deve parar, encerra;
        4. caso contrário executa
           exatamente um especialista.

        Não existe loop automático
        nesta etapa.
        """

        decision, supervisor_result = (
            self.route(
                case_state
            )
        )

        if not decision.should_continue:
            return SupervisedStepResult(
                decision=decision,
                supervisor_result=(
                    supervisor_result
                ),
                specialist_result=None,
            )

        selected_agent = (
            decision.next_agent_id
        )

        if selected_agent is None:
            raise RuntimeError(
                "Supervisor solicitou "
                "continuidade sem agente."
            )

        snapshot = self._e2e.snapshot(
            case_state
        )

        if (
            snapshot.next_pending_agent
            != selected_agent
        ):
            raise RuntimeError(
                "Workflow não preservou "
                "o agente escolhido pelo "
                "Supervisor."
            )

        specialist_result = (
            self._e2e
            .execute_next_pending(
                case_state=case_state,
                input_payload=input_payload,
            )
        )

        if (
            specialist_result.agent_id
            != selected_agent
        ):
            raise RuntimeError(
                "Especialista executado "
                "não corresponde ao agente "
                "selecionado pelo Supervisor."
            )

        return SupervisedStepResult(
            decision=decision,
            supervisor_result=(
                supervisor_result
            ),
            specialist_result=(
                specialist_result
            ),
        )

    def _parse_supervisor_result(
        self,
        *,
        case_state: CaseState,
        result: AgentExecutionResult,
    ) -> SupervisorRoutingDecision:
        """
        Faz uma segunda validação defensiva
        sobre supervisor_result.

        O SOCOrchestrator já valida a saída
        do AG-01 antes deste ponto.

        Esta camada mantém fail-closed
        também na fronteira E2E.
        """

        output = result.output

        if not isinstance(
            output,
            Mapping,
        ):
            raise RuntimeError(
                "Resultado do Supervisor "
                "não possui output válido."
            )

        raw_decision = output.get(
            "supervisor_result"
        )

        if not isinstance(
            raw_decision,
            Mapping,
        ):
            raise RuntimeError(
                "Resultado do Supervisor "
                "não possui supervisor_result."
            )

        case_id = _required_string(
            raw_decision.get(
                "case_id"
            ),
            field_name="case_id",
        )

        if case_id != case_state.case_id:
            raise RuntimeError(
                "case_id retornado pelo "
                "Supervisor não corresponde "
                "ao CaseState."
            )

        case_status = _required_string(
            raw_decision.get(
                "case_status"
            ),
            field_name="case_status",
        )

        should_continue = (
            raw_decision.get(
                "should_continue"
            )
        )

        if not isinstance(
            should_continue,
            bool,
        ):
            raise RuntimeError(
                "should_continue precisa "
                "ser booleano."
            )

        next_agent_id = (
            _optional_agent_id(
                raw_decision.get(
                    "next_agent_id"
                )
            )
        )

        reason = _required_string(
            raw_decision.get(
                "reason"
            ),
            field_name="reason",
        )

        routing_source = (
            _required_string(
                raw_decision.get(
                    "routing_source"
                ),
                field_name=(
                    "routing_source"
                ),
            )
        )

        if should_continue:
            if next_agent_id is None:
                raise RuntimeError(
                    "Supervisor solicitou "
                    "continuidade sem "
                    "next_agent_id."
                )

            if (
                next_agent_id
                not in PHASE7_SPECIALIST_AGENT_IDS
            ):
                raise RuntimeError(
                    "Supervisor selecionou "
                    "agente não autorizado: "
                    f"{next_agent_id}."
                )

        else:
            if next_agent_id is not None:
                raise RuntimeError(
                    "Supervisor solicitou "
                    "parada mas também "
                    "selecionou um agente."
                )

        return SupervisorRoutingDecision(
            case_id=case_id,
            case_status=case_status,
            next_agent_id=next_agent_id,
            should_continue=(
                should_continue
            ),
            reason=reason,
            routing_source=(
                routing_source
            ),
        )


__all__ = [
    "SupervisedE2EController",
    "SupervisedStepResult",
    "SupervisorRoutingDecision",
]