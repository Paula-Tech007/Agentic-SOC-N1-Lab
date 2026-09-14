"""
AG-04 — Threat Intelligence Agent.

Responsável por validar e consolidar resultados de
Threat Intelligence obtidos por ferramentas autorizadas.

Nesta fase, o agente NÃO consulta fontes externas
diretamente.

As integrações reais serão implementadas posteriormente
na camada de Tools / Permission Engine.

Fluxo atual:

Resultado de ferramenta ou simulação controlada
        ↓
AG-04 Threat Intelligence
        ↓
Validação dos findings
        ↓
ThreatIntelResult
        ↓
Orchestrator
        ↓
CaseState

Princípio:

A LLM interpreta.
A ferramenta comprova.
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
    ThreatIntelFinding,
    ThreatIntelResult,
)


class ThreatIntelligenceAgent(BaseAgent):
    """
    AG-04 — Threat Intelligence Agent.
    """

    agent_id = "AG-04"

    agent_name = "Threat Intelligence Agent"

    description = (
        "Validar e consolidar informações de "
        "Threat Intelligence provenientes de "
        "fontes e ferramentas autorizadas."
    )

    allowed_tools: tuple[str, ...] = (
        "lookup_ip",
        "lookup_domain",
        "lookup_url",
        "lookup_hash",
        "lookup_email",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Consolida resultados de Threat Intelligence.

        O input_payload precisa fornecer resultados
        previamente obtidos por ferramenta autorizada
        ou simulação controlada.
        """

        snapshot = request.case_snapshot.to_dict()

        alert_data = snapshot.get("alert")

        if not isinstance(alert_data, Mapping):
            raise ValueError(
                "O snapshot precisa possuir "
                "um objeto 'alert'."
            )

        alert_id = self._required_string(
            alert_data.get("alert_id"),
            "alert.alert_id",
        )

        payload = request.input_payload.to_dict()

        findings_data = payload.get("findings")

        if not isinstance(findings_data, (list, tuple)):
            raise ValueError(
                "input_payload.findings precisa "
                "ser uma lista."
            )

        if not findings_data:
            raise ValueError(
                "AG-04 exige pelo menos um finding "
                "proveniente de ferramenta autorizada."
            )

        findings = self._build_findings(
            findings_data
        )

        queried_sources = self._build_queried_sources(
            payload=payload,
            findings=findings,
        )

        evidence_references = self._string_list(
            payload.get("evidence_references")
        )

        errors = self._string_list(
            payload.get("errors")
        )

        threat_intel_id = payload.get(
            "threat_intel_id"
        )

        if threat_intel_id is None:
            threat_intel_id = (
                self._create_threat_intel_id()
            )

        threat_intel_id = self._required_string(
            threat_intel_id,
            "threat_intel_id",
        )

        summary = self._build_summary(
            findings=findings,
            queried_sources=queried_sources,
            errors=errors,
        )

        result = ThreatIntelResult(
            threat_intel_id=threat_intel_id,
            alert_id=alert_id,
            findings=findings,
            queried_sources=queried_sources,
            evidence_references=evidence_references,
            summary=summary,
            errors=errors,
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    result.threat_intel_id
                ),
                "threat_intel_result": (
                    result.model_dump(
                        mode="json"
                    )
                ),
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Threat Intelligence consolidada "
                    "pelo AG-04."
                ),
                (
                    "Nenhuma reputação foi inventada; "
                    "somente resultados fornecidos "
                    "foram utilizados."
                ),
            ),
        )

    def _build_findings(
        self,
        findings_data: list[Any] | tuple[Any, ...],
    ) -> list[ThreatIntelFinding]:
        """
        Valida cada finding recebido.
        """

        findings: list[
            ThreatIntelFinding
        ] = []

        seen_ioc_ids: set[str] = set()

        for position, item in enumerate(
            findings_data,
            start=1,
        ):
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Finding na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                finding = (
                    ThreatIntelFinding.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "Finding inválido na posição "
                    f"{position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if finding.ioc_id in seen_ioc_ids:
                raise ValueError(
                    "IOC duplicado nos findings: "
                    f"{finding.ioc_id}"
                )

            seen_ioc_ids.add(
                finding.ioc_id
            )

            findings.append(
                finding
            )

        return findings

    def _build_queried_sources(
        self,
        payload: dict[str, Any],
        findings: list[ThreatIntelFinding],
    ) -> list[str]:
        """
        Consolida as fontes explicitamente informadas
        e os providers presentes nos findings.
        """

        provided_sources = self._string_list(
            payload.get("queried_sources")
        )

        sources: list[str] = []

        for source in provided_sources:
            if source not in sources:
                sources.append(source)

        for finding in findings:
            if finding.provider not in sources:
                sources.append(
                    finding.provider
                )

        return sources

    def _build_summary(
        self,
        findings: list[ThreatIntelFinding],
        queried_sources: list[str],
        errors: list[str],
    ) -> str:
        """
        Produz resumo objetivo somente com dados
        comprovados pelos findings recebidos.
        """

        confirmed_malicious = sum(
            1
            for finding in findings
            if finding.malicious_confirmed is True
        )

        confirmed_non_malicious = sum(
            1
            for finding in findings
            if finding.malicious_confirmed is False
        )

        inconclusive = (
            len(findings)
            - confirmed_malicious
            - confirmed_non_malicious
        )

        return (
            "Threat Intelligence processou "
            f"{len(findings)} IOC(s) em "
            f"{len(queried_sources)} fonte(s). "
            f"Maliciosos confirmados: "
            f"{confirmed_malicious}. "
            f"Não maliciosos confirmados: "
            f"{confirmed_non_malicious}. "
            f"Inconclusivos: {inconclusive}. "
            f"Erros de consulta registrados: "
            f"{len(errors)}."
        )

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
            if not isinstance(item, str):
                raise ValueError(
                    "A lista contém valor "
                    "que não é string."
                )

            cleaned = item.strip()

            if cleaned and cleaned not in result:
                result.append(cleaned)

        return result

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Valida campo textual obrigatório.
        """

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} precisa ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} não pode ser vazio."
            )

        return cleaned

    @staticmethod
    def _create_threat_intel_id() -> str:
        """
        Gera identificador único do resultado.
        """

        return (
            "TI-"
            + uuid4().hex.upper()
        )


threat_intelligence_agent = (
    ThreatIntelligenceAgent()
)