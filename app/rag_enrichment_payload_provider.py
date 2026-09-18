"""
Extensão RAG do EnrichmentPayloadProvider
da Fase 7.3 do Agentic SOC N1 Lab.

Responsabilidades:

- preservar os payloads já validados
  de AG-04, AG-05 e AG-06;
- executar retrieval local autorizado
  quando o especialista selecionado
  for AG-08;
- converter RAGSearchResult para o
  contrato oficial do KnowledgeRAGAgent;
- nunca inventar chunks;
- nunca inventar evidência;
- derivar a confiança exclusivamente
  do score de retrieval;
- utilizar conteúdo recuperado como
  resposta factual do RAG.

Fluxo:

EnrichmentPayloadProvider
    |
    +--> AG-04
    +--> AG-05
    +--> AG-06

RAGEnrichmentPayloadProvider
    |
    +--> AG-08
            |
            RAGRetriever
            |
            RAGSearchResult
            |
            RAGKnowledgeAdapter
            |
            input_payload AG-08

Esta classe não executa o AG-08.

Ela somente prepara o payload.

A execução do especialista permanece
sob controle do Supervisor / Orchestrator.
"""

from __future__ import annotations

from typing import Any

from app.enrichment_payload_provider import (
    EnrichmentPayloadProvider,
)

from core.state import (
    CaseState,
)

from rag.retrieval import (
    RAGKnowledgeAdapter,
    RAGRetriever,
)

from tools import (
    ToolRuntime,
)


RAG_ENABLED_ENRICHMENT_AGENTS = (
    "AG-04",
    "AG-05",
    "AG-06",
    "AG-08",
)


