"""
Classe-base oficial dos agentes do Agentic SOC N1 Lab.

Todos os agentes especializados devem herdar de BaseAgent.

A classe-base é responsável por padronizar:

- validação da solicitação;
- identificação do agente;
- controle de max_steps;
- controle de retries;
- execução fail-closed;
- tratamento de exceções;
- medição de duração;
- construção do AgentExecutionResult.

O agente especializado implementa somente sua lógica
de trabalho por meio do método run().
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from core.orchestrator.contracts import (
    AgentExecutionRequest,
    AgentExecutionResult,
)
from core.schemas import AgentStatus
from core.schemas.immutable import FrozenDict


class AgentWorkResult(BaseModel):
    """
    Resultado interno produzido pela lógica especializada
    de um agente.

    BaseAgent transforma este objeto no contrato oficial
    AgentExecutionResult.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    status: AgentStatus = Field(
        default=AgentStatus.COMPLETED,
        description="Estado final do trabalho do agente.",
    )

    success: bool = Field(
        default=True,
        description="Indica se o trabalho foi concluído com sucesso.",
    )

    output: FrozenDict = Field(
        default_factory=FrozenDict,
        description="Saída estruturada produzida pelo agente.",
    )

    evidence_references: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evidências utilizadas ou produzidas.",
    )

    messages: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Mensagens informativas da execução.",
    )

    error: str | None = Field(
        default=None,
        description="Erro identificado durante o trabalho.",
    )

    @field_validator(
        "output",
        mode="before",
    )
    @classmethod
    def freeze_output(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte mappings para FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "output precisa ser um objeto do tipo mapping."
            )

        return FrozenDict(value)

    @field_validator("status")
    @classmethod
    def validate_final_status(
        cls,
        value: AgentStatus,
    ) -> AgentStatus:
        """
        Somente estados finais são permitidos.
        """

        allowed_statuses = {
            AgentStatus.COMPLETED,
            AgentStatus.FAILED,
            AgentStatus.SKIPPED,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "AgentWorkResult exige estado final: "
                "COMPLETED, FAILED ou SKIPPED."
            )

        return value

    @model_validator(mode="after")
    def validate_success_consistency(
        self,
    ) -> "AgentWorkResult":
        """
        Garante coerência entre status e success.
        """

        if self.status == AgentStatus.FAILED and self.success:
            raise ValueError(
                "Uma execução FAILED não pode possuir success=True."
            )

        if self.status == AgentStatus.COMPLETED and not self.success:
            raise ValueError(
                "Uma execução COMPLETED não pode possuir success=False."
            )

        return self

    @field_serializer("output")
    def serialize_output(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte a saída para JSON quando necessário.
        """

        return value.to_dict()


class BaseAgent(ABC):
    """
    Classe-base de todos os agentes do SOC.

    Cada agente especializado precisa definir:

    - agent_id;
    - agent_name;
    - description;
    - método run().
    """

    agent_id: ClassVar[str] = ""
    agent_name: ClassVar[str] = ""
    description: ClassVar[str] = ""

    allowed_tools: ClassVar[tuple[str, ...]] = ()

    def __init__(self) -> None:
        """
        Valida a configuração básica da implementação.
        """

        if not self.agent_id.strip():
            raise ValueError(
                "Todo agente precisa definir agent_id."
            )

        if not self.agent_name.strip():
            raise ValueError(
                "Todo agente precisa definir agent_name."
            )

        if not self.description.strip():
            raise ValueError(
                "Todo agente precisa definir description."
            )

    def execute(
        self,
        request: AgentExecutionRequest,
    ) -> AgentExecutionResult:
        """
        Executa o agente de maneira controlada.

        Este método não deve ser sobrescrito pelos agentes
        especializados.

        A lógica específica deve ficar em run().
        """

        started_at = datetime.now(timezone.utc)
        start_timer = perf_counter()

        validation_error = self._validate_request(
            request=request,
        )

        if validation_error is not None:
            return self._failure_result(
                request=request,
                error=validation_error,
                started_at=started_at,
                start_timer=start_timer,
            )

        try:
            work_result = self.run(request)

        except Exception as exc:
            return self._failure_result(
                request=request,
                error=(
                    f"{type(exc).__name__}: {exc}"
                ),
                started_at=started_at,
                start_timer=start_timer,
            )

        completed_at = datetime.now(timezone.utc)

        duration_ms = (
            perf_counter() - start_timer
        ) * 1000

        return AgentExecutionResult(
            execution_id=request.execution_id,
            agent_id=self.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            status=work_result.status,
            success=work_result.success,
            output=work_result.output,
            evidence_references=(
                work_result.evidence_references
            ),
            messages=work_result.messages,
            error=work_result.error,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _validate_request(
        self,
        request: AgentExecutionRequest,
    ) -> str | None:
        """
        Valida limites e identidade antes da execução.
        """

        if request.agent_id != self.agent_id:
            return (
                "Solicitação destinada ao agente "
                f"{request.agent_id}, mas recebida por "
                f"{self.agent_id}."
            )

        if (
            request.runtime.step_number
            > request.runtime.max_steps
        ):
            return (
                "Limite máximo de passos excedido: "
                f"{request.runtime.step_number} > "
                f"{request.runtime.max_steps}."
            )

        if (
            request.runtime.retry_count
            > request.runtime.max_retries
        ):
            return (
                "Limite máximo de retries excedido: "
                f"{request.runtime.retry_count} > "
                f"{request.runtime.max_retries}."
            )

        return None

    def _failure_result(
        self,
        request: AgentExecutionRequest,
        error: str,
        started_at: datetime,
        start_timer: float,
    ) -> AgentExecutionResult:
        """
        Constrói uma falha padronizada e fail-closed.
        """

        completed_at = datetime.now(timezone.utc)

        duration_ms = (
            perf_counter() - start_timer
        ) * 1000

        return AgentExecutionResult(
            execution_id=request.execution_id,
            agent_id=self.agent_id,
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

    def can_use_tool(
        self,
        tool_name: str,
    ) -> bool:
        """
        Informa se a ferramenta está declarada na allowlist
        conceitual do agente.

        A autorização definitiva será responsabilidade
        da futura camada de Permission Engine.
        """

        return tool_name in self.allowed_tools

    @abstractmethod
    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Implementa a responsabilidade especializada do agente.

        Nenhum agente deve alterar diretamente o CaseState.
        """