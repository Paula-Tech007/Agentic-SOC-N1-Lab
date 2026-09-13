"""
Testes automatizados da Fase 2 do Agentic SOC N1 Lab.

Estes testes validam:

- schemas;
- enums;
- limites de confidence;
- imutabilidade das evidências;
- imutabilidade do raw_event;
- análise de phishing;
- Knowledge / RAG com fonte obrigatória;
- eventos de auditoria imutáveis;
- integridade do CaseState;
- prevenção de evidência duplicada;
- prevenção de auditoria duplicada;
- versionamento do estado;
- serialização JSON;
- persistência SQLite;
- persistência SQLite da auditoria;
- workflow dos agentes;
- QA;
- escalonamento.
"""

import pytest
from pydantic import ValidationError

from core.schemas import (
    AgentExecutionState,
    AgentStatus,
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    CaseStatus,
    EscalationResult,
    Evidence,
    EvidenceType,
    FinalClassification,
    FinalDecision,
    IndicatorType,
    IOC,
    QAResult,
    QAStatus,
    Severity,
    WorkflowState,
)
from core.state import (
    CaseState,
    case_exists_sqlite,
    deserialize_case_state,
    load_case_state_sqlite,
    save_case_state_sqlite,
    serialize_case_state,
)


def create_test_alert(
    alert_id: str = "ALT-TEST-0001",
    correlation_id: str = "CORR-TEST-0001",
) -> Alert:
    """
    Cria um alerta padrão utilizado pelos testes.
    """

    return Alert(
        alert_id=alert_id,
        correlation_id=correlation_id,
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name="Test Rule",
        ),
        event=AlertEvent(
            event_type=AlertType.SUSPICIOUS_LOGIN,
            category="authentication",
            message="Suspicious login detected",
            raw_event={
                "username": "test.user",
                "source_ip": "185.10.20.30",
            },
        ),
        initial_severity=Severity.HIGH,
    )


def create_test_evidence(
    evidence_id: str = "EVID-TEST-0001",
) -> Evidence:
    """
    Cria uma evidência padrão utilizada pelos testes.
    """

    return Evidence(
        evidence_id=evidence_id,
        evidence_type=EvidenceType.THREAT_INTELLIGENCE,
        title="IOC reputation",
        description="Threat Intelligence returned a malicious reputation.",
        source_agent="AG-04",
        source_tool="lookup_ip",
        source_system="Lab-Threat-Intel",
        verified=True,
        confidence=95,
        data={
            "ip": "185.10.20.30",
            "reputation": "malicious",
        },
        references=[
            "IOC-TEST-0001",
            "ALT-TEST-0001",
        ],
    )


def create_test_case() -> CaseState:
    """
    Cria um CaseState válido para os testes.
    """

    alert = create_test_alert()

    ioc = IOC(
        ioc_id="IOC-TEST-0001",
        indicator_type=IndicatorType.IP,
        value="185.10.20.30",
        source="Lab-Threat-Intel",
        confidence=95,
        malicious_confirmed=True,
        reputation="malicious",
    )

    workflow = WorkflowState(
        case_status=CaseStatus.INVESTIGATING,
    )

    return CaseState(
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        alert=alert,
        iocs=[ioc],
        workflow=workflow,
    )


def test_alert_schema_creation() -> None:
    """
    Um alerta válido deve ser criado corretamente.
    """

    alert = create_test_alert()

    assert alert.alert_id == "ALT-TEST-0001"
    assert alert.correlation_id == "CORR-TEST-0001"
    assert alert.event.event_type == AlertType.SUSPICIOUS_LOGIN
    assert alert.initial_severity == Severity.HIGH


def test_ioc_rejects_invalid_confidence() -> None:
    """
    Confidence maior que 100 deve ser rejeitado.
    """

    with pytest.raises(ValidationError):
        IOC(
            ioc_id="IOC-INVALID",
            indicator_type=IndicatorType.IP,
            value="185.10.20.30",
            confidence=150,
        )


def test_evidence_is_frozen() -> None:
    """
    Uma evidência criada não pode ser alterada diretamente.
    """

    evidence = create_test_evidence()

    with pytest.raises(ValidationError):
        evidence.title = "Altered evidence"


def test_case_state_rejects_wrong_correlation() -> None:
    """
    CaseState e Alert precisam possuir o mesmo correlation_id.
    """

    alert = create_test_alert(
        correlation_id="CORR-ALERT-0001",
    )

    with pytest.raises(
        ValidationError,
        match="correlation_id",
    ):
        CaseState(
            case_id="CASE-INVALID",
            correlation_id="CORR-CASE-9999",
            alert=alert,
        )


