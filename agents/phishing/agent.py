"""
AG-07 — Phishing Analyst Agent.

Responsável por analisar contexto de phishing já coletado
por fontes e ferramentas autorizadas.

Fluxo:

Alerta PHISHING
    ↓
AG-07 Phishing Analyst
    ↓
Sender
Recipients
Subject
URLs
Attachments
Hashes
SPF
DKIM
DMARC
Indicators
    ↓
PhishingResult
    ↓
CaseState.phishing

Princípios:

- ferramenta comprova;
- agente interpreta somente dados disponíveis;
- nenhuma evidência é inventada;
- nenhum link é aberto automaticamente;
- nenhum anexo é executado;
- nenhuma ação crítica é executada;
- dados ausentes permanecem ausentes;
- resultado inválido falha de forma controlada.
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
    AlertType,
    EmailAuthenticationResult,
    FinalClassification,
    PhishingResult,
    Severity,
)


class PhishingAnalystAgent(BaseAgent):
    """
    AG-07 — Phishing Analyst Agent.
    """

    agent_id = "AG-07"

    agent_name = "Phishing Analyst Agent"

    description = (
        "Analisar mensagens suspeitas de phishing usando "
        "evidências já coletadas e produzir PhishingResult."
    )

    allowed_tools: tuple[str, ...] = (
        "read_case_context",
        "read_email_metadata",
        "read_email_authentication",
        "read_url_reputation",
        "read_attachment_metadata",
        "read_hash_reputation",
        "read_evidence",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Produz PhishingResult a partir de dados
        defensivos já coletados.

        O agente não acessa URLs e não executa anexos.
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

        event = self._required_mapping(
            alert.get("event"),
            "alert.event",
        )

        event_type = event.get(
            "event_type"
        )

        if event_type != AlertType.PHISHING.value:
            raise ValueError(
                "AG-07 somente pode analisar "
                "alertas do tipo PHISHING."
            )

        payload = request.input_payload.to_dict()

        sender = self._optional_string(
            payload.get("sender")
        )

        recipients = self._string_list(
            payload.get("recipients")
        )

        subject = self._optional_string(
            payload.get("subject")
        )

        urls = self._string_list(
            payload.get("urls")
        )

        attachment_names = self._string_list(
            payload.get(
                "attachment_names"
            )
        )

        attachment_hashes = self._string_list(
            payload.get(
                "attachment_hashes"
            )
        )

        authentication = (
            self._authentication_result(
                payload.get(
                    "authentication"
                )
            )
        )

        suspicious_indicators = (
            self._string_list(
                payload.get(
                    "suspicious_indicators"
                )
            )
        )

        evidence_references = (
            self._string_list(
                payload.get(
                    "evidence_references"
                )
            )
        )

        classification = (
            self._classification(
                payload.get(
                    "classification"
                )
            )
        )

        severity = self._severity(
            payload.get("severity")
        )

        confidence = self._confidence(
            payload.get("confidence")
        )

        summary = self._required_string(
            payload.get("summary"),
            "summary",
        )

        phishing_id = payload.get(
            "phishing_id"
        )

        if phishing_id is None:
            phishing_id = (
                self._create_phishing_id()
            )

        phishing_id = self._required_string(
            phishing_id,
            "phishing_id",
        )

        phishing_result = PhishingResult(
            phishing_id=phishing_id,
            alert_id=alert_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            urls=urls,
            attachment_names=(
                attachment_names
            ),
            attachment_hashes=(
                attachment_hashes
            ),
            authentication=authentication,
            suspicious_indicators=(
                suspicious_indicators
            ),
            evidence_references=(
                evidence_references
            ),
            classification=classification,
            severity=severity,
            confidence=confidence,
            summary=summary,
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    phishing_result
                    .phishing_id
                ),
                "phishing_result": (
                    phishing_result
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
                    "Análise defensiva de phishing "
                    "concluída pelo AG-07."
                ),
                (
                    "URLs e anexos foram tratados "
                    "apenas como dados; nenhum "
                    "conteúdo foi executado."
                ),
                (
                    "Nenhuma evidência foi "
                    "fabricada."
                ),
            ),
        )

    @staticmethod
    def _authentication_result(
        value: Any,
    ) -> EmailAuthenticationResult:
        """
        Valida SPF, DKIM e DMARC.

        Authentication ausente é permitido,
        permanecendo com valores None.
        """

        if value is None:
            return EmailAuthenticationResult()

        if not isinstance(
            value,
            Mapping,
        ):
            raise ValueError(
                "authentication precisa "
                "ser um objeto."
            )

        return EmailAuthenticationResult(
            spf=PhishingAnalystAgent
            ._optional_string(
                value.get("spf")
            ),
            dkim=PhishingAnalystAgent
            ._optional_string(
                value.get("dkim")
            ),
            dmarc=PhishingAnalystAgent
            ._optional_string(
                value.get("dmarc")
            ),
        )

    @staticmethod
    def _classification(
        value: Any,
    ) -> FinalClassification:
        """
        Valida classificação final.
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
        Valida severidade.
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
        Valida objeto obrigatório.
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
    def _optional_string(
        value: Any,
    ) -> str | None:
        """
        Normaliza string opcional.
        """

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "Era esperada uma string "
                "ou None."
            )

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned

    @staticmethod
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Normaliza lista de strings.

        Remove valores vazios e duplicados.
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
    def _create_phishing_id() -> str:
        """
        Gera identificador único
        para PhishingResult.
        """

        return (
            "PHISH-"
            + uuid4().hex.upper()
        )


phishing_analyst_agent = (
    PhishingAnalystAgent()
)