"""
AG-03 — Triage Analyst Agent.

Responsável pela triagem inicial dos alertas já
normalizados pelo AG-02.

O agente:

- identifica o tipo oficial do alerta;
- preserva a severidade conhecida;
- determina quais especialistas são necessários;
- identifica informações ainda ausentes;
- sinaliza escalonamento imediato quando aplicável;
- produz um TriageResult oficial.

Nesta etapa a triagem é determinística.

Nenhuma evidência inexistente é criada e nenhuma
conclusão crítica depende de suposição da LLM.
"""

from typing import Any
from uuid import uuid4

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)
from core.schemas import (
    AlertType,
    Severity,
    TriageResult,
)


class TriageAnalystAgent(BaseAgent):
    """
    AG-03 — Analista de Triagem.
    """

    agent_id = "AG-03"
    agent_name = "Triage Analyst Agent"

    description = (
        "Realizar triagem inicial, classificação, "
        "severidade e direcionamento dos especialistas."
    )

    allowed_tools: tuple[str, ...] = ()

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Executa a triagem utilizando somente o contexto
        autorizado recebido do Orchestrator.
        """

        snapshot = request.case_snapshot.to_dict()

        alert_data = snapshot.get("alert")

        if not isinstance(alert_data, dict):
            raise ValueError(
                "O snapshot precisa possuir "
                "um objeto 'alert'."
            )

        alert_id = self._required_string(
            alert_data.get("alert_id"),
            "alert.alert_id",
        )

        event_data = alert_data.get("event")

        if not isinstance(event_data, dict):
            raise ValueError(
                "alert.event precisa ser um objeto."
            )

        alert_type = self._parse_alert_type(
            event_data.get("event_type")
        )

        severity = self._parse_severity(
            alert_data.get("initial_severity")
        )

        required_agents = (
            self._required_agents(
                alert_type
            )
        )

        missing_data = (
            self._missing_data(
                alert_type
            )
        )

        immediate_escalation = (
            alert_type == AlertType.UNSUPPORTED
            or severity == Severity.CRITICAL
        )

        escalation_reason = None

        if alert_type == AlertType.UNSUPPORTED:
            escalation_reason = (
                "Tipo de alerta não suportado pelo "
                "catálogo inicial do SOC N1."
            )

        elif severity == Severity.CRITICAL:
            escalation_reason = (
                "Alerta recebido com severidade CRITICAL."
            )

        confidence = self._calculate_confidence(
            alert_type=alert_type,
            severity=severity,
        )

        reasons = [
            f"alert_type:{alert_type.value}",
            f"initial_severity:{severity.value}",
            "normalized_alert_available",
        ]

        summary = (
            "Triagem inicial concluída para alerta "
            f"{alert_id} do tipo {alert_type.value}, "
            f"com severidade {severity.value}."
        )

        triage = TriageResult(
            triage_id=self._create_triage_id(),
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            confidence=confidence,
            summary=summary,
            reasons=reasons,
            ioc_references=self._string_list(
                snapshot.get("ioc_references")
            ),
            identity_references=self._string_list(
                snapshot.get("identity_references")
            ),
            asset_references=self._string_list(
                snapshot.get("asset_references")
            ),
            required_agents=required_agents,
            missing_data=missing_data,
            immediate_escalation=immediate_escalation,
            escalation_reason=escalation_reason,
        )

        return AgentWorkResult(
            output={
                "result_reference": triage.triage_id,
                "triage_result": triage.model_dump(
                    mode="json"
                ),
            },
            messages=(
                "Triagem concluída pelo AG-03.",
                (
                    "Nenhuma evidência foi criada "
                    "durante a classificação."
                ),
            ),
        )

    def _required_agents(
        self,
        alert_type: AlertType,
    ) -> list[str]:
        """
        Define especialistas recomendados para cada
        categoria oficial de alerta.
        """

        routing: dict[AlertType, list[str]] = {
            AlertType.AUTH_BRUTE_FORCE: [
                "AG-04",
                "AG-05",
                "AG-06",
                "AG-08",
            ],
            AlertType.SUSPICIOUS_LOGIN: [
                "AG-04",
                "AG-05",
                "AG-06",
                "AG-08",
            ],
            AlertType.CREDENTIAL_EXPOSURE: [
                "AG-04",
                "AG-05",
                "AG-08",
            ],
            AlertType.PHISHING: [
                "AG-07",
                "AG-04",
                "AG-08",
            ],
            AlertType.MALWARE_DETECTION: [
                "AG-04",
                "AG-06",
                "AG-08",
            ],
            AlertType.SUSPICIOUS_POWERSHELL: [
                "AG-06",
                "AG-08",
            ],
            AlertType.MALICIOUS_IOC: [
                "AG-04",
                "AG-06",
                "AG-08",
            ],
            AlertType.PRIVILEGED_ACCOUNT_ACTIVITY: [
                "AG-05",
                "AG-06",
                "AG-08",
            ],
            AlertType.LATERAL_MOVEMENT_SUSPECTED: [
                "AG-04",
                "AG-05",
                "AG-06",
                "AG-08",
            ],
            AlertType.DATA_EXFILTRATION_SUSPECTED: [
                "AG-04",
                "AG-06",
                "AG-08",
            ],
            AlertType.UNSUPPORTED: [
                "AG-12",
            ],
        }

        return list(
            routing.get(
                alert_type,
                ["AG-12"],
            )
        )

    def _missing_data(
        self,
        alert_type: AlertType,
    ) -> list[str]:
        """
        Identifica informações normalmente necessárias
        para aprofundar cada tipo de alerta.

        Estes campos representam dados a buscar,
        não fatos já comprovados.
        """

        requirements: dict[AlertType, list[str]] = {
            AlertType.AUTH_BRUTE_FORCE: [
                "login_success_after_failures",
                "identity_context",
                "source_ip_reputation",
                "asset_context",
            ],
            AlertType.SUSPICIOUS_LOGIN: [
                "identity_context",
                "source_ip_reputation",
                "asset_context",
            ],
            AlertType.CREDENTIAL_EXPOSURE: [
                "identity_status",
                "leak_confirmation",
            ],
            AlertType.PHISHING: [
                "email_headers",
                "urls_and_attachments",
            ],
            AlertType.MALWARE_DETECTION: [
                "asset_context",
                "malware_hash_reputation",
            ],
            AlertType.SUSPICIOUS_POWERSHELL: [
                "asset_context",
                "process_tree",
            ],
            AlertType.MALICIOUS_IOC: [
                "threat_intelligence_confirmation",
                "asset_context",
            ],
            AlertType.PRIVILEGED_ACCOUNT_ACTIVITY: [
                "identity_privileges",
                "asset_context",
            ],
            AlertType.LATERAL_MOVEMENT_SUSPECTED: [
                "identity_context",
                "source_asset",
                "destination_asset",
            ],
            AlertType.DATA_EXFILTRATION_SUSPECTED: [
                "asset_context",
                "network_context",
                "data_volume",
            ],
            AlertType.UNSUPPORTED: [
                "supported_playbook",
            ],
        }

        return list(
            requirements.get(
                alert_type,
                [],
            )
        )

    def _calculate_confidence(
        self,
        alert_type: AlertType,
        severity: Severity,
    ) -> int:
        """
        Calcula confiança apenas sobre a classificação
        estrutural realizada nesta etapa.
        """

        if alert_type == AlertType.UNSUPPORTED:
            return 100

        if severity == Severity.INFORMATIONAL:
            return 85

        return 90

    @staticmethod
    def _parse_alert_type(
        value: Any,
    ) -> AlertType:
        """
        Converte o tipo serializado para AlertType.
        """

        if isinstance(value, AlertType):
            return value

        if not isinstance(value, str):
            raise ValueError(
                "alert.event.event_type precisa "
                "ser uma string."
            )

        try:
            return AlertType(
                value.strip().upper()
            )

        except ValueError as exc:
            raise ValueError(
                f"Tipo de alerta inválido: {value!r}."
            ) from exc

    @staticmethod
    def _parse_severity(
        value: Any,
    ) -> Severity:
        """
        Converte severidade serializada para Severity.
        """

        if isinstance(value, Severity):
            return value

        if not isinstance(value, str):
            raise ValueError(
                "alert.initial_severity precisa "
                "ser uma string."
            )

        try:
            return Severity(
                value.strip().upper()
            )

        except ValueError as exc:
            raise ValueError(
                f"Severidade inválida: {value!r}."
            ) from exc

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Valida string obrigatória.
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
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Converte referências serializadas para lista
        de strings válidas.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Referências precisam ser uma lista."
            )

        result: list[str] = []

        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()

                if cleaned:
                    result.append(cleaned)

        return result

    @staticmethod
    def _create_triage_id() -> str:
        """
        Gera identificador único do resultado de triagem.
        """

        return "TRIAGE-" + uuid4().hex.upper()


triage_analyst_agent = TriageAnalystAgent()