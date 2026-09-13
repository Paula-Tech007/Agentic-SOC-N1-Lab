"""
Estado central de um caso do Agentic SOC N1 Lab.

O CaseState é a ficha viva da investigação.

Ele reúne os resultados produzidos pelos diferentes
agentes durante o ciclo de vida do caso:

- alerta;
- IOCs;
- identidades;
- ativos;
- evidências;
- triagem;
- threat intelligence;
- phishing;
- conhecimento / RAG;
- investigação;
- QA;
- decisão de escalonamento;
- auditoria;
- workflow.

Evidências e eventos de auditoria são armazenados
como tuplas de registros imutáveis, preservando
o princípio append-only.
"""

from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from core.schemas import (
    Alert,
    AssetContext,
    AuditEvent,
    EscalationResult,
    Evidence,
    IdentityContext,
    IOC,
    InvestigationResult,
    KnowledgeResult,
    PhishingResult,
    QAResult,
    ThreatIntelResult,
    TriageResult,
    WorkflowState,
)


class CaseState(BaseModel):
    """
    Estado completo de um caso dentro do SOC multiagente.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    case_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do caso SOC.",
    )

    correlation_id: str = Field(
        ...,
        min_length=1,
        description="Identificador global utilizado para correlação.",
    )

    alert: Alert = Field(
        ...,
        description="Alerta original que iniciou o caso.",
    )

    iocs: list[IOC] = Field(
        default_factory=list,
        description="Indicadores associados ao caso.",
    )

    identities: list[IdentityContext] = Field(
        default_factory=list,
        description="Identidades relacionadas à investigação.",
    )

    assets: list[AssetContext] = Field(
        default_factory=list,
        description="Ativos relacionados à investigação.",
    )

    evidence: tuple[Evidence, ...] = Field(
        default_factory=tuple,
        description=(
            "Coleção append-only das evidências registradas no caso."
        ),
    )

    triage: TriageResult | None = Field(
        default=None,
        description="Resultado da triagem.",
    )

    threat_intel: ThreatIntelResult | None = Field(
        default=None,
        description="Resultado consolidado de Threat Intelligence.",
    )

    phishing: PhishingResult | None = Field(
        default=None,
        description="Resultado da análise especializada de phishing.",
    )

    knowledge: KnowledgeResult | None = Field(
        default=None,
        description="Resultado de conhecimento / RAG utilizado no caso.",
    )

    investigation: InvestigationResult | None = Field(
        default=None,
        description="Investigação consolidada do caso.",
    )

    qa: QAResult | None = Field(
        default=None,
        description="Resultado mais recente da revisão QA.",
    )

    escalation: EscalationResult | None = Field(
        default=None,
        description="Decisão operacional final, quando disponível.",
    )

    audit: tuple[AuditEvent, ...] = Field(
        default_factory=tuple,
        description=(
            "Histórico append-only de eventos de auditoria."
        ),
    )

    workflow: WorkflowState = Field(
        default_factory=WorkflowState,
        description="Estado operacional do workflow.",
    )

    version: int = Field(
        default=1,
        ge=1,
        description="Versão lógica do estado do caso.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def validate_case_consistency(self) -> "CaseState":
        """
        Garante que resultados, auditoria e correlação pertencem
        ao mesmo caso.
        """

        if self.correlation_id != self.alert.correlation_id:
            raise ValueError(
                "correlation_id do CaseState deve ser igual "
                "ao correlation_id do alerta."
            )

        if self.triage is not None:
            if self.triage.alert_id != self.alert.alert_id:
                raise ValueError(
                    "A triagem não pertence ao alerta deste caso."
                )

        if self.threat_intel is not None:
            if self.threat_intel.alert_id != self.alert.alert_id:
                raise ValueError(
                    "O resultado de Threat Intelligence não pertence "
                    "ao alerta deste caso."
                )

        if self.phishing is not None:
            if self.phishing.alert_id != self.alert.alert_id:
                raise ValueError(
                    "A análise de phishing não pertence "
                    "ao alerta deste caso."
                )

        if self.knowledge is not None:
            if self.knowledge.alert_id != self.alert.alert_id:
                raise ValueError(
                    "O resultado de Knowledge/RAG não pertence "
                    "ao alerta deste caso."
                )

        if self.investigation is not None:
            if self.investigation.alert_id != self.alert.alert_id:
                raise ValueError(
                    "A investigação não pertence ao alerta deste caso."
                )

        if self.escalation is not None:
            if self.escalation.alert_id != self.alert.alert_id:
                raise ValueError(
                    "A decisão de escalonamento não pertence "
                    "ao alerta deste caso."
                )

        for audit_event in self.audit:
            if audit_event.case_id != self.case_id:
                raise ValueError(
                    "Evento de auditoria pertence a outro caso."
                )

            if audit_event.correlation_id != self.correlation_id:
                raise ValueError(
                    "Evento de auditoria possui correlation_id diferente."
                )

        return self

    def add_evidence(self, evidence: Evidence) -> None:
        """
        Adiciona uma evidência sem alterar registros anteriores.

        IDs duplicados são rejeitados.
        """

        existing_ids = {
            item.evidence_id
            for item in self.evidence
        }

        if evidence.evidence_id in existing_ids:
            raise ValueError(
                f"Evidência duplicada: {evidence.evidence_id}"
            )

        self.evidence = (
            *self.evidence,
            evidence,
        )

        self.touch()

    def add_audit_event(
        self,
        audit_event: AuditEvent,
    ) -> None:
        """
        Adiciona um evento de auditoria de forma append-only.

        Eventos anteriores não são sobrescritos.
        IDs duplicados são rejeitados.
        """

        if audit_event.case_id != self.case_id:
            raise ValueError(
                "O evento de auditoria pertence a outro caso."
            )

        if audit_event.correlation_id != self.correlation_id:
            raise ValueError(
                "O correlation_id do evento de auditoria "
                "não corresponde ao caso."
            )

        existing_ids = {
            item.audit_id
            for item in self.audit
        }

        if audit_event.audit_id in existing_ids:
            raise ValueError(
                f"Evento de auditoria duplicado: "
                f"{audit_event.audit_id}"
            )

        self.audit = (
            *self.audit,
            audit_event,
        )

        self.touch()

    def touch(self) -> None:
        """
        Atualiza versão e timestamp do CaseState.
        """

        self.version += 1
        self.updated_at = datetime.now(timezone.utc)