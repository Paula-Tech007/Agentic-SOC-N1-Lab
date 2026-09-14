"""
Orchestrator central do Agentic SOC N1 Lab.

O SOCOrchestrator conecta alertas, CaseState,
Runtime e agentes especializados.

Bootstrap:

Alerta bruto
    ↓
SOCOrchestrator
    ↓
AG-02 Alert Intake
    ↓
Alert oficial
    ↓
CaseState

Fluxo normal:

CaseState
    ↓
SOCOrchestrator
    ↓
AgentExecutionRequest
    ↓
AgentRuntime
    ↓
BaseAgent
    ↓
AgentExecutionResult
    ↓
Resultado de domínio validado
    ↓
CaseState atualizado
    ↓
WorkflowState atualizado

Princípios:

- o agente produz o resultado;
- o Orchestrator valida;
- o Orchestrator aplica no CaseState;
- resultados inválidos falham de forma controlada;
- Reflection/QA possui loop limitado;
- Case Management utiliza a auditoria append-only existente;
- nenhuma ação crítica é executada automaticamente.
"""

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from core.config import (
    AGENT_TIMEOUT_SECONDS,
    MAX_AGENT_STEPS,
)
from core.orchestrator.contracts import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentRuntimeContext,
)
from core.orchestrator.runtime import (
    AgentRuntime,
    agent_runtime,
)
from core.schemas import (
    AgentExecutionState,
    AgentStatus,
    Alert,
    AssetContext,
    AuditEvent,
    CaseStatus,
    EscalationResult,
    FinalDecision,
    IdentityContext,
    InvestigationResult,
    KnowledgeResult,
    PhishingResult,
    QAResult,
    QAStatus,
    ThreatIntelResult,
    TriageResult,
)
from core.state import CaseState


