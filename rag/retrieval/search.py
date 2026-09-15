"""
Busca semântica da camada RAG
do Agentic SOC N1 Lab.

Fase 5.5 — Retrieval / Similaridade.

Responsabilidades:

- receber consulta textual;
- gerar embedding da consulta;
- comparar contra o índice vetorial local;
- calcular similaridade cosseno;
- aplicar score mínimo;
- limitar resultados por top_k;
- produzir RAGSearchResult.

Fluxo:

Query
    ↓
Embedding
    ↓
RAGVectorIndex
    ↓
Cosine Similarity
    ↓
Filtro por min_similarity
    ↓
Ordenação
    ↓
Top-K
    ↓
RAGSearchHit
    ↓
RAGSearchResult

Princípios:

- consulta local;
- nenhuma busca web;
- nenhum dado externo arbitrário;
- resultados somente do índice autorizado;
- dimensão vetorial precisa ser compatível;
- scores sempre entre 0.0 e 1.0;
- nenhuma evidência é inventada;
- fail-closed para vetores inválidos.
"""

from __future__ import annotations

from collections.abc import Callable
from math import isfinite, sqrt

from core.llm import create_embedding
from rag.config import RAGConfig
from rag.contracts import (
    RAGSearchHit,
    RAGSearchResult,
)
from rag.index.store import (
    RAGVectorIndex,
)


EmbeddingFunction = Callable[
    [str],
    list[float],
]


