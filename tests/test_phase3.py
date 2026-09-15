"""
Testes automatizados da Fase 3 do Agentic SOC N1 Lab.

Estes testes validam:

- catálogo oficial dos 12 agentes;
- registro dos agentes;
- prevenção de registro duplicado;
- Runtime fail-closed;
- contratos imutáveis de execução;
- limite máximo de passos;
- limite máximo de retries;
- bootstrap do AG-02 Alert Intake;
- falha controlada do bootstrap;
- roteamento do AG-01 SOC Supervisor;
- parada do Supervisor em estado final;
- guardrail de max_steps do Supervisor;
- fail-closed do Supervisor;
- análise defensiva do AG-07 Phishing;
- rejeição de alerta não phishing pelo AG-07;
- allowlist oficial de ferramentas de Email / Phishing;
- hard rules do AG-12 Escalation;
- fechamento automático conservador N1;
- decisão WAITING_HUMAN.
"""

import pytest

from agents.alert_intake import AlertIntakeAgent
from agents.asset import AssetContextAgent
from agents.case_management import CaseManagementAgent
from agents.escalation import EscalationAgent
from agents.identity import IdentityAnalystAgent
from agents.incident import IncidentAnalystAgent
from agents.knowledge import KnowledgeRAGAgent
from agents.phishing import PhishingAnalystAgent
from agents.reflection import ReflectionQAAgent
from agents.supervisor import SOCSupervisorAgent
from agents.threat_intel import ThreatIntelligenceAgent
from agents.triage import TriageAnalystAgent

from core.orchestrator import (
    OFFICIAL_AGENT_IDS,
    AgentExecutionRequest,
    AgentRegistry,
    AgentRuntime,
    AgentRuntimeContext,
    SOCOrchestrator,
)
from core.schemas import (
    AgentStatus,
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    CaseStatus,
    Severity,
)
from core.state import CaseState


AGENT_CLASSES = (
    SOCSupervisorAgent,
    AlertIntakeAgent,
    TriageAnalystAgent,
    ThreatIntelligenceAgent,
    IdentityAnalystAgent,
    AssetContextAgent,
    PhishingAnalystAgent,
    KnowledgeRAGAgent,
    IncidentAnalystAgent,
    ReflectionQAAgent,
    CaseManagementAgent,
    EscalationAgent,
)


def create_test_alert(
    alert_id: str = "ALT-PHASE3-0001",
    correlation_id: str = "CORR-PHASE3-0001",
    alert_type: AlertType = AlertType.AUTH_BRUTE_FORCE,
    severity: Severity = Severity.HIGH,
) -> Alert:
    """
    Cria um alerta padrão para os testes da Fase 3.
    """

    return Alert(
        alert_id=alert_id,
        correlation_id=correlation_id,
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name="Phase 3 Test Rule",
        ),
        event=AlertEvent(
            event_type=alert_type,
            category="security",
            message="Evento defensivo simulado para teste.",
            raw_event={
                "username": "lab.user",
                "source_ip": "203.0.113.10",
            },
        ),
        initial_severity=severity,
    )


def create_test_case(
    case_id: str = "CASE-PHASE3-0001",
    correlation_id: str = "CORR-PHASE3-0001",
    alert_type: AlertType = AlertType.AUTH_BRUTE_FORCE,
    severity: Severity = Severity.HIGH,
    case_status: CaseStatus = CaseStatus.INVESTIGATING,
) -> CaseState:
    """
    Cria um CaseState válido para testes da orquestração.
    """

    alert = create_test_alert(
        alert_id="ALT-PHASE3-0001",
        correlation_id=correlation_id,
        alert_type=alert_type,
        severity=severity,
    )

    case = CaseState(
        case_id=case_id,
        correlation_id=correlation_id,
        alert=alert,
    )

    case.workflow.case_status = case_status

    return case


def create_request(
    agent_id: str,
    case_snapshot: dict | None = None,
    input_payload: dict | None = None,
    step_number: int = 1,
    max_steps: int = 20,
    retry_count: int = 0,
    max_retries: int = 2,
) -> AgentExecutionRequest:
    """
    Cria um AgentExecutionRequest controlado.
    """

    return AgentExecutionRequest(
        execution_id="EXEC-PHASE3-0001",
        agent_id=agent_id,
        case_id="CASE-PHASE3-0001",
        correlation_id="CORR-PHASE3-0001",
        case_version=1,
        runtime=AgentRuntimeContext(
            step_number=step_number,
            max_steps=max_steps,
            retry_count=retry_count,
            max_retries=max_retries,
            timeout_seconds=30,
        ),
        case_snapshot=case_snapshot or {},
        input_payload=input_payload or {},
    )