def test_case_state_add_evidence_increases_version() -> None:
    """
    Adicionar uma evidência deve aumentar a versão do caso.
    """

    case = create_test_case()

    assert case.version == 1

    evidence = create_test_evidence()

    case.add_evidence(evidence)

    assert case.version == 2
    assert len(case.evidence) == 1
    assert case.evidence[0].evidence_id == "EVID-TEST-0001"


def test_case_state_rejects_duplicate_evidence() -> None:
    """
    O mesmo evidence_id não pode ser inserido duas vezes.
    """

    case = create_test_case()

    evidence = create_test_evidence()

    case.add_evidence(evidence)

    with pytest.raises(
        ValueError,
        match="Evidência duplicada",
    ):
        case.add_evidence(evidence)


def test_json_roundtrip() -> None:
    """
    CaseState deve sobreviver a serialização e desserialização.
    """

    case = create_test_case()

    case.add_evidence(
        create_test_evidence()
    )

    json_data = serialize_case_state(case)

    restored = deserialize_case_state(
        json_data
    )

    assert isinstance(restored, CaseState)

    assert restored.case_id == case.case_id
    assert restored.correlation_id == case.correlation_id
    assert restored.alert.alert_id == case.alert.alert_id
    assert restored.iocs[0].value == "185.10.20.30"
    assert restored.evidence[0].evidence_id == "EVID-TEST-0001"


def test_workflow_agent_states() -> None:
    """
    Workflow deve preservar corretamente os estados dos agentes.
    """

    workflow = WorkflowState(
        case_status=CaseStatus.INVESTIGATING,
        current_agent="AG-05",
        agents={
            "AG-03": AgentExecutionState(
                agent_id="AG-03",
                agent_name="Triage Analyst",
                status=AgentStatus.COMPLETED,
            ),
            "AG-05": AgentExecutionState(
                agent_id="AG-05",
                agent_name="Identity Analyst",
                status=AgentStatus.RUNNING,
            ),
            "AG-07": AgentExecutionState(
                agent_id="AG-07",
                agent_name="Phishing Analyst",
                status=AgentStatus.SKIPPED,
            ),
        },
        completed_agents=[
            "AG-03",
        ],
        skipped_agents=[
            "AG-07",
        ],
    )

    assert workflow.case_status == CaseStatus.INVESTIGATING

    assert (
        workflow.agents["AG-03"].status
        == AgentStatus.COMPLETED
    )

    assert (
        workflow.agents["AG-05"].status
        == AgentStatus.RUNNING
    )

    assert (
        workflow.agents["AG-07"].status
        == AgentStatus.SKIPPED
    )


def test_qa_retry_result() -> None:
    """
    QA rejeitado deve conseguir indicar retry.
    """

    qa = QAResult(
        qa_id="QA-TEST-0001",
        investigation_id="INV-TEST-0001",
        status=QAStatus.REJECTED,
        issues=[
            "Missing authentication result.",
        ],
        missing_evidence=[
            "Authentication result after failed logins.",
        ],
        reviewed_severity=Severity.HIGH,
        reviewed_confidence=80,
        retry_required=True,
        retry_targets=[
            "AG-05",
        ],
    )

    assert qa.status == QAStatus.REJECTED
    assert qa.retry_required is True
    assert "AG-05" in qa.retry_targets


def test_escalation_result() -> None:
    """
    Escalonamento N2 deve preservar classificação e hard rules.
    """

    result = EscalationResult(
        escalation_id="ESC-TEST-0001",
        alert_id="ALT-TEST-0001",
        investigation_id="INV-TEST-0001",
        qa_id="QA-TEST-0001",
        decision=FinalDecision.ESCALATED_N2,
        classification=FinalClassification.CONFIRMED_INCIDENT,
        severity=Severity.CRITICAL,
        confidence=96,
        reason=(
            "Critical asset and privileged account "
            "associated with confirmed malicious IOC."
        ),
        hard_rules_triggered=[
            "HR-CRITICAL-ASSET-001",
            "HR-PRIVILEGED-ACCOUNT-001",
        ],
        evidence_references=[
            "EVID-TEST-0001",
        ],
        human_approval_required=False,
        recommended_next_step=(
            "Escalate case to SOC N2."
        ),
    )

    assert result.decision == FinalDecision.ESCALATED_N2

    assert (
        result.classification
        == FinalClassification.CONFIRMED_INCIDENT
    )

    assert result.severity == Severity.CRITICAL

    assert "HR-CRITICAL-ASSET-001" in result.hard_rules_triggered