class RAGEnrichmentPayloadProvider(
    EnrichmentPayloadProvider
):
    """
    Provider de enriquecimento com suporte
    ao Knowledge / RAG Agent.

    AG-04, AG-05 e AG-06 continuam sendo
    atendidos pela implementação base.

    AG-08 utiliza exclusivamente retrieval
    local autorizado.
    """

    def __init__(
        self,
        tool_runtime: ToolRuntime,
        rag_retriever: RAGRetriever,
        *,
        rag_adapter: (
            RAGKnowledgeAdapter
            | None
        ) = None,
    ) -> None:
        """
        Inicializa o provider.

        Nenhuma consulta RAG é executada
        durante a construção.
        """

        super().__init__(
            tool_runtime
        )

        if not isinstance(
            rag_retriever,
            RAGRetriever,
        ):
            raise TypeError(
                "rag_retriever precisa ser "
                "RAGRetriever."
            )

        if (
            rag_adapter is not None
            and not isinstance(
                rag_adapter,
                RAGKnowledgeAdapter,
            )
        ):
            raise TypeError(
                "rag_adapter precisa ser "
                "RAGKnowledgeAdapter ou None."
            )

        self._rag_retriever = (
            rag_retriever
        )

        self._rag_adapter = (
            rag_adapter
            if rag_adapter is not None
            else RAGKnowledgeAdapter()
        )

    @property
    def rag_retriever(
        self,
    ) -> RAGRetriever:
        """
        Retorna o retriever utilizado
        pelo provider.
        """

        return self._rag_retriever

    @property
    def rag_adapter(
        self,
    ) -> RAGKnowledgeAdapter:
        """
        Retorna o adaptador RAG → AG-08.
        """

        return self._rag_adapter

    def build_payload(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Constrói payload para o especialista.

        AG-08 recebe tratamento RAG.

        Os demais agentes continuam
        delegados ao provider original.
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

        if normalized_agent_id == "AG-08":
            return (
                self._build_knowledge_payload(
                    case_state
                )
            )

        return super().build_payload(
            case_state=case_state,
            agent_id=normalized_agent_id,
        )

    def _build_knowledge_payload(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Recupera conhecimento local autorizado
        e produz input_payload compatível
        com o AG-08.

        A resposta utilizada pelo agente
        é derivada diretamente do conteúdo
        do melhor chunk recuperado.

        A confiança é derivada exclusivamente
        do similarity_score do melhor hit.
        """

        query = self._build_rag_query(
            case_state
        )

        search_result = (
            self._rag_retriever.search(
                query=query
            )
        )

        if not search_result.hits:
            raise RuntimeError(
                "AG-08 não encontrou "
                "conhecimento relevante "
                "na base RAG autorizada."
            )

        best_hit = (
            search_result.hits[0]
        )

        answer = (
            best_hit
            .chunk
            .content
            .strip()
        )

        if not answer:
            raise RuntimeError(
                "AG-08 recuperou chunk "
                "sem conteúdo utilizável."
            )

        confidence = (
            self._confidence_from_similarity(
                best_hit.similarity_score
            )
        )

        return (
            self._rag_adapter
            .build_agent_payload(
                result=search_result,
                answer=answer,
                confidence=confidence,
                evidence_references=[],
            )
        )

    def _build_rag_query(
        self,
        case_state: CaseState,
    ) -> str:
        """
        Cria consulta RAG exclusivamente
        a partir de informações observáveis
        existentes no CaseState.

        Nenhuma conclusão é adicionada
        à consulta.
        """

        parts: list[str] = []

        event_type = getattr(
            case_state
            .alert
            .event
            .event_type,
            "value",
            None,
        )

        if isinstance(
            event_type,
            str,
        ):
            normalized = event_type.strip()

            if normalized:
                parts.append(
                    normalized
                )

        category = (
            self._optional_string(
                case_state
                .alert
                .event
                .category
            )
        )

        if category is not None:
            parts.append(
                category
            )

        rule_name = (
            self._optional_string(
                case_state
                .alert
                .source
                .rule_name
            )
        )

        if rule_name is not None:
            parts.append(
                rule_name
            )

        triage = (
            case_state.triage
        )

        if triage is not None:
            triage_data = (
                self._model_data(
                    triage
                )
            )

            alert_type = (
                self._enum_or_string(
                    triage_data.get(
                        "alert_type"
                    )
                )
            )

            if (
                alert_type is not None
                and alert_type
                not in parts
            ):
                parts.append(
                    alert_type
                )

            severity = (
                self._enum_or_string(
                    triage_data.get(
                        "severity"
                    )
                )
            )

            if severity is not None:
                parts.append(
                    severity
                )

            missing_data = (
                triage_data.get(
                    "missing_data"
                )
            )

            if isinstance(
                missing_data,
                (list, tuple),
            ):
                for item in missing_data:
                    normalized_item = (
                        self._optional_string(
                            item
                        )
                    )

                    if (
                        normalized_item
                        is not None
                    ):
                        parts.append(
                            normalized_item
                        )

        if not parts:
            raise RuntimeError(
                "Não foi possível construir "
                "consulta RAG a partir "
                "do CaseState."
            )

        unique_parts: list[str] = []

        for part in parts:
            if (
                part
                not in unique_parts
            ):
                unique_parts.append(
                    part
                )

        return " ".join(
            unique_parts
        )

    @staticmethod
    def _confidence_from_similarity(
        similarity_score: Any,
    ) -> int:
        """
        Converte similarity_score para
        confiança inteira de 0 a 100.

        Não cria confiança arbitrária.

        Exemplos:

        0.59 -> 59
        0.80 -> 80
        1.00 -> 100

        Valores fora do intervalo são
        limitados defensivamente.
        """

        if (
            isinstance(
                similarity_score,
                bool,
            )
            or not isinstance(
                similarity_score,
                (int, float),
            )
        ):
            raise RuntimeError(
                "similarity_score do RAG "
                "é inválido."
            )

        normalized = float(
            similarity_score
        )

        if normalized < 0.0:
            normalized = 0.0

        if normalized > 1.0:
            normalized = 1.0

        return int(
            round(
                normalized
                * 100
            )
        )


__all__ = [
    "RAG_ENABLED_ENRICHMENT_AGENTS",
    "RAGEnrichmentPayloadProvider",
]