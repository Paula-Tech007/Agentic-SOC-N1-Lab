"""
AG-12 — Escalation Agent.

Responsável por aplicar as hard rules do Agentic SOC N1 Lab
e produzir a decisão final de escalonamento.

Fluxo:

CaseState
    ↓
AG-12 Escalation
    ↓
Hard Rules
    ↓
EscalationResult
    ↓
CLOSED_N1
ou
ESCALATED_N2
ou
WAITING_HUMAN

Princípios:

- decisões são baseadas em dados já consolidados;
- ferramentas e evidências têm prioridade sobre interpretação;
- nenhuma evidência é fabricada;
- nenhuma ação crítica é executada automaticamente;
- casos críticos são escalados;
- fechamento automático N1 é conservador;
- na dúvida, o sistema não força fechamento automático.
"""

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)
from core.schemas import (
    FinalClassification,
    FinalDecision,
    QAStatus,
    Severity,
    EscalationResult,
)


class EscalationAgent(BaseAgent):
    """
    AG-12 — Escalation Agent.
    """

    agent_id = "AG-12"

    agent_name = "Escalation Agent"

    description = (
        "Aplicar hard rules e decidir entre fechamento N1, "
        "escalonamento N2 ou espera por decisão humana."
    )

    allowed_tools: tuple[str, ...] = (
        "read_case_context",
        "read_investigation",
        "read_qa",
        "read_identity",
        "read_asset",
        "read_threat_intel",
        "read_evidence",
        "read_audit",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Avalia o caso e produz EscalationResult.
        """

        snapshot = request.case_snapshot.to_dict()

        alert = self._required_mapping(
            snapshot.get("alert"),
            "alert",
        )

        alert_id = self._required_string(
            alert.get("alert_id"),
            "alert.alert_id",
        )

        investigation = self._required_mapping(
            snapshot.get("investigation"),
            "investigation",
        )

        investigation_id = self._required_string(
            investigation.get(
                "investigation_id"
            ),
            "investigation.investigation_id",
        )

        qa = self._required_mapping(
            snapshot.get("qa"),
            "qa",
        )

        qa_id = self._required_string(
            qa.get("qa_id"),
            "qa.qa_id",
        )

        qa_status = self._qa_status(
            qa.get("status")
        )

        classification = (
            self._classification(
                investigation.get(
                    "classification"
                )
            )
        )

        severity = self._severity(
            qa.get(
                "reviewed_severity",
                investigation.get(
                    "final_severity"
                ),
            )
        )

        confidence = self._confidence(
            qa.get(
                "reviewed_confidence",
                investigation.get(
                    "final_confidence"
                ),
            )
        )

        hard_rules = (
            self._evaluate_hard_rules(
                snapshot=snapshot,
                qa_status=qa_status,
                classification=classification,
                severity=severity,
            )
        )

        investigation_gaps = (
            self._string_list(
                investigation.get("gaps")
            )
        )

        evidence_references = (
            self._string_list(
                investigation.get(
                    "evidence_references"
                )
            )
        )

        decision = self._decide(
            qa_status=qa_status,
            classification=classification,
            severity=severity,
            confidence=confidence,
            hard_rules=hard_rules,
            investigation_gaps=(
                investigation_gaps
            ),
        )

        reason = self._build_reason(
            decision=decision,
            qa_status=qa_status,
            classification=classification,
            severity=severity,
            confidence=confidence,
            hard_rules=hard_rules,
            investigation_gaps=(
                investigation_gaps
            ),
        )

        recommended_next_step = (
            self._recommended_next_step(
                decision
            )
        )

        human_approval_required = (
            decision
            != FinalDecision.CLOSED_N1
        )

        escalation_result = (
            EscalationResult(
                escalation_id=(
                    self._create_escalation_id()
                ),
                alert_id=alert_id,
                investigation_id=(
                    investigation_id
                ),
                qa_id=qa_id,
                decision=decision,
                classification=(
                    classification
                ),
                severity=severity,
                confidence=confidence,
                reason=reason,
                hard_rules_triggered=(
                    hard_rules
                ),
                evidence_references=(
                    evidence_references
                ),
                human_approval_required=(
                    human_approval_required
                ),
                recommended_next_step=(
                    recommended_next_step
                ),
            )
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    escalation_result
                    .escalation_id
                ),
                "escalation_result": (
                    escalation_result
                    .model_dump(
                        mode="json"
                    )
                ),
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Hard rules avaliadas "
                    "pelo AG-12."
                ),
                (
                    "Decisão de escalonamento "
                    "produzida de forma "
                    "determinística."
                ),
                (
                    "Nenhuma ação crítica foi "
                    "executada automaticamente."
                ),
            ),
        )

    def _evaluate_hard_rules(
        self,
        snapshot: Mapping[str, Any],
        qa_status: QAStatus,
        classification: FinalClassification,
        severity: Severity,
    ) -> list[str]:
        """
        Avalia hard rules obrigatórias.

        Qualquer regra retornada nesta lista impede
        fechamento automático pelo SOC N1.
        """

        hard_rules: list[str] = []

        alert = self._optional_mapping(
            snapshot.get("alert")
        )

        event = self._optional_mapping(
            alert.get("event")
        )

        event_type = event.get(
            "event_type"
        )

        if (
            event_type
            == "LATERAL_MOVEMENT_SUSPECTED"
        ):
            self._append_unique(
                hard_rules,
                "LATERAL_MOVEMENT_SUSPECTED",
            )

        if (
            event_type
            == "DATA_EXFILTRATION_SUSPECTED"
        ):
            self._append_unique(
                hard_rules,
                "DATA_EXFILTRATION_SUSPECTED",
            )

        if event_type == "UNSUPPORTED":
            self._append_unique(
                hard_rules,
                "UNSUPPORTED_ALERT_TYPE",
            )

        if (
            classification
            == FinalClassification.CONFIRMED_INCIDENT
        ):
            self._append_unique(
                hard_rules,
                "CONFIRMED_INCIDENT",
            )

        if severity == Severity.CRITICAL:
            self._append_unique(
                hard_rules,
                "CRITICAL_SEVERITY",
            )

        triage = self._optional_mapping(
            snapshot.get("triage")
        )

        if (
            triage.get(
                "immediate_escalation"
            )
            is True
        ):
            self._append_unique(
                hard_rules,
                "IMMEDIATE_ESCALATION_TRIAGE",
            )

        identities = self._mapping_list(
            snapshot.get("identities")
        )

        if any(
            identity.get("privileged") is True
            for identity in identities
        ):
            self._append_unique(
                hard_rules,
                "PRIVILEGED_ACCOUNT",
            )

        assets = self._mapping_list(
            snapshot.get("assets")
        )

        if any(
            asset.get("criticality")
            == "CRITICAL"
            for asset in assets
        ):
            self._append_unique(
                hard_rules,
                "CRITICAL_ASSET",
            )

        threat_intel = self._optional_mapping(
            snapshot.get("threat_intel")
        )

        threat_findings = (
            self._mapping_list(
                threat_intel.get("findings")
            )
        )

        if any(
            finding.get(
                "malicious_confirmed"
            )
            is True
            for finding in threat_findings
        ):
            self._append_unique(
                hard_rules,
                "MALICIOUS_IOC_CONFIRMED",
            )

        workflow = self._optional_mapping(
            snapshot.get("workflow")
        )

        retry_count = (
            workflow.get(
                "reflection_retry_count",
                0,
            )
        )

        max_retries = (
            workflow.get(
                "max_reflection_retries",
                2,
            )
        )

        if (
            qa_status == QAStatus.REJECTED
            and isinstance(
                retry_count,
                int,
            )
            and isinstance(
                max_retries,
                int,
            )
            and retry_count > max_retries
        ):
            self._append_unique(
                hard_rules,
                "QA_RETRY_LIMIT_EXCEEDED",
            )

        return hard_rules

    def _decide(
        self,
        qa_status: QAStatus,
        classification: FinalClassification,
        severity: Severity,
        confidence: int,
        hard_rules: list[str],
        investigation_gaps: list[str],
    ) -> FinalDecision:
        """
        Aplica política conservadora de decisão.

        1. Hard rule -> ESCALATED_N2.
        2. Fechamento N1 somente quando:
           - QA aprovado;
           - classificação benigna ou falso positivo;
           - confiança >= 90;
           - severidade até MEDIUM;
           - nenhuma lacuna;
           - nenhuma hard rule.
        3. Qualquer outro caso -> WAITING_HUMAN.
        """

        if hard_rules:
            return (
                FinalDecision.ESCALATED_N2
            )

        auto_close_classifications = {
            FinalClassification.FALSE_POSITIVE,
            FinalClassification.BENIGN_POSITIVE,
        }

        auto_close_severities = {
            Severity.INFORMATIONAL,
            Severity.LOW,
            Severity.MEDIUM,
        }

        if (
            qa_status
            == QAStatus.APPROVED
            and classification
            in auto_close_classifications
            and severity
            in auto_close_severities
            and confidence >= 90
            and not investigation_gaps
        ):
            return (
                FinalDecision.CLOSED_N1
            )

        return (
            FinalDecision.WAITING_HUMAN
        )

    @staticmethod
    def _build_reason(
        decision: FinalDecision,
        qa_status: QAStatus,
        classification: FinalClassification,
        severity: Severity,
        confidence: int,
        hard_rules: list[str],
        investigation_gaps: list[str],
    ) -> str:
        """
        Constrói justificativa auditável.
        """

        if (
            decision
            == FinalDecision.ESCALATED_N2
        ):
            rules = ", ".join(
                hard_rules
            )

            return (
                "Escalonamento obrigatório para N2 "
                "porque uma ou mais hard rules "
                f"foram acionadas: {rules}."
            )

        if (
            decision
            == FinalDecision.CLOSED_N1
        ):
            return (
                "Caso elegível para fechamento N1: "
                "QA aprovado, classificação "
                f"{classification.value}, severidade "
                f"{severity.value}, confiança "
                f"{confidence}, nenhuma lacuna "
                "pendente e nenhuma hard rule."
            )

        details: list[str] = [
            (
                "Os critérios conservadores para "
                "fechamento automático N1 não "
                "foram totalmente atendidos."
            ),
            (
                f"QA={qa_status.value}, "
                f"classificação="
                f"{classification.value}, "
                f"severidade={severity.value}, "
                f"confiança={confidence}."
            ),
        ]

        if investigation_gaps:
            details.append(
                (
                    "Existem lacunas de "
                    "investigação pendentes."
                )
            )

        return " ".join(
            details
        )

    @staticmethod
    def _recommended_next_step(
        decision: FinalDecision,
    ) -> str:
        """
        Define próximo passo recomendado.

        Nenhum passo executa contenção automaticamente.
        """

        if (
            decision
            == FinalDecision.ESCALATED_N2
        ):
            return (
                "Encaminhar o caso para SOC N2/humano, "
                "preservando evidências e avaliando "
                "ações de contenção somente mediante "
                "aprovação apropriada."
            )

        if (
            decision
            == FinalDecision.CLOSED_N1
        ):
            return (
                "Documentar o fechamento N1, manter "
                "a trilha de auditoria e preservar "
                "as evidências associadas."
            )

        return (
            "Solicitar revisão humana antes de "
            "qualquer decisão final ou ação crítica."
        )

    @staticmethod
    def _qa_status(
        value: Any,
    ) -> QAStatus:
        """
        Valida QAStatus.
        """

        try:
            return QAStatus(value)

        except Exception as exc:
            raise ValueError(
                "qa.status inválido."
            ) from exc

    @staticmethod
    def _classification(
        value: Any,
    ) -> FinalClassification:
        """
        Valida FinalClassification.
        """

        try:
            return FinalClassification(
                value
            )

        except Exception as exc:
            raise ValueError(
                "classification inválida."
            ) from exc

    @staticmethod
    def _severity(
        value: Any,
    ) -> Severity:
        """
        Valida Severity.
        """

        try:
            return Severity(value)

        except Exception as exc:
            raise ValueError(
                "severity inválida."
            ) from exc

    @staticmethod
    def _confidence(
        value: Any,
    ) -> int:
        """
        Valida confiança entre 0 e 100.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "confidence precisa ser inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "confidence precisa ser inteiro."
            )

        if value < 0 or value > 100:
            raise ValueError(
                "confidence precisa estar "
                "entre 0 e 100."
            )

        return value

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
    def _optional_mapping(
        value: Any,
    ) -> Mapping[str, Any]:
        """
        Retorna mapping ou mapping vazio.
        """

        if isinstance(
            value,
            Mapping,
        ):
            return value

        return {}

    @staticmethod
    def _mapping_list(
        value: Any,
    ) -> list[Mapping[str, Any]]:
        """
        Normaliza lista de mappings.
        """

        if not isinstance(
            value,
            (list, tuple),
        ):
            return []

        return [
            item
            for item in value
            if isinstance(
                item,
                Mapping,
            )
        ]

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
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Normaliza lista de strings.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Era esperada uma lista "
                "de strings."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(
                item,
                str,
            ):
                raise ValueError(
                    "A lista contém valor "
                    "que não é string."
                )

            cleaned = item.strip()

            if (
                cleaned
                and cleaned not in result
            ):
                result.append(
                    cleaned
                )

        return result

    @staticmethod
    def _append_unique(
        values: list[str],
        value: str,
    ) -> None:
        """
        Adiciona string sem duplicação.
        """

        if value not in values:
            values.append(
                value
            )

    @staticmethod
    def _create_escalation_id() -> str:
        """
        Gera identificador único.
        """

        return (
            "ESC-"
            + uuid4().hex.upper()
        )


escalation_agent = EscalationAgent()