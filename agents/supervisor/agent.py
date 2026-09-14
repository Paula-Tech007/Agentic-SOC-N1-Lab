"""
AG-01 — SOC Supervisor Agent.

Responsável por coordenar o fluxo do Agentic SOC N1 Lab
e selecionar qual agente especializado deve atuar em seguida.

O Supervisor não substitui os especialistas.

Fluxo:

CaseState
    ↓
AG-01 SOC Supervisor
    ↓
analisa:
- case_status
- pending_agents
- completed_agents
- failed_agents
- step_count
- max_steps
    ↓
seleciona próximo agente
ou
interrompe o fluxo

Princípios:

- roteamento determinístico;
- não fabrica evidências;
- não executa investigação especializada;
- não executa contenção;
- respeita agentes pendentes;
- preserva histórico de execução;
- respeita estados finais;
- respeita limite máximo de passos;
- falha de forma conservadora;
- AG-12 é utilizado para decisão/escalonamento
  quando o fluxo não pode continuar normalmente.
"""

from collections.abc import Mapping
from typing import Any

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)


class SOCSupervisorAgent(BaseAgent):
    """
    AG-01 — SOC Supervisor Agent.
    """

    agent_id = "AG-01"

    agent_name = "SOC Supervisor Agent"

    description = (
        "Coordenar o fluxo e decidir quais agentes "
        "especializados devem atuar no caso."
    )

    allowed_tools: tuple[str, ...] = (
        "read_case_context",
        "read_workflow_state",
        "read_agent_status",
        "read_audit",
    )

    FINAL_CASE_STATUSES: frozenset[str] = frozenset(
        {
            "CLOSED_N1",
            "ESCALATED_N2",
            "WAITING_HUMAN",
            "FAILED",
            "CANCELLED",
        }
    )

    OFFICIAL_AGENT_IDS: frozenset[str] = frozenset(
        {
            "AG-01",
            "AG-02",
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
        }
    )

    VALID_SPECIALIST_AGENTS: frozenset[str] = frozenset(
        {
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
        }
    )

    STATUS_FALLBACK_ROUTES: dict[str, str] = {
        "TRIAGING": "AG-03",
        "INVESTIGATING": "AG-09",
        "CORRELATING": "AG-09",
        "REVIEWING": "AG-10",
        "DOCUMENTING": "AG-11",
        "DECIDING": "AG-12",
    }

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Seleciona o próximo agente do fluxo.

        Prioridades:

        1. Estado final -> interrompe.
        2. Limite de passos -> AG-12.
        3. pending_agents -> primeiro agente válido.
        4. Falha sem retry pendente -> AG-12.
        5. Fim do enriquecimento -> AG-09.
        6. RETRYING sem target -> AG-12.
        7. Status conhecido -> rota padrão.
        8. Estado desconhecido -> AG-12.
        """

        snapshot = request.case_snapshot.to_dict()

        case_id = self._required_string(
            snapshot.get("case_id"),
            "case_snapshot.case_id",
        )

        case_status = self._required_string(
            snapshot.get("case_status"),
            "case_snapshot.case_status",
        )

        workflow = self._required_mapping(
            snapshot.get("workflow"),
            "case_snapshot.workflow",
        )

        pending_agents = (
            self._pending_agent_list(
                workflow.get(
                    "pending_agents"
                )
            )
        )

        completed_agents = (
            self._history_agent_list(
                workflow.get(
                    "completed_agents"
                )
            )
        )

        failed_agents = (
            self._history_agent_list(
                workflow.get(
                    "failed_agents"
                )
            )
        )

        step_count = self._integer(
            workflow.get(
                "step_count",
                request.runtime.step_number - 1,
            ),
            "workflow.step_count",
            minimum=0,
        )

        max_steps = self._integer(
            workflow.get(
                "max_steps",
                request.runtime.max_steps,
            ),
            "workflow.max_steps",
            minimum=1,
        )

        if (
            case_status
            in self.FINAL_CASE_STATUSES
        ):
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id=None,
                should_continue=False,
                reason=(
                    "O caso já está em estado final "
                    "ou aguardando intervenção humana: "
                    f"{case_status}."
                ),
                routing_source=(
                    "FINAL_CASE_STATUS"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        if step_count >= max_steps:
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id="AG-12",
                should_continue=True,
                reason=(
                    "O limite máximo de passos do "
                    "workflow foi atingido. "
                    "O caso deve seguir para "
                    "decisão/escalonamento."
                ),
                routing_source=(
                    "MAX_STEPS_GUARDRAIL"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        if pending_agents:
            next_agent_id = (
                pending_agents[0]
            )

            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id=(
                    next_agent_id
                ),
                should_continue=True,
                reason=(
                    f"O agente {next_agent_id} "
                    "já está marcado como pendente "
                    "no WorkflowState."
                ),
                routing_source=(
                    "PENDING_AGENTS"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        if failed_agents:
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id="AG-12",
                should_continue=True,
                reason=(
                    "Existem agentes com falha e "
                    "não há retry pendente. "
                    "O caso deve seguir para "
                    "decisão/escalonamento."
                ),
                routing_source=(
                    "FAILED_AGENT_GUARDRAIL"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        if case_status == "ENRICHING":
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id="AG-09",
                should_continue=True,
                reason=(
                    "A fase de enriquecimento "
                    "não possui mais agentes "
                    "pendentes. O caso pode "
                    "seguir para investigação "
                    "consolidada."
                ),
                routing_source=(
                    "ENRICHMENT_COMPLETE"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        if case_status == "RETRYING":
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id="AG-12",
                should_continue=True,
                reason=(
                    "O caso está em RETRYING, "
                    "porém não possui retry target "
                    "pendente. Aplicando "
                    "fail-closed via AG-12."
                ),
                routing_source=(
                    "RETRY_WITHOUT_TARGET"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        fallback_agent = (
            self.STATUS_FALLBACK_ROUTES.get(
                case_status
            )
        )

        if fallback_agent is not None:
            return self._routing_result(
                case_id=case_id,
                case_status=case_status,
                next_agent_id=(
                    fallback_agent
                ),
                should_continue=True,
                reason=(
                    f"O status {case_status} "
                    "possui rota padrão para "
                    f"{fallback_agent}."
                ),
                routing_source=(
                    "CASE_STATUS"
                ),
                completed_agents=(
                    completed_agents
                ),
                failed_agents=failed_agents,
            )

        return self._routing_result(
            case_id=case_id,
            case_status=case_status,
            next_agent_id="AG-12",
            should_continue=True,
            reason=(
                "O Supervisor encontrou um "
                "estado que não possui rota "
                "operacional segura. "
                "Aplicando fail-closed via AG-12."
            ),
            routing_source="FAIL_CLOSED",
            completed_agents=(
                completed_agents
            ),
            failed_agents=failed_agents,
        )

    def _routing_result(
        self,
        case_id: str,
        case_status: str,
        next_agent_id: str | None,
        should_continue: bool,
        reason: str,
        routing_source: str,
        completed_agents: list[str],
        failed_agents: list[str],
    ) -> AgentWorkResult:
        """
        Constrói o contrato simples de roteamento.

        Não cria schema novo na Fase 2.
        """

        if next_agent_id is not None:
            if (
                next_agent_id
                not in self.VALID_SPECIALIST_AGENTS
            ):
                raise ValueError(
                    "Supervisor tentou selecionar "
                    "agente inválido: "
                    f"{next_agent_id}"
                )

        routing_result = {
            "case_id": case_id,
            "case_status": case_status,
            "next_agent_id": (
                next_agent_id
            ),
            "should_continue": (
                should_continue
            ),
            "reason": reason,
            "routing_source": (
                routing_source
            ),
            "completed_agents": (
                completed_agents
            ),
            "failed_agents": (
                failed_agents
            ),
        }

        reference = (
            next_agent_id
            if next_agent_id is not None
            else f"CASE-{case_id}-STOP"
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    reference
                ),
                "supervisor_result": (
                    routing_result
                ),
            },
            evidence_references=(),
            messages=(
                (
                    "AG-01 avaliou o estado "
                    "atual do workflow."
                ),
                (
                    "O Supervisor apenas "
                    "coordenou o fluxo; nenhuma "
                    "investigação ou ação crítica "
                    "foi executada."
                ),
            ),
        )

    def _pending_agent_list(
        self,
        value: Any,
    ) -> list[str]:
        """
        Valida agentes pendentes.

        Somente especialistas AG-03 até AG-12
        podem ser escolhidos para execução.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "pending_agents precisa "
                "ser uma lista."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(
                item,
                str,
            ):
                raise ValueError(
                    "agent_id pendente "
                    "precisa ser string."
                )

            cleaned = item.strip()

            if not cleaned:
                continue

            if cleaned in {
                "AG-01",
                "AG-02",
            }:
                continue

            if (
                cleaned
                not in self.VALID_SPECIALIST_AGENTS
            ):
                raise ValueError(
                    "Workflow contém "
                    "agent_id pendente "
                    "desconhecido: "
                    f"{cleaned}"
                )

            if cleaned not in result:
                result.append(
                    cleaned
                )

        return result

    def _history_agent_list(
        self,
        value: Any,
    ) -> list[str]:
        """
        Valida histórico de agentes.

        Diferente de pending_agents, aqui
        AG-01 e AG-02 são preservados,
        pois fazem parte do histórico real
        do caso.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Histórico de agentes precisa "
                "ser uma lista."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(
                item,
                str,
            ):
                raise ValueError(
                    "agent_id do histórico "
                    "precisa ser string."
                )

            cleaned = item.strip()

            if not cleaned:
                continue

            if (
                cleaned
                not in self.OFFICIAL_AGENT_IDS
            ):
                raise ValueError(
                    "Histórico contém agent_id "
                    "desconhecido: "
                    f"{cleaned}"
                )

            if cleaned not in result:
                result.append(
                    cleaned
                )

        return result

    @staticmethod
    def _required_mapping(
        value: Any,
        field_name: str,
    ) -> Mapping[str, Any]:
        """
        Valida mapping obrigatório.
        """

        if not isinstance(
            value,
            Mapping,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser um objeto."
            )

        return value

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Valida string obrigatória.
        """

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} não pode "
                "ser vazio."
            )

        return cleaned

    @staticmethod
    def _integer(
        value: Any,
        field_name: str,
        minimum: int,
    ) -> int:
        """
        Valida número inteiro.
        """

        if (
            isinstance(
                value,
                bool,
            )
            or not isinstance(
                value,
                int,
            )
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser inteiro."
            )

        if value < minimum:
            raise ValueError(
                f"{field_name} precisa ser "
                f"maior ou igual a {minimum}."
            )

        return value


soc_supervisor_agent = (
    SOCSupervisorAgent()
)