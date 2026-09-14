"""
AG-09 — Incident Analyst Agent.

Responsável por consolidar os resultados produzidos
pelos agentes anteriores e construir a investigação
técnica do caso.

O AG-09 trabalha sobre contexto já consolidado no
CaseState.

Fluxo:

Triage
+ Threat Intelligence
+ Identity
+ Asset Context
+ Phishing, quando aplicável
+ Knowledge/RAG
+ Evidências
        ↓
AG-09 Incident Analyst
        ↓
InvestigationFinding
+ TimelineEntry
        ↓
InvestigationResult
        ↓
Orchestrator
        ↓
CaseState.investigation

Regras:

- não inventar evidências;
- inferências precisam ser identificadas;
- toda conclusão deve possuir nível de confiança;
- não executar contenção;
- não tomar sozinho a decisão final de escalonamento;
- preservar lacunas de investigação.

Princípio:

Ferramentas comprovam.
Agentes especializados enriquecem.
AG-09 correlaciona.
QA revisa.
Supervisor decide o fluxo.
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
    InvestigationFinding,
    InvestigationResult,
    Severity,
    TimelineEntry,
)


class IncidentAnalystAgent(BaseAgent):
    """
    AG-09 — Incident Analyst Agent.
    """

    agent_id = "AG-09"

    agent_name = "Incident Analyst Agent"

    description = (
        "Correlacionar contexto e evidências do caso "
        "e produzir a investigação técnica consolidada."
    )

    allowed_tools: tuple[str, ...] = (
        "read_case_context",
        "read_evidence",
        "read_threat_intel",
        "read_identity_context",
        "read_asset_context",
        "read_knowledge",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Valida o contexto consolidado e produz
        InvestigationResult.

        Nesta fase, findings, timeline e conclusão
        chegam de análise controlada/simulada.

        Futuramente esta etapa poderá utilizar LLM
        com guardrails e evidências estruturadas.
        """

        snapshot = request.case_snapshot.to_dict()

        self._validate_case_context(
            snapshot
        )

        alert_data = snapshot.get(
            "alert"
        )

        if not isinstance(
            alert_data,
            Mapping,
        ):
            raise ValueError(
                "O snapshot precisa possuir "
                "um objeto 'alert'."
            )

        alert_id = self._required_string(
            alert_data.get("alert_id"),
            "alert.alert_id",
        )

        payload = request.input_payload.to_dict()

        summary = self._required_string(
            payload.get("summary"),
            "input_payload.summary",
        )

        final_severity = self._severity(
            payload.get("final_severity")
        )

        final_confidence = self._confidence(
            payload.get("final_confidence")
        )

        classification = self._classification(
            payload.get("classification")
        )

        recommended_action = self._required_string(
            payload.get("recommended_action"),
            "input_payload.recommended_action",
        )

        findings_data = payload.get(
            "findings"
        )

        if not isinstance(
            findings_data,
            (list, tuple),
        ):
            raise ValueError(
                "input_payload.findings precisa "
                "ser uma lista."
            )

        if not findings_data:
            raise ValueError(
                "AG-09 exige pelo menos um "
                "InvestigationFinding."
            )

        findings = self._build_findings(
            findings_data
        )

        timeline_data = payload.get(
            "timeline"
        )

        if not isinstance(
            timeline_data,
            (list, tuple),
        ):
            raise ValueError(
                "input_payload.timeline precisa "
                "ser uma lista."
            )

        if not timeline_data:
            raise ValueError(
                "AG-09 exige pelo menos um "
                "evento de timeline."
            )

        timeline = self._build_timeline(
            timeline_data
        )

        evidence_references = self._string_list(
            payload.get("evidence_references")
        )

        gaps = self._string_list(
            payload.get("gaps")
        )

        analyst_notes = self._string_list(
            payload.get("analyst_notes")
        )

        investigation_id = payload.get(
            "investigation_id"
        )

        if investigation_id is None:
            investigation_id = (
                self._create_investigation_id()
            )

        investigation_id = self._required_string(
            investigation_id,
            "investigation_id",
        )

        investigation = InvestigationResult(
            investigation_id=investigation_id,
            alert_id=alert_id,
            summary=summary,
            findings=findings,
            timeline=timeline,
            evidence_references=evidence_references,
            gaps=gaps,
            final_severity=final_severity,
            final_confidence=final_confidence,
            classification=classification,
            recommended_action=recommended_action,
            analyst_notes=analyst_notes,
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    investigation.investigation_id
                ),
                "investigation_result": (
                    investigation.model_dump(
                        mode="json"
                    )
                ),
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Investigação consolidada "
                    "pelo AG-09."
                ),
                (
                    "Findings marcados como inferência "
                    "permanecem identificados como "
                    "inferência."
                ),
                (
                    "Nenhuma ação de contenção foi "
                    "executada pelo Incident Analyst."
                ),
            ),
        )

    def _validate_case_context(
        self,
        snapshot: dict[str, Any],
    ) -> None:
        """
        Verifica se o AG-09 recebeu contexto suficiente
        para iniciar uma investigação.

        O AG-09 exige:

        - alerta;
        - triagem;
        - pelo menos uma fonte de enriquecimento.
        """

        alert = snapshot.get(
            "alert"
        )

        if not isinstance(
            alert,
            Mapping,
        ):
            raise ValueError(
                "AG-09 exige alerta consolidado "
                "no CaseState."
            )

        triage = snapshot.get(
            "triage"
        )

        if not isinstance(
            triage,
            Mapping,
        ):
            raise ValueError(
                "AG-09 exige TriageResult "
                "consolidado no CaseState."
            )

        enrichment_available = any(
            (
                snapshot.get(
                    "threat_intel"
                )
                is not None,
                bool(
                    snapshot.get(
                        "identities"
                    )
                ),
                bool(
                    snapshot.get(
                        "assets"
                    )
                ),
                snapshot.get(
                    "knowledge"
                )
                is not None,
                snapshot.get(
                    "phishing"
                )
                is not None,
            )
        )

        if not enrichment_available:
            raise ValueError(
                "AG-09 exige pelo menos uma fonte "
                "de enriquecimento consolidada."
            )

    def _build_findings(
        self,
        findings_data: list[Any] | tuple[Any, ...],
    ) -> list[InvestigationFinding]:
        """
        Valida os findings da investigação.
        """

        findings: list[
            InvestigationFinding
        ] = []

        seen_finding_ids: set[str] = set()

        for position, item in enumerate(
            findings_data,
            start=1,
        ):
            if not isinstance(
                item,
                Mapping,
            ):
                raise ValueError(
                    "Finding na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                finding = (
                    InvestigationFinding.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "InvestigationFinding inválido "
                    f"na posição {position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if (
                finding.finding_id
                in seen_finding_ids
            ):
                raise ValueError(
                    "finding_id duplicado: "
                    f"{finding.finding_id}"
                )

            seen_finding_ids.add(
                finding.finding_id
            )

            findings.append(
                finding
            )

        return findings

    def _build_timeline(
        self,
        timeline_data: list[Any] | tuple[Any, ...],
    ) -> list[TimelineEntry]:
        """
        Valida e ordena cronologicamente a timeline.
        """

        timeline: list[
            TimelineEntry
        ] = []

        for position, item in enumerate(
            timeline_data,
            start=1,
        ):
            if not isinstance(
                item,
                Mapping,
            ):
                raise ValueError(
                    "TimelineEntry na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                entry = (
                    TimelineEntry.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "TimelineEntry inválido "
                    f"na posição {position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            timeline.append(
                entry
            )

        timeline.sort(
            key=lambda item: item.timestamp
        )

        return timeline

    @staticmethod
    def _severity(
        value: Any,
    ) -> Severity:
        """
        Valida Severity utilizando o enum oficial.
        """

        try:
            return Severity(value)

        except Exception as exc:
            raise ValueError(
                "final_severity inválida."
            ) from exc

    @staticmethod
    def _classification(
        value: Any,
    ) -> FinalClassification:
        """
        Valida classificação final utilizando
        o enum oficial.
        """

        try:
            return FinalClassification(value)

        except Exception as exc:
            raise ValueError(
                "classification inválida."
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
                "final_confidence precisa "
                "ser um número inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "final_confidence precisa "
                "ser um número inteiro."
            )

        if value < 0 or value > 100:
            raise ValueError(
                "final_confidence precisa "
                "estar entre 0 e 100."
            )

        return value

    @staticmethod
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Normaliza listas de strings.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Era esperada uma lista de strings."
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
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Valida campo textual obrigatório.
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
                f"{field_name} não pode ser vazio."
            )

        return cleaned

    @staticmethod
    def _create_investigation_id() -> str:
        """
        Gera identificador único de investigação.
        """

        return (
            "INV-"
            + uuid4().hex.upper()
        )


incident_analyst_agent = IncidentAnalystAgent()