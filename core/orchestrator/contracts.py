"""
Contratos oficiais de execução dos agentes
do Agentic SOC N1 Lab.

Este módulo padroniza a comunicação entre:

- SOC Supervisor;
- Orchestrator;
- agentes especializados;
- CaseState;
- mecanismos de auditoria.

Nenhum agente deve alterar diretamente o CaseState completo.

O agente recebe um snapshot do contexto necessário,
executa sua responsabilidade e devolve um resultado
estruturado.

O Orchestrator é responsável por validar e aplicar
esse resultado ao estado central do caso.
"""

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

from core.schemas import AgentStatus
from core.schemas.immutable import FrozenDict


class AgentRuntimeContext(BaseModel):
    """
    Informações de controle utilizadas durante
    a execução de um agente.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    step_number: int = Field(
        ...,
        ge=1,
        description="Número atual do passo do workflow.",
    )

    max_steps: int = Field(
        ...,
        ge=1,
        description="Quantidade máxima de passos permitidos.",
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de retries já executados.",
    )

    max_retries: int = Field(
        default=2,
        ge=0,
        description="Quantidade máxima de retries permitidos.",
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Timeout permitido para o agente.",
    )


class AgentExecutionRequest(BaseModel):
    """
    Entrada padronizada entregue pelo Orchestrator
    para um agente.

    O objeto é imutável depois de criado.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    execution_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único da execução.",
    )

    agent_id: str = Field(
        ...,
        min_length=1,
        description="Identificador oficial do agente.",
    )

    case_id: str = Field(
        ...,
        min_length=1,
        description="Caso relacionado à execução.",
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador global de correlação.",
    )

    case_version: int = Field(
        ...,
        ge=1,
        description=(
            "Versão do CaseState utilizada para montar "
            "esta solicitação."
        ),
    )

    runtime: AgentRuntimeContext = Field(
        ...,
        description="Limites operacionais da execução.",
    )

    case_snapshot: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Snapshot imutável do contexto autorizado "
            "para o agente."
        ),
    )

    input_payload: FrozenDict = Field(
        default_factory=FrozenDict,
        description=(
            "Dados específicos necessários para "
            "a responsabilidade do agente."
        ),
    )

    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "case_snapshot",
        "input_payload",
        mode="before",
    )
    @classmethod
    def freeze_mapping(
        cls,
        value: Any,
    ) -> FrozenDict:
        """
        Converte mappings recebidos em FrozenDict.
        """

        if isinstance(value, FrozenDict):
            return value

        if not isinstance(value, Mapping):
            raise ValueError(
                "O valor precisa ser um objeto do tipo mapping."
            )

        return FrozenDict(value)

    @field_serializer(
        "case_snapshot",
        "input_payload",
    )
    def serialize_frozen_mapping(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Converte FrozenDict para estrutura JSON
        somente durante serialização.
        """

        return value.to_dict()


class AgentExecutionResult(BaseModel):
    """
    Resultado padronizado devolvido por qualquer agente.

    O agente não altera diretamente o CaseState.

    Ele informa ao Orchestrator:

    - se concluiu ou falhou;
    - qual saída produziu;
    - quais evidências utilizou;
    - eventuais mensagens de erro;
    - duração da execução.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        arbitrary_types_allowed=True,
    )

    execution_id: str = Field(
        ...,
        min_length=1,
    )

    agent_id: str = Field(
        ...,
        min_length=1,
    )

    case_id: str = Field(
        ...,
        min_length=1,
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
    )

    status: AgentStatus = Field(
        ...,
        description="Estado final da execução do agente.",
    )

    success: bool = Field(
        ...,
        description="Indica se a execução foi concluída com sucesso.",
    )

    output: FrozenDict = Field(
        default_factory=FrozenDict,
        description="Resultado estruturado produzido pelo agente.",
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
        description="Descrição do erro, quando houver.",
    )

    duration_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Tempo total da execução em milissegundos.",
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
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
        Garante que a saída estruturada seja imutável.
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
        AgentExecutionResult aceita somente estados finais.
        """

        allowed_statuses = {
            AgentStatus.COMPLETED,
            AgentStatus.FAILED,
            AgentStatus.SKIPPED,
        }

        if value not in allowed_statuses:
            raise ValueError(
                "AgentExecutionResult exige estado final: "
                "COMPLETED, FAILED ou SKIPPED."
            )

        return value

    @field_serializer("output")
    def serialize_output(
        self,
        value: FrozenDict,
    ) -> dict[str, Any]:
        """
        Serialização JSON da saída imutável.
        """

        return value.to_dict()