"""
Schema oficial de workflow do Agentic SOC N1 Lab.

Representa o estado operacional do caso e o estado
individual de cada agente envolvido na investigação.

Esse schema será utilizado futuramente principalmente pelo:

AG-01 — SOC Supervisor Agent

para saber:

- qual etapa do caso está ativa;
- quais agentes já executaram;
- quais ainda precisam executar;
- quais falharam;
- quais foram ignorados;
- quantos passos já ocorreram;
- quantos retries já foram realizados.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from core.schemas.enums import (
    AgentStatus,
    CaseStatus,
)


class AgentExecutionState(BaseModel):
    """
    Estado operacional de um agente dentro de um caso.
    """

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(
        ...,
        min_length=1,
        description="Identificador oficial do agente.",
    )

    agent_name: str = Field(
        ...,
        min_length=1,
        description="Nome funcional do agente.",
    )

    status: AgentStatus = Field(
        default=AgentStatus.PENDING,
        description="Estado atual da execução do agente.",
    )

    started_at: datetime | None = Field(
        default=None,
        description="Momento em que o agente iniciou a execução.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Momento em que o agente concluiu a execução.",
    )

    retry_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de retries realizados para o agente.",
    )

    last_error: str | None = Field(
        default=None,
        description="Último erro registrado durante a execução.",
    )

    result_reference: str | None = Field(
        default=None,
        description=(
            "ID do resultado produzido pelo agente, "
            "quando disponível."
        ),
    )


class WorkflowState(BaseModel):
    """
    Estado completo do workflow de um caso SOC.
    """

    model_config = ConfigDict(extra="forbid")

    case_status: CaseStatus = Field(
        default=CaseStatus.RECEIVED,
        description="Estado atual do caso.",
    )

    current_agent: str | None = Field(
        default=None,
        description="Agente atualmente em execução.",
    )

    agents: dict[str, AgentExecutionState] = Field(
        default_factory=dict,
        description="Estado individual dos agentes envolvidos.",
    )

    step_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de etapas executadas no caso.",
    )

    max_steps: int = Field(
        default=20,
        ge=1,
        description="Quantidade máxima permitida de etapas.",
    )

    reflection_retry_count: int = Field(
        default=0,
        ge=0,
        description="Quantidade de retries solicitados pelo QA.",
    )

    max_reflection_retries: int = Field(
        default=2,
        ge=0,
        description="Quantidade máxima de retries do fluxo de QA.",
    )

    pending_agents: list[str] = Field(
        default_factory=list,
        description="Agentes aguardando execução.",
    )

    completed_agents: list[str] = Field(
        default_factory=list,
        description="Agentes concluídos.",
    )

    failed_agents: list[str] = Field(
        default_factory=list,
        description="Agentes que falharam.",
    )

    skipped_agents: list[str] = Field(
        default_factory=list,
        description=(
            "Agentes não necessários para aquele incidente."
        ),
    )

    last_transition_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Momento da última transição do workflow.",
    )