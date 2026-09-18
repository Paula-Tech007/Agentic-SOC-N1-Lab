"""
Provider completo de enriquecimento
do Agentic SOC N1 Lab.

Esta camada finaliza a composição
de payloads da Fase 7.3 sem repetir
implementações já validadas.

Herança:

EnrichmentPayloadProvider
    |
    +-- AG-04 Threat Intelligence
    +-- AG-05 Identity
    +-- AG-06 Asset

RAGEnrichmentPayloadProvider
    |
    +-- AG-08 Knowledge / RAG

FullEnrichmentPayloadProvider
    |
    +-- AG-07 Phishing / Email

Portanto, este módulo acrescenta somente
o comportamento que ainda faltava para
o AG-07.

Princípios:

- nenhuma URL é aberta;
- nenhum anexo é baixado;
- nenhum anexo é executado;
- nenhuma evidência é inventada;
- ToolRuntime continua soberano;
- integrações continuam read-only;
- dados ausentes permanecem ausentes;
- conclusão não comprovada permanece
  INCONCLUSIVE;
- falhas relevantes fecham o fluxo.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.rag_enrichment_payload_provider import (
    RAGEnrichmentPayloadProvider,
)

from core.state import (
    CaseState,
)


FULL_ENRICHMENT_AGENT_IDS = (
    "AG-04",
    "AG-05",
    "AG-06",
    "AG-07",
    "AG-08",
)


_VALID_CLASSIFICATIONS = frozenset(
    {
        "FALSE_POSITIVE",
        "BENIGN_POSITIVE",
        "SUSPICIOUS",
        "CONFIRMED_INCIDENT",
        "INCONCLUSIVE",
    }
)


_VALID_SEVERITIES = frozenset(
    {
        "INFORMATIONAL",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
)


class FullEnrichmentPayloadProvider(
    RAGEnrichmentPayloadProvider
):
    """
    Provider completo da etapa
    de enriquecimento.

    Mantém:

    AG-04
        implementação original;

    AG-05
        implementação original;

    AG-06
        implementação original;

    AG-08
        implementação RAG original.

    Acrescenta somente:

    AG-07
        composição defensiva de
        metadados de Email / Phishing.
    """

    def build_payload(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Constrói o payload compatível
        com o especialista solicitado.

        AG-07 é tratado nesta classe.

        Demais agentes continuam
        delegados às implementações
        já validadas.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        normalized_agent_id = (
            self._required_string(
                agent_id,
                "agent_id",
            )
        )

        if normalized_agent_id == "AG-07":
            return (
                self._build_phishing_payload(
                    case_state
                )
            )

        return super().build_payload(
            case_state=case_state,
            agent_id=(
                normalized_agent_id
            ),
        )

    # ============================================================
    # AG-07
    # ============================================================

    def _build_phishing_payload(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Constrói input_payload para
        o AG-07 utilizando exclusivamente
        resultados obtidos pelo ToolRuntime.

        Ferramentas utilizadas:

        - email.get_message_metadata;
        - email.get_headers;
        - email.get_authentication_results;
        - email.get_attachment_metadata.

        Nenhuma operação ativa sobre
        a mensagem é realizada.
        """

        event_type = (
            self._enum_or_string(
                case_state
                .alert
                .event
                .event_type
            )
        )

        if event_type != "PHISHING":
            raise RuntimeError(
                "AG-07 somente pode preparar "
                "payload para alerta PHISHING."
            )

        message_id = (
            self._message_id_candidate(
                case_state
            )
        )

        if message_id is None:
            raise RuntimeError(
                "AG-07 solicitado sem "
                "message_id disponível "
                "no evento."
            )

        tool_ids = (
            "email.get_message_metadata",
            "email.get_headers",
            (
                "email."
                "get_authentication_results"
            ),
            (
                "email."
                "get_attachment_metadata"
            ),
        )

        results: dict[
            str,
            dict[str, Any],
        ] = {}

        sources: list[str] = []

        errors: list[str] = []

        for tool_id in tool_ids:
            try:
                tool_result = (
                    self._execute_tool(
                        case_state=case_state,
                        agent_id="AG-07",
                        tool_id=tool_id,
                        input_payload={
                            "message_id": (
                                message_id
                            ),
                        },
                    )
                )

            except RuntimeError as exc:
                errors.append(
                    str(exc)
                )
                continue

            result_data = (
                self._tool_output_result(
                    tool_result
                )
            )

            if not isinstance(
                result_data,
                Mapping,
            ):
                errors.append(
                    f"{tool_id} retornou "
                    "resultado não estruturado."
                )
                continue

            results[tool_id] = dict(
                result_data
            )

            source = (
                self._tool_source(
                    tool_result,
                    default="EMAIL",
                )
            )

            if source not in sources:
                sources.append(
                    source
                )

        if not results:
            raise RuntimeError(
                "AG-07 não recebeu nenhum "
                "resultado comprovado "
                "da integração Email."
            )

        metadata = results.get(
            "email.get_message_metadata",
            {},
        )

        headers = results.get(
            "email.get_headers",
            {},
        )

        authentication_data = (
            results.get(
                (
                    "email."
                    "get_authentication_results"
                ),
                {},
            )
        )

        attachment_data = (
            results.get(
                (
                    "email."
                    "get_attachment_metadata"
                ),
                {},
            )
        )

        sender = self._first_string(
            (
                metadata.get(
                    "sender"
                ),
                metadata.get(
                    "from"
                ),
                headers.get(
                    "from"
                ),
                headers.get(
                    "sender"
                ),
            )
        )

        recipients = (
            self._merge_string_values(
                metadata.get(
                    "recipients"
                ),
                metadata.get(
                    "to"
                ),
                headers.get(
                    "recipients"
                ),
                headers.get(
                    "to"
                ),
            )
        )

        subject = self._first_string(
            (
                metadata.get(
                    "subject"
                ),
                headers.get(
                    "subject"
                ),
            )
        )

        urls = (
            self._merge_string_values(
                metadata.get(
                    "urls"
                ),
                headers.get(
                    "urls"
                ),
            )
        )

        (
            attachment_names,
            attachment_hashes,
        ) = self._attachment_context(
            attachment_data
        )

        authentication = {
            "spf": self._first_string(
                (
                    authentication_data.get(
                        "spf"
                    ),
                    authentication_data.get(
                        "spf_result"
                    ),
                )
            ),
            "dkim": self._first_string(
                (
                    authentication_data.get(
                        "dkim"
                    ),
                    authentication_data.get(
                        "dkim_result"
                    ),
                )
            ),
            "dmarc": self._first_string(
                (
                    authentication_data.get(
                        "dmarc"
                    ),
                    authentication_data.get(
                        "dmarc_result"
                    ),
                )
            ),
        }

        suspicious_indicators = (
            self._merge_string_values(
                metadata.get(
                    "suspicious_indicators"
                ),
                headers.get(
                    "suspicious_indicators"
                ),
                authentication_data.get(
                    "suspicious_indicators"
                ),
                attachment_data.get(
                    "suspicious_indicators"
                ),
                metadata.get(
                    "risk_factors"
                ),
                authentication_data.get(
                    "risk_factors"
                ),
                attachment_data.get(
                    "risk_factors"
                ),
            )
        )

        evidence_references = (
            self._merge_string_values(
                metadata.get(
                    "evidence_references"
                ),
                headers.get(
                    "evidence_references"
                ),
                authentication_data.get(
                    "evidence_references"
                ),
                attachment_data.get(
                    "evidence_references"
                ),
            )
        )

        classification = (
            self._classification_from_results(
                metadata=metadata,
                authentication_data=(
                    authentication_data
                ),
                attachment_data=(
                    attachment_data
                ),
            )
        )

        severity = (
            self._severity_from_results(
                case_state=case_state,
                metadata=metadata,
                authentication_data=(
                    authentication_data
                ),
                attachment_data=(
                    attachment_data
                ),
            )
        )

        confidence = max(
            self._explicit_confidence(
                value
            )
            for value in results.values()
        )

        summary = self._first_string(
            (
                metadata.get(
                    "summary"
                ),
                headers.get(
                    "summary"
                ),
                authentication_data.get(
                    "summary"
                ),
                attachment_data.get(
                    "summary"
                ),
            )
        )

        if summary is None:
            summary = (
                "Metadados defensivos de "
                "phishing coletados para a "
                f"mensagem {message_id}; "
                "nenhuma conclusão adicional "
                "foi inferida."
            )

        return {
            "phishing_id": (
                self._stable_id(
                    prefix="PHISH",
                    value=message_id,
                )
            ),
            "sender": sender,
            "recipients": recipients,
            "subject": subject,
            "urls": urls,
            "attachment_names": (
                attachment_names
            ),
            "attachment_hashes": (
                attachment_hashes
            ),
            "authentication": (
                authentication
            ),
            "suspicious_indicators": (
                suspicious_indicators
            ),
            "evidence_references": (
                evidence_references
            ),
            "classification": (
                classification
            ),
            "severity": severity,
            "confidence": confidence,
            "summary": summary,
            "queried_sources": sources,
            "errors": errors,
        }

    # ============================================================
    # MESSAGE
    # ============================================================

    def _message_id_candidate(
        self,
        case_state: CaseState,
    ) -> str | None:
        """
        Obtém somente um identificador
        explicitamente disponível
        no evento original.
        """

        raw_event = (
            self._raw_event(
                case_state
            )
        )

        return self._first_string(
            (
                raw_event.get(
                    "message_id"
                ),
                raw_event.get(
                    "email_message_id"
                ),
                raw_event.get(
                    "internet_message_id"
                ),
            )
        )

    # ============================================================
    # ATTACHMENTS
    # ============================================================

    def _attachment_context(
        self,
        attachment_data: Mapping[
            str,
            Any,
        ],
    ) -> tuple[
        list[str],
        list[str],
    ]:
        """
        Extrai apenas nomes e hashes
        já presentes na resposta
        da ferramenta.

        Não baixa conteúdo.
        """

        attachment_names: list[str] = []

        attachment_hashes: list[str] = []

        attachments = attachment_data.get(
            "attachments"
        )

        if isinstance(
            attachments,
            (list, tuple),
        ):
            for attachment in attachments:
                if not isinstance(
                    attachment,
                    Mapping,
                ):
                    continue

                name = self._first_string(
                    (
                        attachment.get(
                            "name"
                        ),
                        attachment.get(
                            "filename"
                        ),
                    )
                )

                if (
                    name is not None
                    and name
                    not in attachment_names
                ):
                    attachment_names.append(
                        name
                    )

                for hash_key in (
                    "sha256",
                    "sha1",
                    "md5",
                    "hash",
                ):
                    hash_value = (
                        self._optional_string(
                            attachment.get(
                                hash_key
                            )
                        )
                    )

                    if (
                        hash_value is not None
                        and hash_value
                        not in attachment_hashes
                    ):
                        attachment_hashes.append(
                            hash_value
                        )

        for value in (
            self._merge_string_values(
                attachment_data.get(
                    "attachment_names"
                ),
            )
        ):
            if value not in attachment_names:
                attachment_names.append(
                    value
                )

        for value in (
            self._merge_string_values(
                attachment_data.get(
                    "attachment_hashes"
                ),
                attachment_data.get(
                    "hashes"
                ),
            )
        ):
            if value not in attachment_hashes:
                attachment_hashes.append(
                    value
                )

        return (
            attachment_names,
            attachment_hashes,
        )

    # ============================================================
    # CLASSIFICATION
    # ============================================================

    def _classification_from_results(
        self,
        *,
        metadata: Mapping[str, Any],
        authentication_data: Mapping[
            str,
            Any,
        ],
        attachment_data: Mapping[
            str,
            Any,
        ],
    ) -> str:
        """
        Aceita somente classificação
        explicitamente fornecida.

        Sem conclusão explícita,
        permanece INCONCLUSIVE.
        """

        classification = (
            self._first_string(
                (
                    metadata.get(
                        "classification"
                    ),
                    metadata.get(
                        "final_classification"
                    ),
                    authentication_data.get(
                        "classification"
                    ),
                    attachment_data.get(
                        "classification"
                    ),
                )
            )
        )

        if classification is None:
            return "INCONCLUSIVE"

        normalized = (
            classification.upper()
        )

        if normalized not in (
            _VALID_CLASSIFICATIONS
        ):
            return "INCONCLUSIVE"

        return normalized

    # ============================================================
    # SEVERITY
    # ============================================================

    def _severity_from_results(
        self,
        *,
        case_state: CaseState,
        metadata: Mapping[str, Any],
        authentication_data: Mapping[
            str,
            Any,
        ],
        attachment_data: Mapping[
            str,
            Any,
        ],
    ) -> str:
        """
        Usa severidade explícita da
        integração quando disponível.

        Caso contrário, preserva a
        severidade inicial do alerta.

        Nenhuma severidade nova é
        inventada pelo provider.
        """

        severity = self._first_string(
            (
                metadata.get(
                    "severity"
                ),
                authentication_data.get(
                    "severity"
                ),
                attachment_data.get(
                    "severity"
                ),
                self._enum_or_string(
                    case_state
                    .alert
                    .initial_severity
                ),
            )
        )

        if severity is None:
            raise RuntimeError(
                "AG-07 não possui severidade "
                "válida disponível."
            )

        normalized = severity.upper()

        if normalized not in (
            _VALID_SEVERITIES
        ):
            raise RuntimeError(
                "AG-07 recebeu severidade "
                "fora do catálogo oficial."
            )

        return normalized

    # ============================================================
    # HELPERS
    # ============================================================

    @classmethod
    def _merge_string_values(
        cls,
        *values: Any,
    ) -> list[str]:
        """
        Une strings e coleções de
        strings sem duplicação.

        Tipos diferentes são ignorados.
        """

        output: list[str] = []

        for value in values:
            items: tuple[Any, ...]

            if isinstance(
                value,
                str,
            ):
                items = (
                    value,
                )

            elif isinstance(
                value,
                (list, tuple),
            ):
                items = tuple(
                    value
                )

            else:
                continue

            for item in items:
                normalized = (
                    cls._optional_string(
                        item
                    )
                )

                if (
                    normalized is not None
                    and normalized
                    not in output
                ):
                    output.append(
                        normalized
                    )

        return output


__all__ = [
    "FULL_ENRICHMENT_AGENT_IDS",
    "FullEnrichmentPayloadProvider",
]