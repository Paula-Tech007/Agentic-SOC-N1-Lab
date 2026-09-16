"""
Camada E2E controlada do Agentic SOC N1 Lab.

Fase 7.1 — Fundação de execução ponta a ponta.

Este módulo NÃO substitui o SOCOrchestrator.

Responsabilidades:

- reutilizar SOCOrchestrator.bootstrap_case();
- reutilizar SOCOrchestrator.execute_agent();
- representar um snapshot seguro do workflow;
- identificar o próximo especialista pendente;
- executar somente um passo controlado por vez;
- preservar CaseState;
- preservar correlation_id;
- preservar limites do WorkflowState;
- falhar fechado para estados inesperados.

Nesta etapa:

- AG-01 Supervisor NÃO é disparado automaticamente;
- AG-02 continua exclusivo do bootstrap;
- não existe loop E2E automático;
- não existe contenção automática;
- não existem ações críticas;
- não existe bypass do Runtime;
- não existe bypass de permissões.

A automação do Supervisor pertence à Fase 7.2.

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
from core.orchestrator.orchestrator import (
    SOCOrchestrator,
)
from core.state import (
    CaseState,
)


PHASE7_SPECIALIST_AGENT_IDS: tuple[str, ...] = (
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


TERMINAL_CASE_STATUSES: frozenset[str] = frozenset(
    {
        "CLOSED_N1",
        "ESCALATED_N2",
        "WAITING_HUMAN",
    }
)


def _enum_value(
    value: object,
) -> str:
    """
    Converte enum ou string para
    representação textual segura.

    Valores inesperados falham fechado.
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
            "Valor de estado do workflow "
            "não possui representação textual válida."
        )

    normalized = raw_value.strip()

    if not normalized:
        raise RuntimeError(
            "Valor de estado do workflow "
            "não pode ser vazio."
        )

    return normalized


def _required_agent_id(
    value: object,
) -> str:
    """
    Valida identificador de agente
    recebido do WorkflowState.
    """

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            "agent_id pendente precisa ser string."
        )

    normalized = value.strip()

    if not normalized:
        raise RuntimeError(
            "agent_id pendente não pode ser vazio."
        )

    return normalized


