"""
Adaptador entre o Retrieval RAG e o AG-08
Knowledge / RAG Agent.

Fase 5.6 — Integração RAG → AG-08.

Responsabilidades:

- receber RAGSearchResult;
- converter RAGSearchHit em KnowledgeChunk;
- preservar origem, score e metadados;
- preparar retrieved_chunks no formato oficial;
- preparar payload compatível com AG-08;
- nunca inventar resposta;
- nunca inventar confiança;
- nunca inventar evidências.

Fluxo:

RAGSearchResult
    ↓
RAGKnowledgeAdapter
    ↓
KnowledgeChunk
    ↓
input_payload
    ↓
AG-08 Knowledge / RAG Agent
    ↓
KnowledgeResult

Princípios:

- retrieval recupera;
- fonte comprova;
- agente estrutura;
- resposta e confiança precisam ser
  fornecidas explicitamente;
- nenhum chunk externo ao resultado
  pode ser introduzido.
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import Any

from core.schemas import KnowledgeChunk
from rag.contracts import (
    RAGSearchHit,
    RAGSearchResult,
)


class RAGKnowledgeAdapter:
    """
    Converte resultados internos do RAG
    para os contratos oficiais do AG-08.
    """

    def to_knowledge_chunk(
        self,
        hit: RAGSearchHit,
    ) -> KnowledgeChunk:
        """
        Converte um único RAGSearchHit
        em KnowledgeChunk oficial.
        """

        if not isinstance(
            hit,
            RAGSearchHit,
        ):
            raise TypeError(
                "hit precisa ser uma "
                "instância de RAGSearchHit."
            )

        source_chunk = hit.chunk

        metadata = dict(
            source_chunk.metadata
        )

        metadata.update(
            {
                "rag_chunk_id": (
                    source_chunk.chunk_id
                ),
                "rag_document_id": (
                    source_chunk.document_id
                ),
                "rag_position": (
                    source_chunk.position
                ),
                "retrieval_source": (
                    "LOCAL_RAG_INDEX"
                ),
                "local_only": True,
            }
        )

        return KnowledgeChunk(
            chunk_id=(
                source_chunk.chunk_id
            ),
            document_name=(
                source_chunk.document_name
            ),
            document_type=(
                source_chunk.document_type
            ),
            section=(
                source_chunk.section
            ),
            content=(
                source_chunk.content
            ),
            similarity_score=(
                hit.similarity_score
            ),
            source_path=(
                source_chunk.source_path
            ),
            metadata=metadata,
        )

    def to_knowledge_chunks(
        self,
        result: RAGSearchResult,
    ) -> list[KnowledgeChunk]:
        """
        Converte todos os hits recuperados
        em KnowledgeChunk.
        """

        if not isinstance(
            result,
            RAGSearchResult,
        ):
            raise TypeError(
                "result precisa ser uma "
                "instância de RAGSearchResult."
            )

        return [
            self.to_knowledge_chunk(
                hit
            )
            for hit in result.hits
        ]

    def to_retrieved_chunks_payload(
        self,
        result: RAGSearchResult,
    ) -> list[dict[str, Any]]:
        """
        Produz exatamente o formato
        esperado em input_payload.retrieved_chunks.
        """

        chunks = (
            self.to_knowledge_chunks(
                result
            )
        )

        return [
            chunk.model_dump(
                mode="json"
            )
            for chunk in chunks
        ]

    def build_agent_payload(
        self,
        *,
        result: RAGSearchResult,
        answer: str,
        confidence: int,
        evidence_references: (
            Sequence[str]
            | None
        ) = None,
        knowledge_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Prepara input_payload compatível
        com KnowledgeRAGAgent.

        answer e confidence são obrigatórios
        e nunca são inferidos pelo adaptador.
        """

        if not isinstance(
            result,
            RAGSearchResult,
        ):
            raise TypeError(
                "result precisa ser uma "
                "instância de RAGSearchResult."
            )

        if not result.hits:
            raise ValueError(
                "Não é possível preparar "
                "payload do AG-08 sem "
                "chunks recuperados."
            )

        normalized_answer = (
            self._required_string(
                answer,
                field_name="answer",
            )
        )

        normalized_confidence = (
            self._validate_confidence(
                confidence
            )
        )

        normalized_evidence = (
            self._normalize_evidence_references(
                evidence_references
            )
        )

        payload: dict[str, Any] = {
            "query": result.query,
            "answer": normalized_answer,
            "retrieved_chunks": (
                self.to_retrieved_chunks_payload(
                    result
                )
            ),
            "confidence": (
                normalized_confidence
            ),
            "evidence_references": (
                normalized_evidence
            ),
        }

        if knowledge_id is not None:
            payload[
                "knowledge_id"
            ] = self._required_string(
                knowledge_id,
                field_name="knowledge_id",
            )

        return payload

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
    def _validate_confidence(
        value: object,
    ) -> int:
        """
        Valida confiança de 0 a 100.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "confidence precisa "
                "ser inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "confidence precisa "
                "ser inteiro."
            )

        if (
            value < 0
            or value > 100
        ):
            raise ValueError(
                "confidence precisa estar "
                "entre 0 e 100."
            )

        return value

    @staticmethod
    def _normalize_evidence_references(
        value: Sequence[str] | None,
    ) -> list[str]:
        """
        Normaliza referências de evidência
        fornecidas pelo chamador.

        O adaptador não cria evidências.
        """

        if value is None:
            return []

        if isinstance(
            value,
            (str, bytes),
        ):
            raise ValueError(
                "evidence_references precisa "
                "ser uma sequência de strings."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(
                item,
                str,
            ):
                raise ValueError(
                    "evidence_references contém "
                    "valor que não é string."
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

    def safe_summary(
        self,
    ) -> Mapping[str, object]:
        """
        Retorna resumo seguro
        do adaptador.
        """

        return {
            "integration": (
                "RAG_TO_AG08"
            ),
            "source": (
                "RAGSearchResult"
            ),
            "target": (
                "KnowledgeChunk"
            ),
            "invents_chunks": False,
            "invents_answer": False,
            "invents_confidence": False,
            "invents_evidence": False,
            "local_only": True,
        }