def test_sqlite_roundtrip(tmp_path) -> None:
    """
    CaseState deve ser salvo e recuperado do SQLite.
    """

    database_path = (
        tmp_path
        / "phase2_test.db"
    )

    case = create_test_case()

    case.add_evidence(
        create_test_evidence()
    )

    save_case_state_sqlite(
        case_state=case,
        database_path=database_path,
    )

    assert case_exists_sqlite(
        case_id=case.case_id,
        database_path=database_path,
    )

    restored = load_case_state_sqlite(
        case_id=case.case_id,
        database_path=database_path,
    )

    assert isinstance(restored, CaseState)

    assert restored.case_id == case.case_id

    assert (
        restored.workflow.case_status
        == CaseStatus.INVESTIGATING
    )

    assert restored.iocs[0].value == "185.10.20.30"

    assert (
        restored.evidence[0].evidence_id
        == "EVID-TEST-0001"
    )


def test_extra_fields_are_rejected() -> None:
    """
    Campos não previstos pelo schema devem ser rejeitados.
    """

    with pytest.raises(ValidationError):
        AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            unknown_field="not-allowed",
        )


def test_raw_event_is_immutable() -> None:
    """
    O raw_event original não pode ser alterado após criação.
    """

    event = AlertEvent(
        event_type=AlertType.SUSPICIOUS_LOGIN,
        message="Suspicious login detected",
        raw_event={
            "username": "admin",
            "details": {
                "attempts": [1, 2, 3],
            },
        },
    )

    with pytest.raises(TypeError):
        event.raw_event["username"] = "changed"

    assert (
        event.raw_event["details"]["attempts"]
        == (1, 2, 3)
    )


def test_phishing_schema_creation() -> None:
    """
    O resultado de phishing deve preservar análise e evidências.
    """

    from core.schemas import (
        EmailAuthenticationResult,
        PhishingResult,
    )

    result = PhishingResult(
        phishing_id="PHISH-TEST-0001",
        alert_id="ALT-TEST-0001",
        sender="sender@example.test",
        recipients=[
            "user@empresa.local",
        ],
        subject="Atualizacao urgente",
        urls=[
            "https://example.test/login",
        ],
        authentication=EmailAuthenticationResult(
            spf="fail",
            dkim="fail",
            dmarc="fail",
        ),
        suspicious_indicators=[
            "authentication_failed",
            "suspicious_url",
        ],
        evidence_references=[
            "EVID-TEST-0001",
        ],
        classification=FinalClassification.SUSPICIOUS,
        severity=Severity.HIGH,
        confidence=94,
        summary="Indicadores consistentes com phishing.",
    )

    assert result.phishing_id == "PHISH-TEST-0001"
    assert result.confidence == 94
    assert result.authentication.spf == "fail"
    assert result.classification == FinalClassification.SUSPICIOUS


def test_knowledge_requires_source() -> None:
    """
    KnowledgeResult não pode existir sem fonte recuperada.
    """

    from core.schemas import KnowledgeResult

    with pytest.raises(ValidationError):
        KnowledgeResult(
            knowledge_id="KNOW-INVALID",
            alert_id="ALT-TEST-0001",
            query="Como investigar o alerta?",
            answer="Resposta sem fonte.",
            retrieved_chunks=[],
            confidence=90,
        )


def test_audit_event_is_immutable() -> None:
    """
    AuditEvent não pode ser alterado depois de criado.
    """

    from core.schemas import AuditEvent

    audit = AuditEvent(
        audit_id="AUDIT-IMMUTABLE-0001",
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        event_type="CASE_CREATED",
        actor_type="SYSTEM",
        actor_id="orchestrator",
        action="create_case",
    )

    with pytest.raises(ValidationError):
        audit.status = "FAILED"


def test_audit_payload_is_immutable() -> None:
    """
    O payload interno da auditoria também deve ser imutável.
    """

    from core.schemas import AuditEvent

    audit = AuditEvent(
        audit_id="AUDIT-PAYLOAD-0001",
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        event_type="TOOL_CALLED",
        actor_type="AGENT",
        actor_id="AG-04",
        action="lookup_ip",
        payload={
            "ip": "185.10.20.30",
        },
    )

    with pytest.raises(TypeError):
        audit.payload["ip"] = "8.8.8.8"


