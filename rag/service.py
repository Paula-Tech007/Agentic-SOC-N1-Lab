"""
Serviço integrado da camada Knowledge / RAG
do Agentic SOC N1 Lab.

Fase 5.6 — Integração automática RAG → AG-08.

Este serviço conecta:

- busca semântica local;
- adaptação para KnowledgeChunk;
- criação da AgentExecutionRequest;
- execução do AG-08 Knowledge / RAG Agent.

Fluxo:

Query
    ↓
RAGRetriever
    ↓
RAGSearchResult
    ↓
RAGKnowledgeAdapter
    ↓
retrieved_chunks
    ↓
AgentExecutionRequest
    ↓
AG-08
    ↓
KnowledgeResult

Importante:

Este serviço NÃO implementa o fluxo SOC completo
Supervisor → Especialistas → Supervisor.

Esse fluxo continua pertencendo à Fase 7.

Princípios:

- retrieval local;
- nenhuma busca web;
- nenhuma evidência inventada;
- nenhuma resposta inventada pelo serviço;
- nenhuma confiança inventada pelo serviço;
- alerta obrigatório no case_snapshot;
- fail-closed se nenhum conhecimento for recuperado.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agents.knowledge import (
    KnowledgeRAGAgent,
)

from core.orchestrator import (
    AgentExecutionRequest,
    AgentRuntimeContext,
)

from rag.retrieval.adapter import (
    RAGKnowledgeAdapter,
)

from rag.retrieval.search import (
    RAGRetriever,
)


class RAGKnowledgeService:
    """
    Serviço de alto nível que liga
    retrieval local ao AG-08.
    """

    def __init__(
        self,
        retriever: RAGRetriever,
        *,
        adapter: (
            RAGKnowledgeAdapter | None
        ) = None,
        agent: (
            KnowledgeRAGAgent | None
        ) = None,
    ) -> None:
        """
        Inicializa o serviço.
        """

        if not isinstance(
            retriever,
            RAGRetriever,
        ):
            raise TypeError(
                "retriever precisa ser uma "
                "instância de RAGRetriever."
            )

        self._retriever = retriever

        self._adapter = (
            adapter
            if adapter is not None
            else RAGKnowledgeAdapter()
        )

        if not isinstance(
            self._adapter,
            RAGKnowledgeAdapter,
        ):
            raise TypeError(
                "adapter precisa ser uma "
                "instância de "
                "RAGKnowledgeAdapter."
            )

        self._agent = (
            agent
            if agent is not None
            else KnowledgeRAGAgent()
        )

        if not isinstance(
            self._agent,
            KnowledgeRAGAgent,
        ):
            raise TypeError(
                "agent precisa ser uma "
                "instância de "
                "KnowledgeRAGAgent."
            )

    @property
    def retriever(
        self,
    ) -> RAGRetriever:
        """
        Retorna retrieval configurado.
        """

        return self._retriever

    @property
    def adapter(
        self,
    ) -> RAGKnowledgeAdapter:
        """
        Retorna adaptador RAG.
        """

        return self._adapter

    @property
    def agent(
        self,
    ) -> KnowledgeRAGAgent:
        """
        Retorna AG-08 utilizado.
        """

        return self._agent

    def execute(
        self,
        *,
        query: str,
        answer: str,
        confidence: int,
        case_snapshot: Mapping[str, Any],
        execution_id: str,
        case_id: str,
        correlation_id: str,
        case_version: int,
        evidence_references: (
            Sequence[str] | None
        ) = None,
        knowledge_id: str | None = None,
        top_k: int | None = None,
        min_similarity: (
            float | None
        ) = None,
        step_number: int = 1,
        max_steps: int = 20,
        retry_count: int = 0,
        max_retries: int = 2,
        timeout_seconds: int = 30,
    ) -> dict[str, Any]:
        """
        Executa retrieval e entrega
        o resultado ao AG-08.

        Retorna:

        {
            "search_result": ...,
            "agent_result": ...
        }
        """

        normalized_snapshot = (
            self._validate_case_snapshot(
                case_snapshot
            )
        )

        search_result = (
            self._retriever.search(
                query=query,
                top_k=top_k,
                min_similarity=(
                    min_similarity
                ),
            )
        )

        if not search_result.hits:
            raise ValueError(
                "Nenhum conhecimento "
                "relevante foi recuperado "
                "para a consulta."
            )

        payload = (
            self._adapter
            .build_agent_payload(
                result=search_result,
                answer=answer,
                confidence=confidence,
                evidence_references=(
                    evidence_references
                ),
                knowledge_id=(
                    knowledge_id
                ),
            )
        )

        request = AgentExecutionRequest(
            execution_id=(
                self._required_string(
                    execution_id,
                    field_name=(
                        "execution_id"
                    ),
                )
            ),
            agent_id="AG-08",
            case_id=(
                self._required_string(
                    case_id,
                    field_name="case_id",
                )
            ),
            correlation_id=(
                self._required_string(
                    correlation_id,
                    field_name=(
                        "correlation_id"
                    ),
                )
            ),
            case_version=(
                self._validate_non_negative_int(
                    case_version,
                    field_name=(
                        "case_version"
                    ),
                )
            ),
            runtime=AgentRuntimeContext(
                step_number=(
                    self._validate_positive_int(
                        step_number,
                        field_name=(
                            "step_number"
                        ),
                    )
                ),
                max_steps=(
                    self._validate_positive_int(
                        max_steps,
                        field_name=(
                            "max_steps"
                        ),
                    )
                ),
                retry_count=(
                    self._validate_non_negative_int(
                        retry_count,
                        field_name=(
                            "retry_count"
                        ),
                    )
                ),
                max_retries=(
                    self._validate_non_negative_int(
                        max_retries,
                        field_name=(
                            "max_retries"
                        ),
                    )
                ),
                timeout_seconds=(
                    self._validate_positive_int(
                        timeout_seconds,
                        field_name=(
                            "timeout_seconds"
                        ),
                    )
                ),
            ),
            case_snapshot=(
                normalized_snapshot
            ),
            input_payload=payload,
        )

        agent_result = (
            self._agent.execute(
                request
            )
        )

        return {
            "search_result": (
                search_result
            ),
            "agent_result": (
                agent_result
            ),
        }

    @staticmethod
    def _validate_case_snapshot(
        value: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Valida snapshot mínimo
        exigido pelo AG-08.
        """

        if not isinstance(
            value,
            Mapping,
        ):
            raise TypeError(
                "case_snapshot precisa "
                "ser um Mapping."
            )

        snapshot = dict(
            value
        )

        alert = snapshot.get(
            "alert"
        )

        if not isinstance(
            alert,
            Mapping,
        ):
            raise ValueError(
                "case_snapshot precisa "
                "possuir um objeto 'alert'."
            )

        alert_id = alert.get(
            "alert_id"
        )

        if not isinstance(
            alert_id,
            str,
        ):
            raise ValueError(
                "case_snapshot.alert.alert_id "
                "precisa ser string."
            )

        if not alert_id.strip():
            raise ValueError(
                "case_snapshot.alert.alert_id "
                "não pode ser vazio."
            )

        return snapshot

    @staticmethod
    def _required_string(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """
        Valida texto obrigatório.
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
    def _validate_positive_int(
        value: object,
        *,
        field_name: str,
    ) -> int:
        """
        Valida inteiro maior que zero.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser inteiro."
            )

        if value < 1:
            raise ValueError(
                f"{field_name} precisa "
                "ser maior que zero."
            )

        return value

    @staticmethod
    def _validate_non_negative_int(
        value: object,
        *,
        field_name: str,
    ) -> int:
        """
        Valida inteiro maior ou igual a zero.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "ser inteiro."
            )

        if value < 0:
            raise ValueError(
                f"{field_name} não pode "
                "ser negativo."
            )

        return value

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        da integração.
        """

        return {
            "integration": (
                "RAG_KNOWLEDGE_SERVICE"
            ),
            "retrieval": True,
            "adapter": True,
            "agent": "AG-08",
            "local_only": True,
            "web_search": False,
            "invents_answer": False,
            "invents_confidence": False,
            "requires_alert": True,
            "phase7_orchestration": False,
        }