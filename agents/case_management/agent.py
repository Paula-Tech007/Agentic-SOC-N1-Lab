"""
AG-11 — Case Management Agent.

Responsável por consolidar a documentação operacional
do caso depois da aprovação do Reflection/QA.

Fluxo:

CaseState
    ↓
AG-10 Reflection/QA APPROVED
    ↓
AG-11 Case Management
    ↓
Documentação consolidada
    ↓
AuditEvent
    ↓
Orchestrator
    ↓
CaseState.audit

Responsabilidades:

- consolidar informações já existentes no caso;
- produzir resumo documental;
- preservar referências;
- produzir evento de auditoria;
- não inventar evidências;
- não executar contenção;
- não decidir sozinho fechamento ou escalonamento.

Princípio:

AG-11 documenta.
AG-12 decide escalonamento.
Supervisor controla o fluxo.
"""

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)
from core.schemas import AuditEvent


class CaseManagementAgent(BaseAgent):
    """
    AG-11 — Case Management Agent.
    """

    agent_id = "AG-11"

    agent_name = "Case Management Agent"

    description = (
        "Consolidar a documentação do caso e produzir "
        "registro auditável antes da decisão final."
    )

    allowed_tools: tuple[str, ...] = (
        "read_case_context",
        "read_investigation",
        "read_qa",
        "read_evidence",
        "read_audit",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Consolida a documentação do caso.

        O agente somente trabalha quando:

        - existe alerta;
        - existe InvestigationResult;
        - existe QAResult;
        - QA está APPROVED.

        Nenhuma nova evidência é criada.
        """

        snapshot = request.case_snapshot.to_dict()

        case_id = self._required_string(
            snapshot.get("case_id"),
            "case_snapshot.case_id",
        )

        correlation_id = self._required_string(
            snapshot.get("correlation_id"),
            "case_snapshot.correlation_id",
        )

        alert = snapshot.get(
            "alert"
        )

        if not isinstance(
            alert,
            Mapping,
        ):
            raise ValueError(
                "AG-11 exige alerta consolidado "
                "no CaseState."
            )

        alert_id = self._required_string(
            alert.get("alert_id"),
            "alert.alert_id",
        )

        investigation = snapshot.get(
            "investigation"
        )

        if not isinstance(
            investigation,
            Mapping,
        ):
            raise ValueError(
                "AG-11 exige InvestigationResult "
                "consolidado no CaseState."
            )

        investigation_id = self._required_string(
            investigation.get(
                "investigation_id"
            ),
            "investigation.investigation_id",
        )

        qa = snapshot.get(
            "qa"
        )

        if not isinstance(
            qa,
            Mapping,
        ):
            raise ValueError(
                "AG-11 exige QAResult "
                "consolidado no CaseState."
            )

        qa_id = self._required_string(
            qa.get("qa_id"),
            "qa.qa_id",
        )

        qa_status = self._required_string(
            qa.get("status"),
            "qa.status",
        )

        if qa_status != "APPROVED":
            raise ValueError(
                "AG-11 somente pode documentar "
                "casos com QA APPROVED."
            )

        payload = request.input_payload.to_dict()

        documentation_id = payload.get(
            "documentation_id"
        )

        if documentation_id is None:
            documentation_id = (
                self._create_documentation_id()
            )

        documentation_id = self._required_string(
            documentation_id,
            "documentation_id",
        )

        title = self._required_string(
            payload.get(
                "title",
                (
                    "Documentação do caso "
                    f"{case_id}"
                ),
            ),
            "title",
        )

        executive_summary = self._required_string(
            payload.get(
                "executive_summary"
            ),
            "executive_summary",
        )

        analyst_summary = self._required_string(
            payload.get(
                "analyst_summary"
            ),
            "analyst_summary",
        )

        recommendations = self._string_list(
            payload.get(
                "recommendations"
            )
        )

        evidence_references = self._string_list(
            payload.get(
                "evidence_references"
            )
        )

        related_references = self._string_list(
            payload.get(
                "related_references"
            )
        )

        related_references = (
            self._merge_strings(
                [
                    alert_id,
                    investigation_id,
                    qa_id,
                ],
                related_references,
                evidence_references,
            )
        )

        documentation = {
            "documentation_id": (
                documentation_id
            ),
            "case_id": case_id,
            "correlation_id": (
                correlation_id
            ),
            "alert_id": alert_id,
            "investigation_id": (
                investigation_id
            ),
            "qa_id": qa_id,
            "title": title,
            "executive_summary": (
                executive_summary
            ),
            "analyst_summary": (
                analyst_summary
            ),
            "recommendations": (
                recommendations
            ),
            "evidence_references": (
                evidence_references
            ),
            "related_references": (
                related_references
            ),
        }

        audit_event = AuditEvent(
            audit_id=self._create_audit_id(),
            case_id=case_id,
            correlation_id=correlation_id,
            event_type="CASE_DOCUMENTED",
            actor_type="AGENT",
            actor_id=self.agent_id,
            action="document_case",
            status="SUCCESS",
            message=(
                "AG-11 consolidou a documentação "
                "do caso para a etapa de decisão."
            ),
            references=tuple(
                related_references
            ),
            payload={
                "documentation_id": (
                    documentation_id
                ),
                "alert_id": alert_id,
                "investigation_id": (
                    investigation_id
                ),
                "qa_id": qa_id,
                "qa_status": qa_status,
                "recommendation_count": len(
                    recommendations
                ),
                "evidence_reference_count": len(
                    evidence_references
                ),
            },
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    documentation_id
                ),
                "case_documentation": (
                    documentation
                ),
                "audit_event": (
                    audit_event.model_dump(
                        mode="json"
                    )
                ),
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Documentação consolidada "
                    "pelo AG-11."
                ),
                (
                    "Evento de auditoria preparado "
                    "para inclusão no CaseState."
                ),
                (
                    "Nenhuma decisão final ou ação "
                    "crítica foi executada."
                ),
            ),
        )

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
                f"{field_name} não pode "
                "ser vazio."
            )

        return cleaned

    @staticmethod
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Valida e normaliza lista de strings.
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
    def _merge_strings(
        *collections: list[str],
    ) -> list[str]:
        """
        Une listas preservando ordem
        e removendo duplicados.
        """

        result: list[str] = []

        for collection in collections:
            for value in collection:
                if value not in result:
                    result.append(
                        value
                    )

        return result

    @staticmethod
    def _create_documentation_id() -> str:
        """
        Gera identificador da documentação.
        """

        return (
            "DOC-"
            + uuid4().hex.upper()
        )

    @staticmethod
    def _create_audit_id() -> str:
        """
        Gera identificador do AuditEvent.
        """

        return (
            "AUDIT-"
            + uuid4().hex.upper()
        )


case_management_agent = CaseManagementAgent()