class SOCOrchestrator:
    """
    Orquestrador central do workflow multiagente.
    """

    def __init__(
        self,
        runtime: AgentRuntime | None = None,
    ) -> None:
        """
        Permite utilizar um Runtime específico para testes
        ou o Runtime global oficial.
        """

        self.runtime = (
            runtime
            if runtime is not None
            else agent_runtime
        )

    def bootstrap_case(
        self,
        raw_alert: Mapping[str, Any],
        case_id: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[
        CaseState | None,
        AgentExecutionResult,
    ]:
        """
        Executa o AG-02 antes da existência do CaseState.

        Fluxo:

        1. reserva case_id;
        2. reserva correlation_id;
        3. executa AG-02;
        4. recebe Alert normalizado;
        5. cria CaseState;
        6. registra AG-02 como COMPLETED.

        Se AG-02 falhar, nenhum CaseState é criado.
        """

        reserved_case_id = (
            case_id.strip()
            if isinstance(case_id, str)
            and case_id.strip()
            else self._create_case_id()
        )

        reserved_correlation_id = (
            correlation_id.strip()
            if isinstance(correlation_id, str)
            and correlation_id.strip()
            else self._create_correlation_id()
        )

        request = AgentExecutionRequest(
            execution_id=self._create_execution_id(),
            agent_id="AG-02",
            case_id=reserved_case_id,
            correlation_id=reserved_correlation_id,
            case_version=1,
            runtime=AgentRuntimeContext(
                step_number=1,
                max_steps=MAX_AGENT_STEPS,
                retry_count=0,
                timeout_seconds=AGENT_TIMEOUT_SECONDS,
            ),
            case_snapshot={
                "bootstrap": True,
                "case_id": reserved_case_id,
                "correlation_id": reserved_correlation_id,
            },
            input_payload=dict(raw_alert),
        )

        result = self.runtime.execute(
            request
        )

        if not result.success:
            return None, result

        normalized_alert = result.output.get(
            "normalized_alert"
        )

        if normalized_alert is None:
            failure = self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-02 concluiu sem retornar "
                    "'normalized_alert'."
                ),
            )

            return None, failure

        try:
            alert = Alert.model_validate(
                normalized_alert
            )

        except Exception as exc:
            failure = self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "O alerta normalizado retornado pelo "
                    "AG-02 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

            return None, failure

        if (
            alert.correlation_id
            != reserved_correlation_id
        ):
            failure = self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "correlation_id do alerta normalizado "
                    "não corresponde ao reservado pelo "
                    "Orchestrator."
                ),
            )

            return None, failure

        case_state = CaseState(
            case_id=reserved_case_id,
            correlation_id=reserved_correlation_id,
            alert=alert,
        )

        self._register_bootstrap_completion(
            case_state=case_state,
            result=result,
        )

        return case_state, result

    def execute_agent(
        self,
        case_state: CaseState,
        agent_id: str,
        input_payload: Mapping[str, Any] | None = None,
    ) -> AgentExecutionResult:
        """
        Executa um agente através do Runtime.

        Regras de contagem:

        - AG-01 e AG-12 pertencem ao plano de controle;
        - AG-01 e AG-12 não consomem step_count;
        - os demais agentes consomem step_count;
        - uma execução operacional recusada por max_steps
          não altera o CaseState.

        Depois da execução:

        1. valida a saída;
        2. aplica o resultado de domínio;
        3. atualiza WorkflowState;
        4. atualiza a versão do caso.
        """

        payload = (
            dict(input_payload)
            if input_payload is not None
            else {}
        )

        workflow = case_state.workflow

        existing_state = workflow.agents.get(
            agent_id
        )

        retry_count = 0

        if existing_state is not None:
            retry_count = (
                existing_state.retry_count
            )

            if (
                existing_state.status
                == AgentStatus.FAILED
            ):
                retry_count += 1

        control_plane_agents = {
            "AG-01",
            "AG-12",
        }

        consumes_operational_step = (
            agent_id
            not in control_plane_agents
        )

        if consumes_operational_step:
            step_number = (
                workflow.step_count + 1
            )
        else:
            step_number = min(
                max(
                    workflow.step_count,
                    1,
                ),
                workflow.max_steps,
            )

        if (
            consumes_operational_step
            and step_number
            > workflow.max_steps
        ):
            rejected_at = datetime.now(
                timezone.utc
            )

            return AgentExecutionResult(
                execution_id=(
                    self._create_execution_id()
                ),
                agent_id=agent_id,
                case_id=case_state.case_id,
                correlation_id=(
                    case_state.correlation_id
                ),
                status=AgentStatus.FAILED,
                success=False,
                output={},
                evidence_references=(),
                messages=(
                    "Execução recusada antes de "
                    "alterar o CaseState.",
                ),
                error=(
                    "Limite máximo de passos "
                    "excedido: "
                    f"{step_number} > "
                    f"{workflow.max_steps}."
                ),
                duration_ms=0.0,
                started_at=rejected_at,
                completed_at=rejected_at,
            )

        request = AgentExecutionRequest(
            execution_id=self._create_execution_id(),
            agent_id=agent_id,
            case_id=case_state.case_id,
            correlation_id=case_state.correlation_id,
            case_version=case_state.version,
            runtime=AgentRuntimeContext(
                step_number=step_number,
                max_steps=workflow.max_steps,
                retry_count=retry_count,
                timeout_seconds=AGENT_TIMEOUT_SECONDS,
            ),
            case_snapshot=self._build_case_snapshot(
                case_state
            ),
            input_payload=payload,
        )

        started_at = datetime.now(
            timezone.utc
        )

        self._mark_agent_running(
            case_state=case_state,
            agent_id=agent_id,
            step_number=step_number,
            retry_count=retry_count,
            started_at=started_at,
            consume_step=(
                consumes_operational_step
            ),
        )

        result = self.runtime.execute(
            request
        )

        result = self._apply_domain_result(
            case_state=case_state,
            request=request,
            result=result,
        )

        self._apply_execution_result(
            case_state=case_state,
            result=result,
        )

        return result

    def _apply_domain_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Aplica resultados específicos dos agentes
        ao CaseState.

        Somente resultados COMPLETED são aplicados.
        """

        if (
            result.status
            != AgentStatus.COMPLETED
        ):
            return result

        if result.agent_id == "AG-01":
            return self._apply_supervisor_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-03":
            return self._apply_triage_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-04":
            return (
                self._apply_threat_intel_result(
                    case_state=case_state,
                    request=request,
                    result=result,
                )
            )

        if result.agent_id == "AG-05":
            return self._apply_identity_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-06":
            return self._apply_asset_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-07":
            return self._apply_phishing_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-08":
            return self._apply_knowledge_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-09":
            return (
                self._apply_investigation_result(
                    case_state=case_state,
                    request=request,
                    result=result,
                )
            )

        if result.agent_id == "AG-10":
            return self._apply_qa_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        if result.agent_id == "AG-11":
            return (
                self._apply_case_management_result(
                    case_state=case_state,
                    request=request,
                    result=result,
                )
            )

        if result.agent_id == "AG-12":
            return self._apply_escalation_result(
                case_state=case_state,
                request=request,
                result=result,
            )

        return result

    def _apply_supervisor_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida e aplica o resultado do
        AG-01 SOC Supervisor.

        O Supervisor:

        - nao investiga;
        - nao cria evidencia;
        - nao executa contencao;
        - escolhe o proximo agente;
        - preserva a fila restante;
        - interrompe o fluxo quando o
          caso ja esta finalizado.
        """

        supervisor_data = (
            result.output.get(
                "supervisor_result"
            )
        )

        if not isinstance(
            supervisor_data,
            Mapping,
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-01 concluiu sem retornar "
                    "'supervisor_result' valido."
                ),
            )

        supervisor_case_id = (
            supervisor_data.get(
                "case_id"
            )
        )

        if (
            supervisor_case_id
            != case_state.case_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "case_id do supervisor_result "
                    "nao corresponde ao CaseState."
                ),
            )

        supervisor_case_status = (
            supervisor_data.get(
                "case_status"
            )
        )

        current_case_status = (
            case_state
            .workflow
            .case_status
            .value
        )

        if (
            supervisor_case_status
            != current_case_status
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "case_status do supervisor_result "
                    "nao corresponde ao status atual "
                    "do CaseState."
                ),
            )

        should_continue = (
            supervisor_data.get(
                "should_continue"
            )
        )

        if not isinstance(
            should_continue,
            bool,
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-01 retornou "
                    "should_continue invalido."
                ),
            )

        next_agent_id = (
            supervisor_data.get(
                "next_agent_id"
            )
        )

        if (
            next_agent_id is not None
            and not isinstance(
                next_agent_id,
                str,
            )
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-01 retornou "
                    "next_agent_id invalido."
                ),
            )

        if isinstance(
            next_agent_id,
            str,
        ):
            next_agent_id = (
                next_agent_id.strip()
            )

            if not next_agent_id:
                next_agent_id = None

        reason = supervisor_data.get(
            "reason"
        )

        if (
            not isinstance(
                reason,
                str,
            )
            or not reason.strip()
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-01 retornou "
                    "reason invalido."
                ),
            )

        routing_source = (
            supervisor_data.get(
                "routing_source"
            )
        )

        if (
            not isinstance(
                routing_source,
                str,
            )
            or not routing_source.strip()
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-01 retornou "
                    "routing_source invalido."
                ),
            )

        allowed_specialists = {
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

        if should_continue:
            if next_agent_id is None:
                return self._failure_from_result(
                    request=request,
                    original_result=result,
                    message=(
                        "AG-01 solicitou continuidade "
                        "sem definir next_agent_id."
                    ),
                )

            if (
                next_agent_id
                not in allowed_specialists
            ):
                return self._failure_from_result(
                    request=request,
                    original_result=result,
                    message=(
                        "AG-01 selecionou agente "
                        "nao autorizado: "
                        f"{next_agent_id}"
                    ),
                )

        else:
            if next_agent_id is not None:
                return self._failure_from_result(
                    request=request,
                    original_result=result,
                    message=(
                        "AG-01 solicitou parada do "
                        "workflow, mas retornou "
                        "next_agent_id."
                    ),
                )

        result_reference = (
            result.output.get(
                "result_reference"
            )
        )

        if should_continue:
            if (
                not isinstance(
                    result_reference,
                    str,
                )
                or result_reference.strip()
                != next_agent_id
            ):
                return self._failure_from_result(
                    request=request,
                    original_result=result,
                    message=(
                        "result_reference do AG-01 "
                        "nao corresponde ao "
                        "next_agent_id."
                    ),
                )

        workflow = case_state.workflow

        if not should_continue:
            workflow.pending_agents = []

            return result

        remaining_agents = [
            agent_id
            for agent_id in (
                workflow.pending_agents
            )
            if agent_id not in {
                "AG-01",
                next_agent_id,
            }
        ]

        workflow.pending_agents = [
            next_agent_id,
            *remaining_agents,
        ]

        return result

    def _apply_triage_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-03 e grava TriageResult.
        """

        triage_data = result.output.get(
            "triage_result"
        )

        if triage_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-03 concluiu sem retornar "
                    "'triage_result'."
                ),
            )

        try:
            triage = (
                TriageResult.model_validate(
                    triage_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "TriageResult retornado pelo "
                    "AG-03 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        if (
            triage.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do TriageResult não "
                    "corresponde ao alerta do "
                    "CaseState."
                ),
            )

        case_state.triage = triage

        workflow = case_state.workflow

        workflow.pending_agents = (
            self._normalize_agent_ids(
                triage.required_agents,
                exclude={
                    "AG-02",
                    "AG-03",
                },
            )
        )

        if triage.immediate_escalation:
            if (
                "AG-12"
                not in workflow.pending_agents
            ):
                workflow.pending_agents.append(
                    "AG-12"
                )

        workflow.case_status = (
            CaseStatus.ENRICHING
        )

        return result

    def _apply_threat_intel_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-04 e grava ThreatIntelResult.
        """

        threat_intel_data = (
            result.output.get(
                "threat_intel_result"
            )
        )

        if threat_intel_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-04 concluiu sem retornar "
                    "'threat_intel_result'."
                ),
            )

        try:
            threat_intel = (
                ThreatIntelResult.model_validate(
                    threat_intel_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "ThreatIntelResult retornado pelo "
                    "AG-04 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        if (
            threat_intel.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do ThreatIntelResult não "
                    "corresponde ao alerta do "
                    "CaseState."
                ),
            )

        case_state.threat_intel = (
            threat_intel
        )

        return result

    def _apply_identity_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-05 e grava IdentityContext.

        Identidades repetidas são atualizadas
        através de identity_id.
        """

        alert_id = result.output.get(
            "alert_id"
        )

        if not isinstance(
            alert_id,
            str,
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-05 concluiu sem retornar "
                    "um 'alert_id' válido."
                ),
            )

        if (
            alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do resultado do "
                    "AG-05 não corresponde ao "
                    "alerta do CaseState."
                ),
            )

        identities_data = (
            result.output.get(
                "identities"
            )
        )

        if not isinstance(
            identities_data,
            (list, tuple),
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-05 concluiu sem retornar "
                    "'identities' em formato "
                    "de lista."
                ),
            )

        if not identities_data:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-05 concluiu sem retornar "
                    "nenhuma identidade."
                ),
            )

        identities: list[
            IdentityContext
        ] = []

        seen_identity_ids: set[str] = set()

        for position, item in enumerate(
            identities_data,
            start=1,
        ):
            try:
                identity = (
                    IdentityContext.model_validate(
                        item
                    )
                )

            except Exception as exc:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "IdentityContext inválido "
                            f"na posição {position}: "
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    )
                )

            if (
                identity.identity_id
                in seen_identity_ids
            ):
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "AG-05 retornou "
                            "identity_id duplicado: "
                            f"{identity.identity_id}"
                        ),
                    )
                )

            seen_identity_ids.add(
                identity.identity_id
            )

            identities.append(
                identity
            )

        case_state.identities = (
            self._merge_identity_contexts(
                existing=case_state.identities,
                incoming=identities,
            )
        )

        return result

    def _apply_asset_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-06 e grava AssetContext.

        Ativos repetidos são atualizados
        através de asset_id.
        """

        alert_id = result.output.get(
            "alert_id"
        )

        if not isinstance(
            alert_id,
            str,
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-06 concluiu sem retornar "
                    "um 'alert_id' válido."
                ),
            )

        if (
            alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do resultado do "
                    "AG-06 não corresponde ao "
                    "alerta do CaseState."
                ),
            )

        assets_data = result.output.get(
            "assets"
        )

        if not isinstance(
            assets_data,
            (list, tuple),
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-06 concluiu sem retornar "
                    "'assets' em formato de lista."
                ),
            )

        if not assets_data:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-06 concluiu sem retornar "
                    "nenhum ativo."
                ),
            )

        assets: list[
            AssetContext
        ] = []

        seen_asset_ids: set[str] = set()

        for position, item in enumerate(
            assets_data,
            start=1,
        ):
            try:
                asset = (
                    AssetContext.model_validate(
                        item
                    )
                )

            except Exception as exc:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "AssetContext inválido "
                            f"na posição {position}: "
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    )
                )

            if (
                asset.asset_id
                in seen_asset_ids
            ):
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "AG-06 retornou "
                            "asset_id duplicado: "
                            f"{asset.asset_id}"
                        ),
                    )
                )

            seen_asset_ids.add(
                asset.asset_id
            )

            assets.append(
                asset
            )

        case_state.assets = (
            self._merge_asset_contexts(
                existing=case_state.assets,
                incoming=assets,
            )
        )

        return result

    def _apply_phishing_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-07 e grava PhishingResult.

        O AG-07:

        - analisa somente alertas PHISHING;
        - retorna PhishingResult;
        - nao executa URLs;
        - nao executa anexos;
        - nao executa acao critica;
        - grava o resultado em CaseState.phishing.

        Se o AG-07 for o ultimo agente
        pendente da fase de enriquecimento,
        o caso avanca para INVESTIGATING.
        """

        phishing_data = (
            result.output.get(
                "phishing_result"
            )
        )

        if phishing_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-07 concluiu sem retornar "
                    "'phishing_result'."
                ),
            )

        try:
            phishing = (
                PhishingResult.model_validate(
                    phishing_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "PhishingResult retornado pelo "
                    "AG-07 e invalido: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

        if (
            phishing.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do PhishingResult "
                    "nao corresponde ao alerta "
                    "do CaseState."
                ),
            )

        result_reference = (
            result.output.get(
                "result_reference"
            )
        )

        if (
            not isinstance(
                result_reference,
                str,
            )
            or result_reference.strip()
            != phishing.phishing_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "result_reference do AG-07 "
                    "nao corresponde ao "
                    "phishing_id."
                ),
            )

        case_state.phishing = phishing

        workflow = case_state.workflow

        if not workflow.pending_agents:
            workflow.case_status = (
                CaseStatus.INVESTIGATING
            )

        return result

    def _apply_knowledge_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-08 e grava KnowledgeResult.

        Quando o enriquecimento termina,
        o caso avança para INVESTIGATING.
        """

        knowledge_data = (
            result.output.get(
                "knowledge_result"
            )
        )

        if knowledge_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-08 concluiu sem retornar "
                    "'knowledge_result'."
                ),
            )

        try:
            knowledge = (
                KnowledgeResult.model_validate(
                    knowledge_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "KnowledgeResult retornado pelo "
                    "AG-08 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        if (
            knowledge.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do KnowledgeResult "
                    "não corresponde ao alerta "
                    "do CaseState."
                ),
            )

        case_state.knowledge = knowledge

        workflow = case_state.workflow

        if not workflow.pending_agents:
            workflow.case_status = (
                CaseStatus.INVESTIGATING
            )

        return result

    def _apply_investigation_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-09 e grava InvestigationResult.

        Depois da investigação:

        - status vai para REVIEWING;
        - AG-10 passa a ser pendente.
        """

        investigation_data = (
            result.output.get(
                "investigation_result"
            )
        )

        if investigation_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-09 concluiu sem retornar "
                    "'investigation_result'."
                ),
            )

        try:
            investigation = (
                InvestigationResult.model_validate(
                    investigation_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "InvestigationResult retornado "
                    "pelo AG-09 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        if (
            investigation.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do InvestigationResult "
                    "não corresponde ao alerta do "
                    "CaseState."
                ),
            )

        case_state.investigation = (
            investigation
        )

        workflow = case_state.workflow

        workflow.case_status = (
            CaseStatus.REVIEWING
        )

        workflow.pending_agents = [
            "AG-10"
        ]

        return result

    def _apply_qa_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida AG-10 e grava QAResult.

        APPROVED:
            DOCUMENTING
                ↓
            AG-11

        REJECTED dentro do limite:
            RETRYING
                ↓
            retry_targets

        REJECTED acima do limite:
            DECIDING
                ↓
            AG-12
        """

        qa_data = result.output.get(
            "qa_result"
        )

        if qa_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-10 concluiu sem retornar "
                    "'qa_result'."
                ),
            )

        try:
            qa = QAResult.model_validate(
                qa_data
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "QAResult retornado pelo "
                    "AG-10 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        investigation = (
            case_state.investigation
        )

        if investigation is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-10 não pode ser aplicado "
                    "sem InvestigationResult no "
                    "CaseState."
                ),
            )

        if (
            qa.investigation_id
            != investigation.investigation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "investigation_id do QAResult "
                    "não corresponde à investigação "
                    "atual do CaseState."
                ),
            )

        if (
            qa.status
            == QAStatus.NOT_REVIEWED
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-10 não pode concluir com "
                    "QAStatus.NOT_REVIEWED."
                ),
            )

        workflow = case_state.workflow

        if (
            qa.status
            == QAStatus.APPROVED
        ):
            if qa.retry_required:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "QA aprovado não pode "
                            "solicitar retry."
                        ),
                    )
                )

            if qa.retry_targets:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "QA aprovado não pode "
                            "possuir retry_targets."
                        ),
                    )
                )

            case_state.qa = qa

            workflow.case_status = (
                CaseStatus.DOCUMENTING
            )

            workflow.pending_agents = [
                "AG-11"
            ]

            return result

        if (
            qa.status
            == QAStatus.REJECTED
        ):
            if not qa.retry_required:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "QA rejeitado precisa "
                            "solicitar retry."
                        ),
                    )
                )

            retry_targets = (
                self._normalize_agent_ids(
                    qa.retry_targets,
                    exclude={
                        "AG-10",
                    },
                )
            )

            if not retry_targets:
                return (
                    self._failure_from_result(
                        request=request,
                        original_result=result,
                        message=(
                            "QA rejeitado precisa "
                            "possuir pelo menos um "
                            "retry_target válido."
                        ),
                    )
                )

            case_state.qa = qa

            next_retry_count = (
                workflow.reflection_retry_count
                + 1
            )

            workflow.reflection_retry_count = (
                next_retry_count
            )

            if (
                next_retry_count
                <= workflow.max_reflection_retries
            ):
                workflow.case_status = (
                    CaseStatus.RETRYING
                )

                workflow.pending_agents = (
                    retry_targets
                )

                return result

            workflow.case_status = (
                CaseStatus.DECIDING
            )

            workflow.pending_agents = [
                "AG-12"
            ]

            return result

        return self._failure_from_result(
            request=request,
            original_result=result,
            message=(
                "QAStatus não suportado pelo "
                "Orchestrator."
            ),
        )

    def _apply_case_management_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida o resultado do AG-11 Case Management.

        O AG-11:

        - exige investigação existente;
        - exige QA APPROVED;
        - retorna documentação consolidada;
        - retorna AuditEvent;
        - AuditEvent é adicionado ao CaseState
          usando o método append-only oficial;
        - o caso avança para DECIDING;
        - AG-12 passa a ser o próximo agente.

        Não é criado um campo case_management
        no CaseState.
        """

        documentation_data = (
            result.output.get(
                "case_documentation"
            )
        )

        if not isinstance(
            documentation_data,
            Mapping,
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-11 concluiu sem retornar "
                    "'case_documentation' válida."
                ),
            )

        documentation_id = (
            documentation_data.get(
                "documentation_id"
            )
        )

        if not isinstance(
            documentation_id,
            str,
        ) or not documentation_id.strip():
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "case_documentation não possui "
                    "documentation_id válido."
                ),
            )

        documentation_id = (
            documentation_id.strip()
        )

        documentation_case_id = (
            documentation_data.get(
                "case_id"
            )
        )

        if (
            documentation_case_id
            != case_state.case_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "case_id da documentação do "
                    "AG-11 não corresponde ao "
                    "CaseState."
                ),
            )

        documentation_correlation_id = (
            documentation_data.get(
                "correlation_id"
            )
        )

        if (
            documentation_correlation_id
            != case_state.correlation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "correlation_id da documentação "
                    "do AG-11 não corresponde ao "
                    "CaseState."
                ),
            )

        documentation_alert_id = (
            documentation_data.get(
                "alert_id"
            )
        )

        if (
            documentation_alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id da documentação do "
                    "AG-11 não corresponde ao "
                    "alerta do CaseState."
                ),
            )

        investigation = (
            case_state.investigation
        )

        if investigation is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-11 não pode documentar "
                    "um caso sem InvestigationResult."
                ),
            )

        documentation_investigation_id = (
            documentation_data.get(
                "investigation_id"
            )
        )

        if (
            documentation_investigation_id
            != investigation.investigation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "investigation_id da documentação "
                    "não corresponde à investigação "
                    "atual do CaseState."
                ),
            )

        qa = case_state.qa

        if qa is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-11 não pode documentar "
                    "um caso sem QAResult."
                ),
            )

        if qa.status != QAStatus.APPROVED:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-11 somente pode documentar "
                    "casos com QA APPROVED."
                ),
            )

        documentation_qa_id = (
            documentation_data.get(
                "qa_id"
            )
        )

        if (
            documentation_qa_id
            != qa.qa_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "qa_id da documentação não "
                    "corresponde ao QAResult atual "
                    "do CaseState."
                ),
            )

        result_reference = (
            result.output.get(
                "result_reference"
            )
        )

        if (
            not isinstance(
                result_reference,
                str,
            )
            or result_reference.strip()
            != documentation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "result_reference do AG-11 não "
                    "corresponde ao documentation_id."
                ),
            )

        audit_data = result.output.get(
            "audit_event"
        )

        if audit_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-11 concluiu sem retornar "
                    "'audit_event'."
                ),
            )

        try:
            audit_event = (
                AuditEvent.model_validate(
                    audit_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AuditEvent retornado pelo "
                    "AG-11 é inválido: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        if (
            audit_event.actor_type
            != "AGENT"
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AuditEvent do AG-11 precisa "
                    "possuir actor_type AGENT."
                ),
            )

        if (
            audit_event.actor_id
            != "AG-11"
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AuditEvent do Case Management "
                    "precisa possuir actor_id AG-11."
                ),
            )

        if (
            audit_event.event_type
            != "CASE_DOCUMENTED"
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AuditEvent do AG-11 precisa "
                    "possuir event_type "
                    "CASE_DOCUMENTED."
                ),
            )

        if (
            audit_event.status
            != "SUCCESS"
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AuditEvent do AG-11 precisa "
                    "possuir status SUCCESS."
                ),
            )

        try:
            case_state.add_audit_event(
                audit_event
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "Falha ao adicionar AuditEvent "
                    "do AG-11 ao CaseState: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        workflow = case_state.workflow

        workflow.case_status = (
            CaseStatus.DECIDING
        )

        workflow.pending_agents = [
            "AG-12"
        ]

        return result

    def _apply_escalation_result(
        self,
        case_state: CaseState,
        request: AgentExecutionRequest,
        result: AgentExecutionResult,
    ) -> AgentExecutionResult:
        """
        Valida o resultado do AG-12 Escalation.

        O AG-12:

        - retorna EscalationResult;
        - referencia o alerta atual;
        - referencia a investigacao atual;
        - referencia o QA atual;
        - grava em CaseState.escalation;
        - atualiza o estado final do caso.

        Mapeamento:

        CLOSED_N1
            -> CaseStatus.CLOSED_N1

        ESCALATED_N2
            -> CaseStatus.ESCALATED_N2

        WAITING_HUMAN
            -> CaseStatus.WAITING_HUMAN

        Nenhuma acao critica e executada
        automaticamente.
        """

        escalation_data = (
            result.output.get(
                "escalation_result"
            )
        )

        if escalation_data is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-12 concluiu sem retornar "
                    "'escalation_result'."
                ),
            )

        try:
            escalation = (
                EscalationResult.model_validate(
                    escalation_data
                )
            )

        except Exception as exc:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "EscalationResult retornado "
                    "pelo AG-12 e invalido: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

        if (
            escalation.alert_id
            != case_state.alert.alert_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "alert_id do "
                    "EscalationResult nao "
                    "corresponde ao alerta "
                    "do CaseState."
                ),
            )

        investigation = (
            case_state.investigation
        )

        if investigation is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-12 nao pode ser "
                    "aplicado sem "
                    "InvestigationResult "
                    "no CaseState."
                ),
            )

        if (
            escalation.investigation_id
            != investigation.investigation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "investigation_id do "
                    "EscalationResult nao "
                    "corresponde a investigacao "
                    "atual do CaseState."
                ),
            )

        qa = case_state.qa

        if qa is None:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "AG-12 nao pode ser "
                    "aplicado sem QAResult "
                    "no CaseState."
                ),
            )

        if (
            escalation.qa_id
            != qa.qa_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "qa_id do EscalationResult "
                    "nao corresponde ao "
                    "QAResult atual do "
                    "CaseState."
                ),
            )

        result_reference = (
            result.output.get(
                "result_reference"
            )
        )

        if (
            not isinstance(
                result_reference,
                str,
            )
            or result_reference.strip()
            != escalation.escalation_id
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "result_reference do "
                    "AG-12 nao corresponde "
                    "ao escalation_id."
                ),
            )

        if (
            escalation.decision
            == FinalDecision.CLOSED_N1
            and
            escalation.human_approval_required
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "CLOSED_N1 nao pode "
                    "exigir aprovacao humana "
                    "pendente."
                ),
            )

        if (
            escalation.decision
            in {
                FinalDecision.ESCALATED_N2,
                FinalDecision.WAITING_HUMAN,
            }
            and not
            escalation.human_approval_required
        ):
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "Decisao que depende de "
                    "N2/humano precisa marcar "
                    "human_approval_required="
                    "True."
                ),
            )

        workflow = case_state.workflow

        if (
            escalation.decision
            == FinalDecision.CLOSED_N1
        ):
            target_status = (
                CaseStatus.CLOSED_N1
            )

        elif (
            escalation.decision
            == FinalDecision.ESCALATED_N2
        ):
            target_status = (
                CaseStatus.ESCALATED_N2
            )

        elif (
            escalation.decision
            == FinalDecision.WAITING_HUMAN
        ):
            target_status = (
                CaseStatus.WAITING_HUMAN
            )

        else:
            return self._failure_from_result(
                request=request,
                original_result=result,
                message=(
                    "FinalDecision nao "
                    "suportado pelo "
                    "Orchestrator."
                ),
            )

        case_state.escalation = (
            escalation
        )

        workflow.case_status = (
            target_status
        )

        workflow.pending_agents = []

        return result

    def _register_bootstrap_completion(
        self,
        case_state: CaseState,
        result: AgentExecutionResult,
    ) -> None:
        """
        Registra AG-02 como a primeira execução
        concluída do workflow.
        """

        workflow = case_state.workflow

        workflow.agents["AG-02"] = (
            AgentExecutionState(
                agent_id="AG-02",
                agent_name=self._agent_name(
                    "AG-02"
                ),
                status=AgentStatus.COMPLETED,
                started_at=result.started_at,
                completed_at=result.completed_at,
                retry_count=0,
                last_error=None,
                result_reference=(
                    self._extract_result_reference(
                        result
                    )
                ),
            )
        )

        workflow.case_status = (
            CaseStatus.TRIAGING
        )

        workflow.current_agent = None
        workflow.step_count = 1

        workflow.pending_agents = (
            self._remove_agent_id(
                workflow.pending_agents,
                "AG-02",
            )
        )

        workflow.failed_agents = (
            self._remove_agent_id(
                workflow.failed_agents,
                "AG-02",
            )
        )

        workflow.skipped_agents = (
            self._remove_agent_id(
                workflow.skipped_agents,
                "AG-02",
            )
        )

        workflow.completed_agents = (
            self._remove_agent_id(
                workflow.completed_agents,
                "AG-02",
            )
        )

        workflow.completed_agents.append(
            "AG-02"
        )

        workflow.last_transition_at = (
            result.completed_at
        )

        case_state.touch()

    def _failure_from_result(
        self,
        request: AgentExecutionRequest,
        original_result: AgentExecutionResult,
        message: str,
    ) -> AgentExecutionResult:
        """
        Converte um resultado aparentemente concluído
        em falha controlada quando sua saída não atende
        ao contrato do Orchestrator.
        """

        return AgentExecutionResult(
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            status=AgentStatus.FAILED,
            success=False,
            output={},
            evidence_references=(
                original_result.evidence_references
            ),
            messages=original_result.messages,
            error=message,
            duration_ms=original_result.duration_ms,
            started_at=original_result.started_at,
            completed_at=datetime.now(
                timezone.utc
            ),
        )

    def _create_execution_id(
        self,
    ) -> str:
        """
        Gera identificador único de execução.
        """

        return (
            "EXEC-"
            + uuid4().hex.upper()
        )

    def _create_case_id(
        self,
    ) -> str:
        """
        Gera identificador único de caso.
        """

        return (
            "CASE-"
            + uuid4().hex.upper()
        )

    def _create_correlation_id(
        self,
    ) -> str:
        """
        Gera identificador de correlação.
        """

        return (
            "CORR-"
            + uuid4().hex.upper()
        )

    def _build_case_snapshot(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Cria contexto consolidado enviado aos agentes.
        """

        return {
            "case_id": (
                case_state.case_id
            ),
            "correlation_id": (
                case_state.correlation_id
            ),
            "case_version": (
                case_state.version
            ),
            "case_status": (
                case_state
                .workflow
                .case_status
                .value
            ),
            "alert": (
                case_state
                .alert
                .model_dump(
                    mode="json"
                )
            ),
            "ioc_references": [
                item.ioc_id
                for item in case_state.iocs
            ],
            "identity_references": [
                item.identity_id
                for item in (
                    case_state.identities
                )
            ],
            "asset_references": [
                item.asset_id
                for item in (
                    case_state.assets
                )
            ],
            "evidence_references": [
                item.evidence_id
                for item in (
                    case_state.evidence
                )
            ],
            "triage": (
                case_state
                .triage
                .model_dump(
                    mode="json"
                )
                if case_state.triage
                is not None
                else None
            ),
            "threat_intel": (
                case_state
                .threat_intel
                .model_dump(
                    mode="json"
                )
                if case_state.threat_intel
                is not None
                else None
            ),
            "identities": [
                identity.model_dump(
                    mode="json"
                )
                for identity in (
                    case_state.identities
                )
            ],
            "assets": [
                asset.model_dump(
                    mode="json"
                )
                for asset in (
                    case_state.assets
                )
            ],
            "phishing": (
                case_state
                .phishing
                .model_dump(
                    mode="json"
                )
                if case_state.phishing
                is not None
                else None
            ),
            "knowledge": (
                case_state
                .knowledge
                .model_dump(
                    mode="json"
                )
                if case_state.knowledge
                is not None
                else None
            ),
            "investigation": (
                case_state
                .investigation
                .model_dump(
                    mode="json"
                )
                if case_state.investigation
                is not None
                else None
            ),
            "qa": (
                case_state
                .qa
                .model_dump(
                    mode="json"
                )
                if case_state.qa
                is not None
                else None
            ),
            "audit": [
                audit_event.model_dump(
                    mode="json"
                )
                for audit_event in (
                    case_state.audit
                )
            ],
            "workflow": {
                "step_count": (
                    case_state
                    .workflow
                    .step_count
                ),
                "max_steps": (
                    case_state
                    .workflow
                    .max_steps
                ),
                "reflection_retry_count": (
                    case_state
                    .workflow
                    .reflection_retry_count
                ),
                "max_reflection_retries": (
                    case_state
                    .workflow
                    .max_reflection_retries
                ),
                "pending_agents": list(
                    case_state
                    .workflow
                    .pending_agents
                ),
                "completed_agents": list(
                    case_state
                    .workflow
                    .completed_agents
                ),
                "failed_agents": list(
                    case_state
                    .workflow
                    .failed_agents
                ),
            },
        }

    def _agent_name(
        self,
        agent_id: str,
    ) -> str:
        """
        Recupera nome oficial do agente.
        """

        try:
            definition = (
                self.runtime
                .registry
                .definition(
                    agent_id
                )
            )

            return definition.name

        except KeyError:
            return agent_id

    def _mark_agent_running(
        self,
        case_state: CaseState,
        agent_id: str,
        step_number: int,
        retry_count: int,
        started_at: datetime,
        consume_step: bool = True,
    ) -> None:
        """
        Marca agente como RUNNING.

        Agentes do plano de controle podem executar
        sem consumir o orçamento operacional de
        step_count.
        """

        workflow = case_state.workflow

        workflow.agents[agent_id] = (
            AgentExecutionState(
                agent_id=agent_id,
                agent_name=self._agent_name(
                    agent_id
                ),
                status=AgentStatus.RUNNING,
                started_at=started_at,
                completed_at=None,
                retry_count=retry_count,
                last_error=None,
                result_reference=None,
            )
        )

        workflow.current_agent = (
            agent_id
        )

        if consume_step:
            workflow.step_count = (
                step_number
            )

        workflow.pending_agents = (
            self._remove_agent_id(
                workflow.pending_agents,
                agent_id,
            )
        )

        workflow.completed_agents = (
            self._remove_agent_id(
                workflow.completed_agents,
                agent_id,
            )
        )

        workflow.failed_agents = (
            self._remove_agent_id(
                workflow.failed_agents,
                agent_id,
            )
        )

        workflow.skipped_agents = (
            self._remove_agent_id(
                workflow.skipped_agents,
                agent_id,
            )
        )

        workflow.last_transition_at = (
            started_at
        )

    def _apply_execution_result(
        self,
        case_state: CaseState,
        result: AgentExecutionResult,
    ) -> None:
        """
        Aplica resultado operacional ao WorkflowState.
        """

        workflow = case_state.workflow

        previous_state = (
            workflow.agents.get(
                result.agent_id
            )
        )

        started_at = None
        retry_count = 0

        if previous_state is not None:
            started_at = (
                previous_state.started_at
            )

            retry_count = (
                previous_state.retry_count
            )

        result_reference = (
            self._extract_result_reference(
                result
            )
        )

        workflow.agents[
            result.agent_id
        ] = AgentExecutionState(
            agent_id=result.agent_id,
            agent_name=self._agent_name(
                result.agent_id
            ),
            status=result.status,
            started_at=started_at,
            completed_at=result.completed_at,
            retry_count=retry_count,
            last_error=result.error,
            result_reference=(
                result_reference
            ),
        )

        workflow.current_agent = None

        workflow.completed_agents = (
            self._remove_agent_id(
                workflow.completed_agents,
                result.agent_id,
            )
        )

        workflow.failed_agents = (
            self._remove_agent_id(
                workflow.failed_agents,
                result.agent_id,
            )
        )

        workflow.skipped_agents = (
            self._remove_agent_id(
                workflow.skipped_agents,
                result.agent_id,
            )
        )

        if (
            result.status
            == AgentStatus.COMPLETED
        ):
            workflow.completed_agents.append(
                result.agent_id
            )

        elif (
            result.status
            == AgentStatus.FAILED
        ):
            workflow.failed_agents.append(
                result.agent_id
            )

        elif (
            result.status
            == AgentStatus.SKIPPED
        ):
            workflow.skipped_agents.append(
                result.agent_id
            )

        workflow.last_transition_at = (
            result.completed_at
        )

        case_state.touch()

    def _extract_result_reference(
        self,
        result: AgentExecutionResult,
    ) -> str | None:
        """
        Recupera referência principal produzida.
        """

        value = result.output.get(
            "result_reference"
        )

        if isinstance(
            value,
            str,
        ):
            cleaned_value = (
                value.strip()
            )

            if cleaned_value:
                return cleaned_value

        return None

    @staticmethod
    def _merge_identity_contexts(
        existing: list[IdentityContext],
        incoming: list[IdentityContext],
    ) -> list[IdentityContext]:
        """
        Mescla identidades por identity_id.
        """

        merged = list(
            existing
        )

        positions = {
            identity.identity_id: index
            for index, identity in enumerate(
                merged
            )
        }

        for identity in incoming:
            position = positions.get(
                identity.identity_id
            )

            if position is None:
                positions[
                    identity.identity_id
                ] = len(merged)

                merged.append(
                    identity
                )

            else:
                merged[position] = (
                    identity
                )

        return merged

    @staticmethod
    def _merge_asset_contexts(
        existing: list[AssetContext],
        incoming: list[AssetContext],
    ) -> list[AssetContext]:
        """
        Mescla ativos por asset_id.
        """

        merged = list(
            existing
        )

        positions = {
            asset.asset_id: index
            for index, asset in enumerate(
                merged
            )
        }

        for asset in incoming:
            position = positions.get(
                asset.asset_id
            )

            if position is None:
                positions[
                    asset.asset_id
                ] = len(merged)

                merged.append(
                    asset
                )

            else:
                merged[position] = asset

        return merged

    @staticmethod
    def _normalize_agent_ids(
        values: Any,
        exclude: set[str] | None = None,
    ) -> list[str]:
        """
        Normaliza agent_ids.

        Remove:

        - valores inválidos;
        - strings vazias;
        - IDs excluídos;
        - duplicados.
        """

        excluded = (
            exclude
            if exclude is not None
            else set()
        )

        if values is None:
            return []

        if not isinstance(
            values,
            (list, tuple),
        ):
            raise ValueError(
                "Lista de agentes esperada."
            )

        result: list[str] = []

        for value in values:
            if not isinstance(
                value,
                str,
            ):
                continue

            cleaned = (
                value.strip()
            )

            if not cleaned:
                continue

            if cleaned in excluded:
                continue

            if cleaned not in result:
                result.append(
                    cleaned
                )

        return result

    @staticmethod
    def _remove_agent_id(
        values: list[str],
        agent_id: str,
    ) -> list[str]:
        """
        Remove todas as ocorrências de um agent_id.
        """

        return [
            value
            for value in values
            if value != agent_id
        ]


soc_orchestrator = SOCOrchestrator()