def test_case_state_supports_phishing_knowledge_and_audit() -> None:
    """
    CaseState deve consolidar phishing, knowledge e auditoria.
    """

    from core.schemas import (
        AuditEvent,
        EmailAuthenticationResult,
        KnowledgeChunk,
        KnowledgeResult,
        PhishingResult,
    )

    alert = Alert(
        alert_id="ALT-ADHERENCE-0001",
        correlation_id="CORR-ADHERENCE-0001",
        source=AlertSource(
            system="SIEM",
        ),
        event=AlertEvent(
            event_type=AlertType.PHISHING,
            message="Phishing detected",
            raw_event={
                "sender": "attacker@example.test",
            },
        ),
        initial_severity=Severity.HIGH,
    )

    phishing = PhishingResult(
        phishing_id="PHISH-ADHERENCE-0001",
        alert_id="ALT-ADHERENCE-0001",
        sender="attacker@example.test",
        authentication=EmailAuthenticationResult(
            spf="fail",
            dkim="fail",
            dmarc="fail",
        ),
        classification=FinalClassification.SUSPICIOUS,
        severity=Severity.HIGH,
        confidence=94,
        summary="Indicadores consistentes com phishing.",
    )

    knowledge = KnowledgeResult(
        knowledge_id="KNOW-ADHERENCE-0001",
        alert_id="ALT-ADHERENCE-0001",
        query="Como tratar phishing?",
        answer="Seguir o playbook corporativo.",
        retrieved_chunks=[
            KnowledgeChunk(
                chunk_id="CHUNK-ADHERENCE-0001",
                document_name="Playbook Phishing",
                document_type="playbook",
                content=(
                    "Validar remetente, URLs, anexos "
                    "e autenticacao."
                ),
                similarity_score=0.95,
            ),
        ],
        confidence=95,
    )

    case = CaseState(
        case_id="CASE-ADHERENCE-0001",
        correlation_id="CORR-ADHERENCE-0001",
        alert=alert,
        phishing=phishing,
        knowledge=knowledge,
    )

    audit = AuditEvent(
        audit_id="AUDIT-ADHERENCE-0001",
        case_id="CASE-ADHERENCE-0001",
        correlation_id="CORR-ADHERENCE-0001",
        event_type="CASE_UPDATED",
        actor_type="SYSTEM",
        actor_id="orchestrator",
        action="update_case",
    )

    case.add_audit_event(audit)

    assert case.phishing is not None
    assert case.knowledge is not None
    assert case.phishing.phishing_id == "PHISH-ADHERENCE-0001"
    assert case.knowledge.knowledge_id == "KNOW-ADHERENCE-0001"
    assert case.audit[0].audit_id == "AUDIT-ADHERENCE-0001"
    assert case.version == 2


def test_case_state_rejects_duplicate_audit() -> None:
    """
    Um audit_id não pode ser adicionado duas vezes ao CaseState.
    """

    from core.schemas import AuditEvent

    case = create_test_case()

    audit = AuditEvent(
        audit_id="AUDIT-DUPLICATE-0001",
        case_id=case.case_id,
        correlation_id=case.correlation_id,
        event_type="TEST",
        actor_type="SYSTEM",
        actor_id="orchestrator",
        action="test",
    )

    case.add_audit_event(audit)

    with pytest.raises(
        ValueError,
        match="Evento de auditoria duplicado",
    ):
        case.add_audit_event(audit)


def test_sqlite_audit_roundtrip(tmp_path) -> None:
    """
    Auditoria deve ser persistida no SQLite sem duplicação.
    """

    from core.schemas import AuditEvent
    from core.state import load_audit_events_sqlite

    database_path = (
        tmp_path
        / "phase2_audit_test.db"
    )

    case = create_test_case()

    audit_1 = AuditEvent(
        audit_id="AUDIT-SQL-TEST-0001",
        case_id=case.case_id,
        correlation_id=case.correlation_id,
        event_type="CASE_CREATED",
        actor_type="SYSTEM",
        actor_id="orchestrator",
        action="create_case",
    )

    audit_2 = AuditEvent(
        audit_id="AUDIT-SQL-TEST-0002",
        case_id=case.case_id,
        correlation_id=case.correlation_id,
        event_type="AGENT_STARTED",
        actor_type="AGENT",
        actor_id="AG-03",
        action="start_triage",
    )

    case.add_audit_event(audit_1)
    case.add_audit_event(audit_2)

    save_case_state_sqlite(
        case_state=case,
        database_path=database_path,
    )

    save_case_state_sqlite(
        case_state=case,
        database_path=database_path,
    )

    audit_events = load_audit_events_sqlite(
        case_id=case.case_id,
        database_path=database_path,
    )

    assert len(audit_events) == 2
    assert audit_events[0].audit_id == "AUDIT-SQL-TEST-0001"
    assert audit_events[1].audit_id == "AUDIT-SQL-TEST-0002"