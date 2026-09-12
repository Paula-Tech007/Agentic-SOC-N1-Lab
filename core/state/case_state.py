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
- investigação;
- QA;
- decisão de escalonamento;
- workflow.

As evidências são armazenadas como uma tupla de registros
imutáveis, ajudando a preservar o princípio append-only.
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
    EscalationResult,
    Evidence,
    IdentityContext,
    IOC,
    InvestigationResult,
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
        Garante que os principais resultados pertencem ao
        mesmo alerta e à mesma correlação.
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

        return self

    def add_evidence(self, evidence: Evidence) -> None:
        """
        Adiciona uma nova evidência sem alterar registros anteriores.

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

        self.evidence = (*self.evidence, evidence)
        self.touch()

    def touch(self) -> None:
        """
        Atualiza versão e timestamp do CaseState.
        """

        self.version += 1
        self.updated_at = datetime.now(timezone.utc)