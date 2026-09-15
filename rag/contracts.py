"""
Contratos internos da camada RAG
do Agentic SOC N1 Lab.

Fase 5.0 — Fundação do Knowledge / RAG.

Este módulo define os objetos utilizados entre:

- ingestão;
- chunking;
- embeddings;
- índice vetorial;
- retrieval.

Fluxo:

RAGDocument
    ↓
RAGChunk
    ↓
RAGEmbeddedChunk
    ↓
RAGSearchHit
    ↓
RAGSearchResult
    ↓
KnowledgeChunk
    ↓
AG-08 Knowledge / RAG Agent

Princípios:

- contratos imutáveis;
- campos extras proibidos;
- tipos de conhecimento controlados;
- conteúdo textual obrigatório;
- embeddings numéricos e não vazios;
- scores de similaridade entre 0 e 1;
- metadados preservados;
- nenhuma credencial armazenada.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from rag.config import (
    ALLOWED_KNOWLEDGE_TYPES,
)


class RAGDocument(BaseModel):
    """
    Documento autorizado carregado da base
    local de conhecimento.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    document_id: str = Field(
        ...,
        min_length=1,
    )

    document_name: str = Field(
        ...,
        min_length=1,
    )

    document_type: str = Field(
        ...,
        min_length=1,
    )

    source_path: str = Field(
        ...,
        min_length=1,
    )

    content: str = Field(
        ...,
        min_length=1,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    loaded_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @field_validator(
        "document_id",
        "document_name",
        "source_path",
        "content",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Impede campos textuais obrigatórios vazios.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Campo textual obrigatório "
                "não pode ser vazio."
            )

        return cleaned

    @field_validator(
        "document_type"
    )
    @classmethod
    def validate_document_type(
        cls,
        value: str,
    ) -> str:
        """
        Permite somente os tipos oficiais
        de conhecimento do projeto.
        """

        cleaned = value.strip().lower()

        if (
            cleaned
            not in ALLOWED_KNOWLEDGE_TYPES
        ):
            raise ValueError(
                "document_type não autorizado. "
                "Tipos permitidos: "
                + ", ".join(
                    ALLOWED_KNOWLEDGE_TYPES
                )
            )

        return cleaned


class RAGChunk(BaseModel):
    """
    Trecho textual produzido pelo processo
    de chunking.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    chunk_id: str = Field(
        ...,
        min_length=1,
    )

    document_id: str = Field(
        ...,
        min_length=1,
    )

    document_name: str = Field(
        ...,
        min_length=1,
    )

    document_type: str = Field(
        ...,
        min_length=1,
    )

    section: str | None = None

    content: str = Field(
        ...,
        min_length=1,
    )

    source_path: str = Field(
        ...,
        min_length=1,
    )

    position: int = Field(
        ...,
        ge=0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @field_validator(
        "chunk_id",
        "document_id",
        "document_name",
        "source_path",
        "content",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Impede textos obrigatórios vazios.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Campo textual obrigatório "
                "não pode ser vazio."
            )

        return cleaned

    @field_validator(
        "document_type"
    )
    @classmethod
    def validate_document_type(
        cls,
        value: str,
    ) -> str:
        """
        Valida tipo oficial de conhecimento.
        """

        cleaned = value.strip().lower()

        if (
            cleaned
            not in ALLOWED_KNOWLEDGE_TYPES
        ):
            raise ValueError(
                "document_type não autorizado."
            )

        return cleaned

    @field_validator(
        "section"
    )
    @classmethod
    def normalize_section(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normaliza seção opcional.
        """

        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


class RAGEmbeddedChunk(BaseModel):
    """
    Chunk associado ao vetor numérico
    produzido pelo modelo de embeddings.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    chunk: RAGChunk

    embedding: list[float] = Field(
        ...,
        min_length=1,
    )

    embedding_model: str = Field(
        ...,
        min_length=1,
    )

    embedded_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @field_validator(
        "embedding_model"
    )
    @classmethod
    def validate_embedding_model(
        cls,
        value: str,
    ) -> str:
        """
        Modelo de embedding não pode ser vazio.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "embedding_model não pode "
                "ser vazio."
            )

        return cleaned

    @field_validator(
        "embedding"
    )
    @classmethod
    def validate_embedding(
        cls,
        value: list[float],
    ) -> list[float]:
        """
        Garante vetor numérico válido.
        """

        if not value:
            raise ValueError(
                "embedding não pode ser vazio."
            )

        result: list[float] = []

        for item in value:
            if isinstance(
                item,
                bool,
            ):
                raise ValueError(
                    "embedding deve conter "
                    "somente números."
                )

            if not isinstance(
                item,
                (int, float),
            ):
                raise ValueError(
                    "embedding deve conter "
                    "somente números."
                )

            result.append(
                float(item)
            )

        return result


class RAGSearchHit(BaseModel):
    """
    Resultado individual de uma busca
    semântica no índice RAG.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    chunk: RAGChunk

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )


class RAGSearchResult(BaseModel):
    """
    Resultado consolidado de uma consulta
    semântica ao índice local.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    query: str = Field(
        ...,
        min_length=1,
    )

    hits: list[RAGSearchHit] = Field(
        default_factory=list,
    )

    top_k: int = Field(
        ...,
        ge=1,
    )

    min_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    searched_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @field_validator(
        "query"
    )
    @classmethod
    def validate_query(
        cls,
        value: str,
    ) -> str:
        """
        Consulta não pode ser vazia.
        """

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "query não pode ser vazia."
            )

        return cleaned