class RAGRetriever:
    """
    Executa busca semântica
    no índice vetorial local.
    """

    def __init__(
        self,
        index: RAGVectorIndex,
        config: RAGConfig | None = None,
        *,
        embedding_function: (
            EmbeddingFunction | None
        ) = None,
    ) -> None:
        """
        Inicializa o retrieval.

        Em produção utiliza
        core.llm.create_embedding.

        Em testes pode receber uma função
        controlada para geração de vetores.
        """

        if not isinstance(
            index,
            RAGVectorIndex,
        ):
            raise TypeError(
                "index precisa ser uma "
                "instância de RAGVectorIndex."
            )

        self._index = index

        self._config = (
            config
            if config is not None
            else index.config
        )

        if not isinstance(
            self._config,
            RAGConfig,
        ):
            raise TypeError(
                "config precisa ser uma "
                "instância de RAGConfig."
            )

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

    @property
    def index(
        self,
    ) -> RAGVectorIndex:
        """
        Retorna o índice utilizado.
        """

        return self._index

    @property
    def config(
        self,
    ) -> RAGConfig:
        """
        Retorna configuração RAG.
        """

        return self._config

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity: float | None = None,
    ) -> RAGSearchResult:
        """
        Executa busca semântica no índice.

        Somente chunks previamente indexados
        podem aparecer como resultado.
        """

        normalized_query = (
            self._normalize_query(
                query
            )
        )

        effective_top_k = (
            self._validate_top_k(
                top_k
                if top_k is not None
                else self._config.top_k
            )
        )

        effective_min_similarity = (
            self._validate_min_similarity(
                min_similarity
                if min_similarity is not None
                else self._config.min_similarity
            )
        )

        if self._index.count == 0:
            return RAGSearchResult(
                query=normalized_query,
                hits=[],
                top_k=effective_top_k,
                min_similarity=(
                    effective_min_similarity
                ),
            )

        raw_query_embedding = (
            self._embedding_function(
                normalized_query
            )
        )

        query_embedding = (
            self._validate_embedding(
                raw_query_embedding
            )
        )

        expected_dimension = (
            self._index.dimension
        )

        if expected_dimension is None:
            raise ValueError(
                "Índice possui itens, mas "
                "não possui dimensão definida."
            )

        if (
            len(query_embedding)
            != expected_dimension
        ):
            raise ValueError(
                "Dimensão do embedding da consulta "
                "é incompatível com o índice. "
                f"Consulta={len(query_embedding)}, "
                f"índice={expected_dimension}."
            )

        scored_hits: list[
            RAGSearchHit
        ] = []

        for item in (
            self._index.all_items()
        ):
            score = (
                self._cosine_similarity(
                    query_embedding,
                    item.embedding,
                )
            )

            if (
                score
                < effective_min_similarity
            ):
                continue

            scored_hits.append(
                RAGSearchHit(
                    chunk=item.chunk,
                    similarity_score=score,
                )
            )

        scored_hits.sort(
            key=lambda hit: (
                -hit.similarity_score,
                hit.chunk.chunk_id,
            )
        )

        selected_hits = (
            scored_hits[
                :effective_top_k
            ]
        )

        return RAGSearchResult(
            query=normalized_query,
            hits=selected_hits,
            top_k=effective_top_k,
            min_similarity=(
                effective_min_similarity
            ),
        )

    @staticmethod
    def _normalize_query(
        value: str,
    ) -> str:
        """
        Valida consulta textual.
        """

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "query precisa ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "query não pode ser vazia."
            )

        return cleaned

    @staticmethod
    def _validate_top_k(
        value: int,
    ) -> int:
        """
        Valida quantidade máxima
        de resultados.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "top_k precisa ser inteiro."
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                "top_k precisa ser inteiro."
            )

        if (
            value < 1
            or value > 50
        ):
            raise ValueError(
                "top_k precisa estar "
                "entre 1 e 50."
            )

        return value

    @staticmethod
    def _validate_min_similarity(
        value: float | int,
    ) -> float:
        """
        Valida score mínimo.
        """

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "min_similarity precisa "
                "ser numérico."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise ValueError(
                "min_similarity precisa "
                "ser numérico."
            )

        result = float(
            value
        )

        if not isfinite(
            result
        ):
            raise ValueError(
                "min_similarity precisa "
                "ser finito."
            )

        if (
            result < 0.0
            or result > 1.0
        ):
            raise ValueError(
                "min_similarity precisa "
                "estar entre 0.0 e 1.0."
            )

        return result

    @staticmethod
    def _validate_embedding(
        value: object,
    ) -> list[float]:
        """
        Valida embedding da consulta.
        """

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Embedding da consulta precisa "
                "ser lista ou tupla numérica."
            )

        if not value:
            raise ValueError(
                "Embedding da consulta "
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
                    "Embedding da consulta "
                    "contém booleano na posição "
                    f"{position}."
                )

            if not isinstance(
                item,
                (int, float),
            ):
                raise ValueError(
                    "Embedding da consulta "
                    "contém valor não numérico "
                    f"na posição {position}."
                )

            numeric_value = float(
                item
            )

            if not isfinite(
                numeric_value
            ):
                raise ValueError(
                    "Embedding da consulta "
                    "contém valor não finito "
                    f"na posição {position}."
                )

            result.append(
                numeric_value
            )

        return result

    @staticmethod
    def _cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:
        """
        Calcula similaridade cosseno.

        Scores negativos são convertidos
        para 0.0 porque o contrato oficial
        RAGSearchHit trabalha no intervalo
        de 0.0 até 1.0.
        """

        if len(left) != len(right):
            raise ValueError(
                "Vetores possuem dimensões "
                "incompatíveis."
            )

        if not left:
            raise ValueError(
                "Vetores não podem ser vazios."
            )

        dot_product = sum(
            left_value * right_value
            for (
                left_value,
                right_value,
            ) in zip(
                left,
                right,
                strict=True,
            )
        )

        left_norm = sqrt(
            sum(
                value * value
                for value in left
            )
        )

        right_norm = sqrt(
            sum(
                value * value
                for value in right
            )
        )

        if (
            left_norm == 0.0
            or right_norm == 0.0
        ):
            return 0.0

        cosine = (
            dot_product
            / (
                left_norm
                * right_norm
            )
        )

        if not isfinite(
            cosine
        ):
            raise ValueError(
                "Similaridade calculada "
                "não é finita."
            )

        cosine = max(
            -1.0,
            min(
                1.0,
                cosine,
            ),
        )

        return max(
            0.0,
            cosine,
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        do mecanismo de retrieval.
        """

        return {
            "integration": (
                "RAG_RETRIEVAL"
            ),
            "algorithm": (
                "COSINE_SIMILARITY"
            ),
            "top_k": (
                self._config.top_k
            ),
            "min_similarity": (
                self._config
                .min_similarity
            ),
            "index_count": (
                self._index.count
            ),
            "local_only": True,
            "web_search": False,
        }