def _agent_tuple(
    values: object,
    *,
    field_name: str,
) -> tuple[str, ...]:
    """
    Converte coleção de agent_ids
    do workflow para tupla imutável.

    A conversão é fail-closed.
    """

    if not isinstance(
        values,
        (list, tuple),
    ):
        raise RuntimeError(
            f"{field_name} precisa ser "
            "uma lista ou tupla."
        )

    normalized: list[str] = []

    for value in values:
        agent_id = _required_agent_id(
            value
        )

        if agent_id in normalized:
            raise RuntimeError(
                f"{field_name} contém agent_id "
                f"duplicado: {agent_id}."
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
class E2EWorkflowSnapshot:
    """
    Snapshot imutável do estado operacional
    necessário pela camada E2E.

    O snapshot não altera o CaseState.
    """

    case_id: str
    correlation_id: str
    case_status: str

    step_count: int
    max_steps: int

    current_agent: str | None

    pending_agents: tuple[str, ...]
    completed_agents: tuple[str, ...]
    failed_agents: tuple[str, ...]
    skipped_agents: tuple[str, ...]

    @property
    def terminal(
        self,
    ) -> bool:
        """
        Indica se o caso atingiu
        um estado final.
        """

        return (
            self.case_status
            in TERMINAL_CASE_STATUSES
        )

    @property
    def next_pending_agent(
        self,
    ) -> str | None:
        """
        Retorna o primeiro agente
        atualmente pendente.
        """

        if not self.pending_agents:
            return None

        return self.pending_agents[0]

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo seguro para testes,
        logging e observabilidade.
        """

        return {
            "case_id": self.case_id,
            "correlation_id": (
                self.correlation_id
            ),
            "case_status": (
                self.case_status
            ),
            "step_count": (
                self.step_count
            ),
            "max_steps": (
                self.max_steps
            ),
            "current_agent": (
                self.current_agent
            ),
            "pending_agents": list(
                self.pending_agents
            ),
            "completed_agents": list(
                self.completed_agents
            ),
            "failed_agents": list(
                self.failed_agents
            ),
            "skipped_agents": list(
                self.skipped_agents
            ),
            "terminal": self.terminal,
        }


class E2EExecutionController:
    """
    Controlador E2E da Fase 7.1.

    Ele trabalha acima do SOCOrchestrator.

    Não executa agentes diretamente.

    Toda execução continua passando por:

        E2EExecutionController
            ↓
        SOCOrchestrator
            ↓
        AgentRuntime
            ↓
        BaseAgent

    Portanto, os guardrails já existentes
    permanecem soberanos.
    """

    def __init__(
        self,
        orchestrator: SOCOrchestrator
        | None = None,
    ) -> None:
        """
        Permite injetar um SOCOrchestrator
        específico para testes.

        Sem injeção, utiliza a configuração
        oficial do projeto.
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

    @property
    def orchestrator(
        self,
    ) -> SOCOrchestrator:
        """
        Retorna o SOCOrchestrator
        associado ao controlador.
        """

        return self._orchestrator

    def bootstrap(
        self,
        raw_alert: Mapping[str, Any],
        *,
        case_id: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[
        CaseState | None,
        AgentExecutionResult,
    ]:
        """
        Inicia um caso através do AG-02.

        Nenhum CaseState paralelo é criado.

        A criação continua totalmente
        delegada ao SOCOrchestrator oficial.
        """

        if not isinstance(
            raw_alert,
            Mapping,
        ):
            raise TypeError(
                "raw_alert precisa ser "
                "um Mapping."
            )

        return (
            self._orchestrator
            .bootstrap_case(
                raw_alert=raw_alert,
                case_id=case_id,
                correlation_id=(
                    correlation_id
                ),
            )
        )

    def snapshot(
        self,
        case_state: CaseState,
    ) -> E2EWorkflowSnapshot:
        """
        Obtém uma visão imutável
        do workflow atual.

        Nenhum estado é modificado.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        workflow = case_state.workflow

        step_count = (
            workflow.step_count
        )

        max_steps = (
            workflow.max_steps
        )

        if (
            isinstance(
                step_count,
                bool,
            )
            or not isinstance(
                step_count,
                int,
            )
            or step_count < 0
        ):
            raise RuntimeError(
                "workflow.step_count inválido."
            )

        if (
            isinstance(
                max_steps,
                bool,
            )
            or not isinstance(
                max_steps,
                int,
            )
            or max_steps < 1
        ):
            raise RuntimeError(
                "workflow.max_steps inválido."
            )

        current_agent = (
            workflow.current_agent
        )

        if current_agent is not None:
            current_agent = (
                _required_agent_id(
                    current_agent
                )
            )

        return E2EWorkflowSnapshot(
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            case_status=_enum_value(
                workflow.case_status
            ),
            step_count=step_count,
            max_steps=max_steps,
            current_agent=current_agent,
            pending_agents=_agent_tuple(
                workflow.pending_agents,
                field_name=(
                    "workflow.pending_agents"
                ),
            ),
            completed_agents=_agent_tuple(
                workflow.completed_agents,
                field_name=(
                    "workflow.completed_agents"
                ),
            ),
            failed_agents=_agent_tuple(
                workflow.failed_agents,
                field_name=(
                    "workflow.failed_agents"
                ),
            ),
            skipped_agents=_agent_tuple(
                workflow.skipped_agents,
                field_name=(
                    "workflow.skipped_agents"
                ),
            ),
        )

    def is_terminal(
        self,
        case_state: CaseState,
    ) -> bool:
        """
        Informa se o caso já atingiu
        um estado final.
        """

        return self.snapshot(
            case_state
        ).terminal

    def next_pending_agent(
        self,
        case_state: CaseState,
    ) -> str | None:
        """
        Retorna o primeiro agente pendente.

        Nesta Fase 7.1 isso é somente
        observação de estado.

        O Supervisor automático será
        introduzido na Fase 7.2.
        """

        return self.snapshot(
            case_state
        ).next_pending_agent

    def execute_next_pending(
        self,
        case_state: CaseState,
        input_payload: Mapping[
            str,
            Any,
        ]
        | None = None,
    ) -> AgentExecutionResult:
        """
        Executa exatamente um especialista
        pendente através do SOCOrchestrator.

        Regras:

        - caso final não pode continuar;
        - precisa existir agente pendente;
        - AG-01 não é executado aqui;
        - AG-02 não é executado novamente;
        - somente AG-03..AG-12 são aceitos;
        - Runtime e políticas existentes
          continuam responsáveis pela execução.

        Não existe loop automático nesta etapa.
        """

        snapshot = self.snapshot(
            case_state
        )

        if snapshot.terminal:
            raise RuntimeError(
                "Caso já está em estado final: "
                f"{snapshot.case_status}."
            )

        next_agent_id = (
            snapshot.next_pending_agent
        )

        if next_agent_id is None:
            raise RuntimeError(
                "Workflow não possui "
                "agente pendente."
            )

        if next_agent_id == "AG-01":
            raise RuntimeError(
                "AG-01 Supervisor não pode "
                "ser disparado automaticamente "
                "pela Fase 7.1."
            )

        if next_agent_id == "AG-02":
            raise RuntimeError(
                "AG-02 Alert Intake é exclusivo "
                "do bootstrap."
            )

        if (
            next_agent_id
            not in PHASE7_SPECIALIST_AGENT_IDS
        ):
            raise RuntimeError(
                "Workflow contém agente "
                "não autorizado para a "
                "execução E2E controlada: "
                f"{next_agent_id}."
            )

        payload: Mapping[str, Any] | None

        if input_payload is None:
            payload = None

        else:
            if not isinstance(
                input_payload,
                Mapping,
            ):
                raise TypeError(
                    "input_payload precisa ser "
                    "Mapping ou None."
                )

            payload = dict(
                input_payload
            )

        return (
            self._orchestrator
            .execute_agent(
                case_state=case_state,
                agent_id=next_agent_id,
                input_payload=payload,
            )
        )


__all__ = [
    "E2EExecutionController",
    "E2EWorkflowSnapshot",
    "PHASE7_SPECIALIST_AGENT_IDS",
    "TERMINAL_CASE_STATUSES",
]