"""
Serviço de embeddings da camada RAG
do Agentic SOC N1 Lab.

Fase 5.3 — Embeddings locais.

Responsabilidades:

- receber RAGChunk validado;
- gerar embedding numérico;
- validar o vetor retornado;
- preservar origem do chunk;
- registrar o modelo utilizado;
- produzir RAGEmbeddedChunk.

Em produção:

RAGChunk
    ↓
core.llm.create_embedding()
    ↓
Ollama local
    ↓
embeddinggemma
    ↓
RAGEmbeddedChunk

Em testes:

RAGChunk
    ↓
embedding_function controlada
    ↓
RAGEmbeddedChunk

Princípios:

- execução local;
- nenhum embedding inventado;
- vetores vazios são rejeitados;
- valores não numéricos são rejeitados;
- NaN e infinito são rejeitados;
- falha do modelo é propagada;
- nenhum dado externo arbitrário é consultado.
"""

from __future__ import annotations

from collections.abc import Callable
from math import isfinite

from core.config import EMBEDDING_MODEL
from core.llm import create_embedding
from rag.contracts import (
    RAGChunk,
    RAGEmbeddedChunk,
)


EmbeddingFunction = Callable[
    [str],
    list[float],
]


class RAGEmbeddingService:
    """
    Serviço responsável por transformar
    chunks do RAG em vetores numéricos.
    """

    def __init__(
        self,
        *,
        embedding_function: (
            EmbeddingFunction | None
        ) = None,
        embedding_model: str | None = None,
    ) -> None:
        """
        Inicializa o serviço.

        embedding_function:

        - None:
          utiliza core.llm.create_embedding;

        - função fornecida:
          utilizada em testes controlados.
        """

        self._embedding_function = (
            embedding_function
            if embedding_function is not None
            else create_embedding
        )

        if not callable(
            self._embedding_function
        ):
            raise TypeError(
                "embedding_function precisa "
                "ser chamável."
            )

        model = (
            embedding_model
            if embedding_model is not None
            else EMBEDDING_MODEL
        )

        if not isinstance(
            model,
            str,
        ):
            raise ValueError(
                "embedding_model precisa "
                "ser uma string."
            )

        model = model.strip()

        if not model:
            raise ValueError(
                "embedding_model não pode "
                "ser vazio."
            )

        self._embedding_model = model

    @property
    def embedding_model(
        self,
    ) -> str:
        """
        Retorna o modelo configurado.
        """

        return self._embedding_model

    def embed_chunk(
        self,
        chunk: RAGChunk,
    ) -> RAGEmbeddedChunk:
        """
        Gera embedding de um único chunk.
        """

        if not isinstance(
            chunk,
            RAGChunk,
        ):
            raise TypeError(
                "chunk precisa ser uma "
                "instância de RAGChunk."
            )

        raw_embedding = (
            self._embedding_function(
                chunk.content
            )
        )

        embedding = (
            self._validate_embedding(
                raw_embedding
            )
        )

        return RAGEmbeddedChunk(
            chunk=chunk,
            embedding=embedding,
            embedding_model=(
                self._embedding_model
            ),
        )

    def embed_chunks(
        self,
        chunks: (
            list[RAGChunk]
            | tuple[RAGChunk, ...]
        ),
    ) -> list[RAGEmbeddedChunk]:
        """
        Gera embeddings para vários chunks.

        Todos os vetores precisam possuir
        a mesma dimensão.
        """

        if not isinstance(
            chunks,
            (list, tuple),
        ):
            raise TypeError(
                "chunks precisa ser "
                "lista ou tupla."
            )

        results: list[
            RAGEmbeddedChunk
        ] = []

        expected_dimension: (
            int | None
        ) = None

        for chunk in chunks:
            embedded = (
                self.embed_chunk(
                    chunk
                )
            )

            dimension = len(
                embedded.embedding
            )

            if expected_dimension is None:
                expected_dimension = (
                    dimension
                )

            elif (
                dimension
                != expected_dimension
            ):
                raise ValueError(
                    "Todos os embeddings "
                    "precisam possuir a "
                    "mesma dimensão."
                )

            results.append(
                embedded
            )

        return results

    @staticmethod
    def _validate_embedding(
        value: object,
    ) -> list[float]:
        """
        Valida vetor retornado
        pelo modelo de embeddings.
        """

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "O gerador de embeddings "
                "precisa retornar lista "
                "ou tupla numérica."
            )

        if not value:
            raise ValueError(
                "Embedding retornado "
                "não pode ser vazio."
            )

        result: list[float] = []

        for position, item in enumerate(
            value
        ):
            if isinstance(
                item,
                bool,
            ):
                raise ValueError(
                    "Embedding contém valor "
                    "booleano na posição "
                    f"{position}."
                )

            if not isinstance(
                item,
                (int, float),
            ):
                raise ValueError(
                    "Embedding contém valor "
                    "não numérico na posição "
                    f"{position}."
                )

            numeric_value = float(
                item
            )

            if not isfinite(
                numeric_value
            ):
                raise ValueError(
                    "Embedding contém valor "
                    "não finito na posição "
                    f"{position}."
                )

            result.append(
                numeric_value
            )

        return result

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        do serviço de embeddings.
        """

        return {
            "integration": (
                "RAG_EMBEDDINGS"
            ),
            "embedding_model": (
                self._embedding_model
            ),
            "local_only": True,
            "external_api_required": False,
            "output": (
                "RAGEmbeddedChunk"
            ),
        }