def create_supervisor_snapshot(
    case_status: str,
    pending_agents: list[str] | None = None,
    completed_agents: list[str] | None = None,
    failed_agents: list[str] | None = None,
    step_count: int = 0,
    max_steps: int = 20,
) -> dict:
    """
    Cria snapshot mínimo aceito pelo AG-01.
    """

    return {
        "case_id": "CASE-PHASE3-0001",
        "case_status": case_status,
        "workflow": {
            "pending_agents": pending_agents or [],
            "completed_agents": completed_agents or [],
            "failed_agents": failed_agents or [],
            "step_count": step_count,
            "max_steps": max_steps,
        },
    }


def test_phase3_catalog_contains_12_official_agents() -> None:
    """
    O catálogo oficial deve conter exatamente os 12 agentes.
    """

    expected = {
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

    assert len(OFFICIAL_AGENT_IDS) == 12
    assert set(OFFICIAL_AGENT_IDS) == expected


def test_all_12_agents_register_successfully() -> None:
    """
    Todos os agentes implementados devem ser aceitos pelo Registry.
    """

    registry = AgentRegistry()

    for agent_class in AGENT_CLASSES:
        registry.register(
            agent_class()
        )

    assert registry.registered_count() == 12

    assert set(
        registry.registered_ids()
    ) == set(
        OFFICIAL_AGENT_IDS
    )

    assert registry.missing_official_agents() == ()


def test_registry_rejects_duplicate_agent() -> None:
    """
    O mesmo agent_id não pode ser registrado duas vezes.
    """

    registry = AgentRegistry()

    registry.register(
        SOCSupervisorAgent()
    )

    with pytest.raises(
        ValueError,
        match="já registrado",
    ):
        registry.register(
            SOCSupervisorAgent()
        )


def test_runtime_fails_closed_for_unregistered_agent() -> None:
    """
    Runtime deve retornar FAILED se o agente não estiver registrado.
    """

    registry = AgentRegistry()

    runtime = AgentRuntime(
        registry
    )

    request = create_request(
        agent_id="AG-01",
    )

    result = runtime.execute(
        request
    )

    assert result.status == AgentStatus.FAILED
    assert result.success is False
    assert result.error is not None

    assert (
        "Runtime recusou a execução"
        in result.error
    )


def test_execution_request_payload_is_immutable() -> None:
    """
    input_payload não pode ser alterado depois da criação.
    """

    request = create_request(
        agent_id="AG-01",
        input_payload={
            "value": "original",
        },
    )

    with pytest.raises(TypeError):
        request.input_payload[
            "value"
        ] = "altered"


def test_base_agent_blocks_step_limit_exceeded() -> None:
    """
    BaseAgent deve impedir execução acima de max_steps.
    """

    agent = SOCSupervisorAgent()

    request = create_request(
        agent_id="AG-01",
        step_number=21,
        max_steps=20,
    )

    result = agent.execute(
        request
    )

    assert result.status == AgentStatus.FAILED
    assert result.success is False
    assert result.error is not None

    assert (
        "Limite máximo de passos excedido"
        in result.error
    )


def test_base_agent_blocks_retry_limit_exceeded() -> None:
    """
    BaseAgent deve impedir retries acima do limite.
    """

    agent = SOCSupervisorAgent()

    request = create_request(
        agent_id="AG-01",
        retry_count=3,
        max_retries=2,
    )

    result = agent.execute(
        request
    )

    assert result.status == AgentStatus.FAILED
    assert result.success is False
    assert result.error is not None

    assert (
        "Limite máximo de retries excedido"
        in result.error
    )


def test_alert_intake_bootstrap_creates_case() -> None:
    """
    AG-02 deve normalizar o alerta e criar CaseState.
    """

    registry = AgentRegistry()

    registry.register(
        AlertIntakeAgent()
    )

    orchestrator = SOCOrchestrator(
        AgentRuntime(registry)
    )

    raw_alert = {
        "alert_id": "ALT-BOOT-0001",
        "source": {
            "system": "SIEM",
            "product": "Lab-SIEM",
            "rule_name": "Brute Force Test",
        },
        "event": {
            "event_type": "AUTH_BRUTE_FORCE",
            "category": "authentication",
            "message": (
                "Múltiplas falhas de autenticação "
                "detectadas no laboratório."
            ),
            "raw_event": {
                "username": "lab.user",
                "source_ip": "203.0.113.10",
            },
        },
        "initial_severity": "HIGH",
    }

    case, result = (
        orchestrator.bootstrap_case(
            raw_alert=raw_alert,
            case_id="CASE-BOOT-0001",
            correlation_id="CORR-BOOT-0001",
        )
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert case is not None

    assert (
        case.alert.alert_id
        == "ALT-BOOT-0001"
    )

    assert (
        case.alert.event.event_type
        == AlertType.AUTH_BRUTE_FORCE
    )

    assert (
        case.workflow.case_status
        == CaseStatus.TRIAGING
    )

    assert (
        case.workflow.completed_agents
        == ["AG-02"]
    )

    assert (
        case.workflow.step_count
        == 1
    )


def test_alert_intake_bootstrap_failure_creates_no_case() -> None:
    """
    Alerta bruto inválido não deve gerar CaseState.
    """

    registry = AgentRegistry()

    registry.register(
        AlertIntakeAgent()
    )

    orchestrator = SOCOrchestrator(
        AgentRuntime(registry)
    )

    raw_alert = {
        "source": {
            "system": "SIEM",
        },
        "initial_severity": "HIGH",
    }

    case, result = (
        orchestrator.bootstrap_case(
            raw_alert=raw_alert,
            case_id="CASE-BOOT-FAIL-0001",
            correlation_id=(
                "CORR-BOOT-FAIL-0001"
            ),
        )
    )

    assert case is None

    assert (
        result.status
        == AgentStatus.FAILED
    )

    assert result.success is False
    assert result.error is not None


def test_supervisor_routes_first_pending_agent() -> None:
    """
    AG-01 integrado deve selecionar o primeiro agente pendente.
    """

    registry = AgentRegistry()

    registry.register(
        SOCSupervisorAgent()
    )

    orchestrator = SOCOrchestrator(
        AgentRuntime(registry)
    )

    case = create_test_case(
        case_status=CaseStatus.ENRICHING,
    )

    case.workflow.pending_agents = [
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-08",
    ]

    case.workflow.completed_agents = [
        "AG-02",
        "AG-03",
    ]

    case.workflow.step_count = 2

    result = orchestrator.execute_agent(
        case_state=case,
        agent_id="AG-01",
        input_payload={},
    )

    supervisor_result = (
        result.output[
            "supervisor_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        supervisor_result[
            "next_agent_id"
        ]
        == "AG-04"
    )

    assert (
        supervisor_result[
            "should_continue"
        ]
        is True
    )

    assert (
        supervisor_result[
            "routing_source"
        ]
        == "PENDING_AGENTS"
    )

    assert (
        case.workflow.pending_agents
        == [
            "AG-04",
            "AG-05",
            "AG-06",
            "AG-08",
        ]
    )

    assert (
        "AG-01"
        in case.workflow.completed_agents
    )

    assert case.workflow.step_count == 2


def test_supervisor_stops_final_case() -> None:
    """
    AG-01 não deve continuar um caso já encerrado.
    """

    registry = AgentRegistry()

    registry.register(
        SOCSupervisorAgent()
    )

    orchestrator = SOCOrchestrator(
        AgentRuntime(registry)
    )

    case = create_test_case(
        case_status=CaseStatus.CLOSED_N1,
    )

    case.workflow.pending_agents = []

    case.workflow.completed_agents = [
        "AG-02",
        "AG-03",
        "AG-09",
        "AG-10",
        "AG-11",
        "AG-12",
    ]

    case.workflow.step_count = 6

    result = orchestrator.execute_agent(
        case_state=case,
        agent_id="AG-01",
        input_payload={},
    )

    supervisor_result = (
        result.output[
            "supervisor_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        supervisor_result[
            "next_agent_id"
        ]
        is None
    )

    assert (
        supervisor_result[
            "should_continue"
        ]
        is False
    )

    assert (
        supervisor_result[
            "routing_source"
        ]
        == "FINAL_CASE_STATUS"
    )

    assert (
        case.workflow.case_status
        == CaseStatus.CLOSED_N1
    )

    assert (
        case.workflow.pending_agents
        == []
    )

    assert (
        "AG-01"
        in case.workflow.completed_agents
    )


def test_supervisor_routes_max_steps_to_ag12() -> None:
    """
    Supervisor deve enviar o caso ao AG-12
    quando o limite operacional for atingido.
    """

    agent = SOCSupervisorAgent()

    snapshot = create_supervisor_snapshot(
        case_status="INVESTIGATING",
        completed_agents=[
            "AG-02",
            "AG-03",
            "AG-09",
        ],
        step_count=20,
        max_steps=20,
    )

    request = create_request(
        agent_id="AG-01",
        case_snapshot=snapshot,
        step_number=20,
        max_steps=20,
    )

    result = agent.execute(
        request
    )

    supervisor_result = (
        result.output[
            "supervisor_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        supervisor_result[
            "next_agent_id"
        ]
        == "AG-12"
    )

    assert (
        supervisor_result[
            "routing_source"
        ]
        == "MAX_STEPS_GUARDRAIL"
    )


def test_supervisor_unknown_state_fails_closed() -> None:
    """
    Estado desconhecido deve seguir para AG-12.
    """

    agent = SOCSupervisorAgent()

    snapshot = create_supervisor_snapshot(
        case_status="UNKNOWN_STATE",
        completed_agents=[
            "AG-02",
            "AG-03",
        ],
    )

    request = create_request(
        agent_id="AG-01",
        case_snapshot=snapshot,
    )

    result = agent.execute(
        request
    )

    supervisor_result = (
        result.output[
            "supervisor_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        supervisor_result[
            "next_agent_id"
        ]
        == "AG-12"
    )

    assert (
        supervisor_result[
            "routing_source"
        ]
        == "FAIL_CLOSED"
    )


def test_phishing_agent_defensive_analysis() -> None:
    """
    AG-07 deve analisar somente metadados defensivos recebidos.
    """

    agent = PhishingAnalystAgent()

    snapshot = {
        "alert": {
            "alert_id": "ALT-PHISH-P3-0001",
            "event": {
                "event_type": "PHISHING",
            },
        },
    }

    payload = {
        "sender": "sender@example.invalid",
        "recipients": [
            "user@example.invalid",
        ],
        "subject": "Mensagem simulada",
        "urls": [
            "https://example.invalid/login",
        ],
        "attachment_names": [
            "documento-simulado.pdf",
        ],
        "attachment_hashes": [],
        "authentication": {
            "spf": "fail",
            "dkim": "fail",
            "dmarc": "fail",
        },
        "suspicious_indicators": [
            "authentication_failed",
            "suspicious_url",
        ],
        "evidence_references": [
            "EVID-PHISH-P3-0001",
        ],
        "classification": "SUSPICIOUS",
        "severity": "HIGH",
        "confidence": 95,
        "summary": (
            "Metadados simulados apresentam "
            "indicadores consistentes com phishing."
        ),
    }

    request = create_request(
        agent_id="AG-07",
        case_snapshot=snapshot,
        input_payload=payload,
    )

    result = agent.execute(
        request
    )

    phishing_result = (
        result.output[
            "phishing_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        phishing_result[
            "alert_id"
        ]
        == "ALT-PHISH-P3-0001"
    )

    assert (
        phishing_result[
            "classification"
        ]
        == "SUSPICIOUS"
    )

    assert (
        phishing_result[
            "severity"
        ]
        == "HIGH"
    )

    assert (
        phishing_result[
            "confidence"
        ]
        == 95
    )

    assert (
        phishing_result[
            "authentication"
        ][
            "spf"
        ]
        == "fail"
    )


def test_phishing_agent_rejects_non_phishing_alert() -> None:
    """
    AG-07 deve recusar alerta que não seja PHISHING.
    """

    agent = PhishingAnalystAgent()

    snapshot = {
        "alert": {
            "alert_id": "ALT-NON-PHISH-0001",
            "event": {
                "event_type": (
                    "SUSPICIOUS_LOGIN"
                ),
            },
        },
    }

    request = create_request(
        agent_id="AG-07",
        case_snapshot=snapshot,
        input_payload={
            "classification": "SUSPICIOUS",
            "severity": "MEDIUM",
            "confidence": 80,
            "summary": "Teste controlado.",
        },
    )

    result = agent.execute(
        request
    )

    assert result.status == AgentStatus.FAILED
    assert result.success is False
    assert result.error is not None

    assert (
        "somente pode analisar alertas "
        "do tipo PHISHING"
        in result.error
    )


def test_phishing_agent_tool_allowlist() -> None:
    """
    AG-07 deve permitir somente as ferramentas
    oficiais de Email / Phishing autorizadas.
    """

    agent = PhishingAnalystAgent()

    assert (
        agent.can_use_tool(
            "email.get_message_metadata"
        )
        is True
    )

    assert (
        agent.can_use_tool(
            "email.get_headers"
        )
        is True
    )

    assert (
        agent.can_use_tool(
            "email.get_authentication_results"
        )
        is True
    )

    assert (
        agent.can_use_tool(
            "email.get_attachment_metadata"
        )
        is True
    )

    assert (
        agent.can_use_tool(
            "email.open_url"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "email.execute_attachment"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "email.download_attachment"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "read_email_metadata"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "read_email_authentication"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "read_attachment_metadata"
        )
        is False
    )


def test_escalation_confirmed_incident_goes_to_n2() -> None:
    """
    Incidente confirmado e crítico deve escalar para N2.
    """

    agent = EscalationAgent()

    snapshot = {
        "alert": {
            "alert_id": "ALT-ESC-P3-0001",
            "event": {
                "event_type": (
                    "SUSPICIOUS_LOGIN"
                ),
            },
        },
        "investigation": {
            "investigation_id": (
                "INV-ESC-P3-0001"
            ),
            "classification": (
                "CONFIRMED_INCIDENT"
            ),
            "final_severity": "CRITICAL",
            "final_confidence": 98,
            "gaps": [],
            "evidence_references": [
                "EVID-ESC-P3-0001",
            ],
        },
        "qa": {
            "qa_id": "QA-ESC-P3-0001",
            "status": "APPROVED",
            "reviewed_severity": "CRITICAL",
            "reviewed_confidence": 98,
        },
        "identities": [],
        "assets": [],
        "threat_intel": None,
    }

    request = create_request(
        agent_id="AG-12",
        case_snapshot=snapshot,
    )

    result = agent.execute(
        request
    )

    escalation_result = (
        result.output[
            "escalation_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        escalation_result[
            "decision"
        ]
        == "ESCALATED_N2"
    )

    assert (
        "CONFIRMED_INCIDENT"
        in escalation_result[
            "hard_rules_triggered"
        ]
    )

    assert (
        "CRITICAL_SEVERITY"
        in escalation_result[
            "hard_rules_triggered"
        ]
    )

    assert (
        escalation_result[
            "human_approval_required"
        ]
        is True
    )


def test_escalation_false_positive_can_close_n1() -> None:
    """
    Falso positivo aprovado, baixa severidade e alta
    confiança pode ser fechado automaticamente pelo N1.
    """

    agent = EscalationAgent()

    snapshot = {
        "alert": {
            "alert_id": "ALT-CLOSE-P3-0001",
            "event": {
                "event_type": (
                    "SUSPICIOUS_LOGIN"
                ),
            },
        },
        "investigation": {
            "investigation_id": (
                "INV-CLOSE-P3-0001"
            ),
            "classification": (
                "FALSE_POSITIVE"
            ),
            "final_severity": "LOW",
            "final_confidence": 96,
            "gaps": [],
            "evidence_references": [
                "EVID-CLOSE-P3-0001",
            ],
        },
        "qa": {
            "qa_id": "QA-CLOSE-P3-0001",
            "status": "APPROVED",
            "reviewed_severity": "LOW",
            "reviewed_confidence": 96,
        },
        "identities": [],
        "assets": [],
        "threat_intel": None,
    }

    request = create_request(
        agent_id="AG-12",
        case_snapshot=snapshot,
    )

    result = agent.execute(
        request
    )

    escalation_result = (
        result.output[
            "escalation_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        escalation_result[
            "decision"
        ]
        == "CLOSED_N1"
    )

    assert (
        escalation_result[
            "hard_rules_triggered"
        ]
        == ()
    )

    assert (
        escalation_result[
            "human_approval_required"
        ]
        is False
    )


def test_escalation_suspicious_case_waits_for_human() -> None:
    """
    Caso suspeito sem hard rule e com confiança insuficiente
    não deve ser fechado automaticamente.
    """

    agent = EscalationAgent()

    snapshot = {
        "alert": {
            "alert_id": "ALT-HUMAN-P3-0001",
            "event": {
                "event_type": (
                    "SUSPICIOUS_LOGIN"
                ),
            },
        },
        "investigation": {
            "investigation_id": (
                "INV-HUMAN-P3-0001"
            ),
            "classification": "SUSPICIOUS",
            "final_severity": "MEDIUM",
            "final_confidence": 88,
            "gaps": [],
            "evidence_references": [
                "EVID-HUMAN-P3-0001",
            ],
        },
        "qa": {
            "qa_id": "QA-HUMAN-P3-0001",
            "status": "APPROVED",
            "reviewed_severity": "MEDIUM",
            "reviewed_confidence": 88,
        },
        "identities": [],
        "assets": [],
        "threat_intel": None,
    }

    request = create_request(
        agent_id="AG-12",
        case_snapshot=snapshot,
    )

    result = agent.execute(
        request
    )

    escalation_result = (
        result.output[
            "escalation_result"
        ]
    )

    assert result.status == AgentStatus.COMPLETED
    assert result.success is True

    assert (
        escalation_result[
            "decision"
        ]
        == "WAITING_HUMAN"
    )

    assert (
        escalation_result[
            "human_approval_required"
        ]
        is True
    )