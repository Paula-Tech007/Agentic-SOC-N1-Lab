"""
Runtime oficial de execução dos agentes
do Agentic SOC N1 Lab.

O Runtime conecta:

AgentExecutionRequest
        ↓
AgentRegistry
        ↓
BaseAgent
        ↓
AgentExecutionResult

Responsabilidades:

- localizar o agente solicitado;
- impedir execução de agente indisponível;
- executar o agente registrado;
- manter comportamento fail-closed;
- devolver sempre um AgentExecutionResult;
- não alterar diretamente o CaseState.

O Runtime não decide qual agente deve executar.

Essa decisão pertence ao Supervisor / Orchestrator.
"""

from datetime import datetime, timezone
from time import perf_counter

from core.orchestrator.contracts import (
    AgentExecutionRequest,
    AgentExecutionResult,
)
from core.orchestrator.registry import (
    AgentRegistry,
    agent_registry,
)
from core.schemas import AgentStatus


class AgentRuntime:
    """
    Executor central dos agentes registrados.
    """

    def __init__(
        self,
        registry: AgentRegistry | None = None,
    ) -> None:
        """
        Permite utilizar um Registry específico em testes
        ou o Registry global oficial da aplicação.
        """

        self.registry = (
            registry
            if registry is not None
            else agent_registry
        )

    def execute(
        self,
        request: AgentExecutionRequest,
    ) -> AgentExecutionResult:
        """
        Localiza e executa o agente solicitado.

        Qualquer falha anterior à execução do agente
        resulta em FAILED, seguindo fail-closed.
        """

        started_at = datetime.now(timezone.utc)
        start_timer = perf_counter()

        try:
            agent = self.registry.get(
                request.agent_id
            )

        except (KeyError, ValueError, TypeError) as exc:
            return self._failure_result(
                request=request,
                error=(
                    "Runtime recusou a execução: "
                    f"{exc}"
                ),
                started_at=started_at,
                start_timer=start_timer,
            )

        try:
            return agent.execute(request)

        except Exception as exc:
            return self._failure_result(
                request=request,
                error=(
                    "Falha inesperada no Runtime: "
                    f"{type(exc).__name__}: {exc}"
                ),
                started_at=started_at,
                start_timer=start_timer,
            )

    def can_execute(
        self,
        agent_id: str,
    ) -> bool:
        """
        Informa se o agente está registrado e disponível.
        """

        return self.registry.contains(agent_id)

    def _failure_result(
        self,
        request: AgentExecutionRequest,
        error: str,
        started_at: datetime,
        start_timer: float,
    ) -> AgentExecutionResult:
        """
        Gera resposta padronizada de falha.
        """

        completed_at = datetime.now(timezone.utc)

        duration_ms = (
            perf_counter() - start_timer
        ) * 1000

        return AgentExecutionResult(
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            status=AgentStatus.FAILED,
            success=False,
            output={},
            evidence_references=(),
            messages=(),
            error=error,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )


agent_runtime = AgentRuntime()