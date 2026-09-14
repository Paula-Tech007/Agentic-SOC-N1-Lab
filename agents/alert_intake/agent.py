"""
AG-02 — Alert Intake Agent.

Responsável pela entrada inicial de alertas no
Agentic SOC N1 Lab.

Fluxo:

Alerta bruto
    ↓
AG-02 Alert Intake
    ↓
Validação
    ↓
Normalização
    ↓
Alert oficial
    ↓
CaseState

Este agente não utiliza LLM para normalização básica.

A normalização deve ser determinística, validável e
baseada nos schemas oficiais do projeto.
"""

from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)
from core.schemas import (
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    Severity,
)


class AlertIntakeAgent(BaseAgent):
    """
    Agente oficial de entrada e normalização de alertas.
    """

    agent_id = "AG-02"
    agent_name = "Alert Intake Agent"

    description = (
        "Receber, validar e normalizar alertas antes "
        "da criação do CaseState."
    )

    allowed_tools: tuple[str, ...] = ()

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Normaliza o alerta bruto recebido pelo Orchestrator.
        """

        payload = request.input_payload.to_dict()

        source_data = payload.get("source")
        event_data = payload.get("event")

        if not isinstance(source_data, dict):
            raise ValueError(
                "O alerta bruto precisa possuir "
                "o objeto 'source'."
            )

        if not isinstance(event_data, dict):
            raise ValueError(
                "O alerta bruto precisa possuir "
                "o objeto 'event'."
            )

        source = self._build_source(
            source_data
        )

        event, normalization_notes = (
            self._build_event(
                event_data
            )
        )

        severity = self._normalize_severity(
            payload.get(
                "initial_severity",
                Severity.MEDIUM,
            )
        )

        alert_id = payload.get("alert_id")

        if alert_id is None:
            alert_id = self._create_alert_id()

        if not isinstance(alert_id, str):
            raise ValueError(
                "alert_id precisa ser uma string."
            )

        alert_id = alert_id.strip()

        if not alert_id:
            raise ValueError(
                "alert_id não pode ser vazio."
            )

        try:
            alert = Alert(
                alert_id=alert_id,
                correlation_id=request.correlation_id,
                source=source,
                event=event,
                initial_severity=severity,
            )

        except ValidationError as exc:
            raise ValueError(
                "Falha ao validar o alerta normalizado: "
                f"{exc}"
            ) from exc

        messages = (
            "Alerta recebido e normalizado pelo AG-02.",
            *normalization_notes,
        )

        return AgentWorkResult(
            output={
                "result_reference": alert.alert_id,
                "normalized_alert": alert.model_dump(
                    mode="json"
                ),
            },
            messages=messages,
        )

    def _build_source(
        self,
        source_data: dict[str, Any],
    ) -> AlertSource:
        """
        Normaliza a origem do alerta.
        """

        system = source_data.get("system")

        if not isinstance(system, str):
            raise ValueError(
                "source.system precisa ser uma string."
            )

        system = system.strip()

        if not system:
            raise ValueError(
                "source.system não pode ser vazio."
            )

        return AlertSource(
            system=system,
            product=self._optional_string(
                source_data.get("product")
            ),
            rule_name=self._optional_string(
                source_data.get("rule_name")
            ),
            rule_id=self._optional_string(
                source_data.get("rule_id")
            ),
        )

    def _build_event(
        self,
        event_data: dict[str, Any],
    ) -> tuple[AlertEvent, tuple[str, ...]]:
        """
        Normaliza o evento associado ao alerta.

        Tipos desconhecidos não são inventados.
        Eles são convertidos para UNSUPPORTED para que
        etapas posteriores possam escalá-los.
        """

        message = event_data.get("message")

        if not isinstance(message, str):
            raise ValueError(
                "event.message precisa ser uma string."
            )

        message = message.strip()

        if not message:
            raise ValueError(
                "event.message não pode ser vazio."
            )

        event_type, type_note = (
            self._normalize_alert_type(
                event_data.get("event_type")
            )
        )

        raw_event = event_data.get(
            "raw_event",
            {},
        )

        if not isinstance(raw_event, dict):
            raise ValueError(
                "event.raw_event precisa ser um objeto."
            )

        event_kwargs: dict[str, Any] = {
            "event_type": event_type,
            "category": self._optional_string(
                event_data.get("category")
            ),
            "message": message,
            "raw_event": raw_event,
        }

        timestamp = event_data.get("timestamp")

        if timestamp is not None:
            event_kwargs["timestamp"] = timestamp

        try:
            event = AlertEvent.model_validate(
                event_kwargs
            )

        except ValidationError as exc:
            raise ValueError(
                "Falha ao validar o evento normalizado: "
                f"{exc}"
            ) from exc

        notes: list[str] = []

        if type_note is not None:
            notes.append(type_note)

        return event, tuple(notes)

    def _normalize_alert_type(
        self,
        value: Any,
    ) -> tuple[AlertType, str | None]:
        """
        Normaliza o tipo de alerta.

        Valores desconhecidos viram UNSUPPORTED em vez
        de serem interpretados livremente.
        """

        if isinstance(value, AlertType):
            return value, None

        if not isinstance(value, str):
            raise ValueError(
                "event.event_type precisa ser uma string."
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValueError(
                "event.event_type não pode ser vazio."
            )

        try:
            return AlertType(normalized), None

        except ValueError:
            return (
                AlertType.UNSUPPORTED,
                (
                    "Tipo de alerta não reconhecido: "
                    f"{value!r}. Normalizado como UNSUPPORTED."
                ),
            )

    def _normalize_severity(
        self,
        value: Any,
    ) -> Severity:
        """
        Normaliza a severidade recebida.
        """

        if isinstance(value, Severity):
            return value

        if not isinstance(value, str):
            raise ValueError(
                "initial_severity precisa ser uma string."
            )

        normalized = value.strip().upper()

        aliases = {
            "INFO": "INFORMATIONAL",
            "INFORMATION": "INFORMATIONAL",
        }

        normalized = aliases.get(
            normalized,
            normalized,
        )

        try:
            return Severity(normalized)

        except ValueError as exc:
            raise ValueError(
                "Severidade não suportada: "
                f"{value!r}."
            ) from exc

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        """
        Normaliza campos textuais opcionais.
        """

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Campo textual opcional recebeu "
                "valor que não é string."
            )

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned

    @staticmethod
    def _create_alert_id() -> str:
        """
        Gera identificador único para o alerta.
        """

        return "ALT-" + uuid4().hex.upper()


alert_intake_agent = AlertIntakeAgent()