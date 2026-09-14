"""
AG-10 — Reflection / QA Agent.

Responsável por revisar de forma independente
o InvestigationResult produzido pelo AG-09.

Fluxo:

CaseState.investigation
        ↓
AG-10 Reflection / QA
        ↓
Verificação de:
- consistência;
- evidências ausentes;
- alegações não sustentadas;
- contradições;
- severidade;
- confiança;
- necessidade de nova investigação.
        ↓
QAResult
        ↓
Orchestrator
        ↓
CaseState.qa

Princípios:

- QA não fabrica evidências;
- QA não altera silenciosamente findings;
- QA pode aprovar ou rejeitar a investigação;
- QA pode solicitar retry;
- retry precisa indicar os agentes necessários;
- decisão final permanece fora do AG-10;
- ações críticas permanecem proibidas nesta etapa.
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
    QAResult,
    QAStatus,
    Severity,
)


class ReflectionQAAgent(BaseAgent):
    """
    AG-10 — Reflection / QA Agent.
    """

    agent_id = "AG-10"

    agent_name = "Reflection/QA Agent"

    description = (
        "Revisar a investigação consolidada, identificar "
        "lacunas, inconsistências, alegações não sustentadas "
        "e decidir se uma nova análise é necessária."
    )

    allowed_tools: tuple[str, ...] = (
        "read_investigation",
        "read_case_context",
        "read_evidence",
        "read_audit",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Revisa o InvestigationResult presente no snapshot
        e produz um QAResult oficial.
        """

        snapshot = request.case_snapshot.to_dict()

        investigation_data = snapshot.get(
            "investigation"
        )

        if not isinstance(
            investigation_data,
            Mapping,
        ):
            raise ValueError(
                "AG-10 exige InvestigationResult "
                "consolidado no CaseState."
            )

        investigation_id = self._required_string(
            investigation_data.get(
                "investigation_id"
            ),
            "investigation.investigation_id",
        )

        payload = request.input_payload.to_dict()

        qa_id = payload.get(
            "qa_id"
        )

        if qa_id is None:
            qa_id = self._create_qa_id()

        qa_id = self._required_string(
            qa_id,
            "qa_id",
        )

        payload_investigation_id = payload.get(
            "investigation_id",
            investigation_id,
        )

        payload_investigation_id = (
            self._required_string(
                payload_investigation_id,
                "investigation_id",
            )
        )

        if (
            payload_investigation_id
            != investigation_id
        ):
            raise ValueError(
                "investigation_id informado ao AG-10 "
                "não corresponde à investigação "
                "presente no CaseState."
            )

        status = self._qa_status(
            payload.get("status")
        )

        reviewed_severity = self._severity(
            payload.get(
                "reviewed_severity"
            )
        )

        reviewed_confidence = (
            self._confidence(
                payload.get(
                    "reviewed_confidence"
                )
            )
        )

        issues = self._string_list(
            payload.get("issues")
        )

        unsupported_claims = self._string_list(
            payload.get(
                "unsupported_claims"
            )
        )

        contradictions = self._string_list(
            payload.get(
                "contradictions"
            )
        )

        missing_evidence = self._string_list(
            payload.get(
                "missing_evidence"
            )
        )

        retry_required = payload.get(
            "retry_required",
            False,
        )

        if not isinstance(
            retry_required,
            bool,
        ):
            raise ValueError(
                "retry_required precisa ser booleano."
            )

        retry_targets = self._string_list(
            payload.get(
                "retry_targets"
            )
        )

        notes = self._string_list(
            payload.get("notes")
        )

        self._validate_review_logic(
            status=status,
            retry_required=retry_required,
            retry_targets=retry_targets,
        )

        qa_result = QAResult(
            qa_id=qa_id,
            investigation_id=(
                investigation_id
            ),
            status=status,
            issues=issues,
            unsupported_claims=(
                unsupported_claims
            ),
            contradictions=contradictions,
            missing_evidence=(
                missing_evidence
            ),
            reviewed_severity=(
                reviewed_severity
            ),
            reviewed_confidence=(
                reviewed_confidence
            ),
            retry_required=retry_required,
            retry_targets=retry_targets,
            notes=notes,
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    qa_result.qa_id
                ),
                "qa_result": (
                    qa_result.model_dump(
                        mode="json"
                    )
                ),
            },
            messages=(
                (
                    "Investigação revisada "
                    "pelo AG-10."
                ),
                (
                    "Nenhuma evidência nova "
                    "foi fabricada pelo QA."
                ),
                (
                    "A decisão final permanece "
                    "fora do Reflection/QA Agent."
                ),
            ),
        )

    def _validate_review_logic(
        self,
        status: QAStatus,
        retry_required: bool,
        retry_targets: list[str],
    ) -> None:
        """
        Aplica regras de consistência do QA.

        APPROVED:
        - não pode solicitar retry.

        REJECTED:
        - deve solicitar retry;
        - deve informar pelo menos um retry_target.

        NOT_REVIEWED:
        - não é aceito como resultado final do AG-10.
        """

        if status == QAStatus.NOT_REVIEWED:
            raise ValueError(
                "AG-10 não pode concluir com "
                "status NOT_REVIEWED."
            )

        if status == QAStatus.APPROVED:
            if retry_required:
                raise ValueError(
                    "QA aprovado não pode "
                    "solicitar retry."
                )

            if retry_targets:
                raise ValueError(
                    "QA aprovado não pode possuir "
                    "retry_targets."
                )

        if status == QAStatus.REJECTED:
            if not retry_required:
                raise ValueError(
                    "QA rejeitado precisa "
                    "solicitar retry."
                )

            if not retry_targets:
                raise ValueError(
                    "QA rejeitado precisa informar "
                    "pelo menos um retry_target."
                )

    @staticmethod
    def _qa_status(
        value: Any,
    ) -> QAStatus:
        """
        Valida status utilizando QAStatus oficial.
        """

        try:
            return QAStatus(value)

        except Exception as exc:
            raise ValueError(
                "status de QA inválido."
            ) from exc

    @staticmethod
    def _severity(
        value: Any,
    ) -> Severity:
        """
        Valida severidade revisada.
        """

        try:
            return Severity(value)

        except Exception as exc:
            raise ValueError(
                "reviewed_severity inválida."
            ) from exc

    @staticmethod
    def _confidence(
        value: Any,
    ) -> int:
        """
        Valida confiança revisada entre 0 e 100.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "reviewed_confidence precisa "
                "ser um número inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "reviewed_confidence precisa "
                "ser um número inteiro."
            )

        if value < 0 or value > 100:
            raise ValueError(
                "reviewed_confidence precisa "
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
    def _create_qa_id() -> str:
        """
        Gera identificador único de QA.
        """

        return (
            "QA-"
            + uuid4().hex.upper()
        )


reflection_qa_agent = ReflectionQAAgent()