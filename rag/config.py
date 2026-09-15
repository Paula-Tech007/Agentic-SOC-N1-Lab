"""
Configuração central da camada RAG
do Agentic SOC N1 Lab.

Fase 5.0 — Fundação do Knowledge / RAG.

A camada RAG utiliza exclusivamente conhecimento
interno autorizado armazenado dentro do projeto.

Estrutura esperada:

knowledge/
├── mitre/
├── playbooks/
├── policies/
└── runbooks/

rag/
├── embeddings/
├── index/
├── ingestion/
└── retrieval/

Princípios:

- conhecimento local e autorizado;
- índice gerado localmente;
- nenhuma credencial;
- nenhum acesso externo arbitrário;
- caminhos restritos ao projeto;
- chunking controlado;
- retrieval com quantidade limitada;
- similaridade mínima explícita;
- fail-closed para configurações inválidas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_KNOWLEDGE_DIRECTORY = "knowledge"

DEFAULT_INDEX_FILE = (
    "rag/index/knowledge_index.json"
)

DEFAULT_CHUNK_SIZE = 1200

DEFAULT_CHUNK_OVERLAP = 200

DEFAULT_TOP_K = 5

DEFAULT_MIN_SIMILARITY = 0.25


MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 10000

MIN_TOP_K = 1
MAX_TOP_K = 50


ALLOWED_KNOWLEDGE_TYPES: tuple[str, ...] = (
    "mitre",
    "playbook",
    "policy",
    "runbook",
)


def _normalize_project_path(
    value: str,
    *,
    field_name: str,
) -> str:
    """
    Valida caminho relativo ao projeto.

    Caminhos absolutos e traversal com '..'
    são recusados.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{field_name} precisa ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{field_name} não pode ser vazio."
        )

    path = Path(cleaned)

    if path.is_absolute():
        raise ValueError(
            f"{field_name} precisa ser relativo "
            "ao diretório do projeto."
        )

    if ".." in path.parts:
        raise ValueError(
            f"{field_name} não pode utilizar '..'."
        )

    normalized = path.as_posix()

    if normalized in {
        ".",
        "",
    }:
        raise ValueError(
            f"{field_name} precisa apontar "
            "para um caminho válido."
        )

    return normalized


def _parse_integer(
    value: str | int | None,
    *,
    field_name: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    """
    Converte e valida um inteiro configurável.
    """

    if value is None:
        result = default

    elif isinstance(
        value,
        bool,
    ):
        raise ValueError(
            f"{field_name} precisa ser inteiro."
        )

    elif isinstance(
        value,
        int,
    ):
        result = value

    elif isinstance(
        value,
        str,
    ):
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} não pode ser vazio."
            )

        try:
            result = int(cleaned)

        except ValueError as exc:
            raise ValueError(
                f"{field_name} precisa ser inteiro."
            ) from exc

    else:
        raise ValueError(
            f"{field_name} precisa ser inteiro."
        )

    if (
        result < minimum
        or result > maximum
    ):
        raise ValueError(
            f"{field_name} precisa estar entre "
            f"{minimum} e {maximum}."
        )

    return result


def _parse_similarity(
    value: str | float | int | None,
) -> float:
    """
    Valida score mínimo de similaridade.

    O valor deve permanecer entre 0.0 e 1.0.
    """

    if value is None:
        result = DEFAULT_MIN_SIMILARITY

    elif isinstance(
        value,
        bool,
    ):
        raise ValueError(
            "RAG_MIN_SIMILARITY precisa ser numérico."
        )

    elif isinstance(
        value,
        (int, float),
    ):
        result = float(value)

    elif isinstance(
        value,
        str,
    ):
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "RAG_MIN_SIMILARITY não pode ser vazio."
            )

        try:
            result = float(cleaned)

        except ValueError as exc:
            raise ValueError(
                "RAG_MIN_SIMILARITY precisa ser numérico."
            ) from exc

    else:
        raise ValueError(
            "RAG_MIN_SIMILARITY precisa ser numérico."
        )

    if (
        result < 0.0
        or result > 1.0
    ):
        raise ValueError(
            "RAG_MIN_SIMILARITY precisa estar "
            "entre 0.0 e 1.0."
        )

    return result


@dataclass(
    frozen=True,
    slots=True,
)
class RAGConfig:
    """
    Configuração imutável da camada RAG.
    """

    knowledge_directory: str = (
        DEFAULT_KNOWLEDGE_DIRECTORY
    )

    index_file: str = (
        DEFAULT_INDEX_FILE
    )

    chunk_size: int = (
        DEFAULT_CHUNK_SIZE
    )

    chunk_overlap: int = (
        DEFAULT_CHUNK_OVERLAP
    )

    top_k: int = (
        DEFAULT_TOP_K
    )

    min_similarity: float = (
        DEFAULT_MIN_SIMILARITY
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida também construções diretas.
        """

        object.__setattr__(
            self,
            "knowledge_directory",
            _normalize_project_path(
                self.knowledge_directory,
                field_name=(
                    "knowledge_directory"
                ),
            ),
        )

        object.__setattr__(
            self,
            "index_file",
            _normalize_project_path(
                self.index_file,
                field_name="index_file",
            ),
        )

        chunk_size = _parse_integer(
            self.chunk_size,
            field_name="chunk_size",
            default=DEFAULT_CHUNK_SIZE,
            minimum=MIN_CHUNK_SIZE,
            maximum=MAX_CHUNK_SIZE,
        )

        chunk_overlap = _parse_integer(
            self.chunk_overlap,
            field_name="chunk_overlap",
            default=DEFAULT_CHUNK_OVERLAP,
            minimum=0,
            maximum=MAX_CHUNK_SIZE,
        )

        if (
            chunk_overlap
            >= chunk_size
        ):
            raise ValueError(
                "chunk_overlap precisa ser menor "
                "que chunk_size."
            )

        top_k = _parse_integer(
            self.top_k,
            field_name="top_k",
            default=DEFAULT_TOP_K,
            minimum=MIN_TOP_K,
            maximum=MAX_TOP_K,
        )

        min_similarity = (
            _parse_similarity(
                self.min_similarity
            )
        )

        object.__setattr__(
            self,
            "chunk_size",
            chunk_size,
        )

        object.__setattr__(
            self,
            "chunk_overlap",
            chunk_overlap,
        )

        object.__setattr__(
            self,
            "top_k",
            top_k,
        )

        object.__setattr__(
            self,
            "min_similarity",
            min_similarity,
        )

    @classmethod
    def from_env(
        cls,
    ) -> "RAGConfig":
        """
        Carrega configuração RAG
        das variáveis de ambiente.
        """

        knowledge_directory = os.getenv(
            "RAG_KNOWLEDGE_DIRECTORY",
            DEFAULT_KNOWLEDGE_DIRECTORY,
        )

        index_file = os.getenv(
            "RAG_INDEX_FILE",
            DEFAULT_INDEX_FILE,
        )

        chunk_size = _parse_integer(
            os.getenv(
                "RAG_CHUNK_SIZE"
            ),
            field_name="RAG_CHUNK_SIZE",
            default=DEFAULT_CHUNK_SIZE,
            minimum=MIN_CHUNK_SIZE,
            maximum=MAX_CHUNK_SIZE,
        )

        chunk_overlap = _parse_integer(
            os.getenv(
                "RAG_CHUNK_OVERLAP"
            ),
            field_name=(
                "RAG_CHUNK_OVERLAP"
            ),
            default=DEFAULT_CHUNK_OVERLAP,
            minimum=0,
            maximum=MAX_CHUNK_SIZE,
        )

        top_k = _parse_integer(
            os.getenv(
                "RAG_TOP_K"
            ),
            field_name="RAG_TOP_K",
            default=DEFAULT_TOP_K,
            minimum=MIN_TOP_K,
            maximum=MAX_TOP_K,
        )

        min_similarity = (
            _parse_similarity(
                os.getenv(
                    "RAG_MIN_SIMILARITY"
                )
            )
        )

        return cls(
            knowledge_directory=(
                knowledge_directory
            ),
            index_file=index_file,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            min_similarity=min_similarity,
        )

    @property
    def allowed_knowledge_types(
        self,
    ) -> tuple[str, ...]:
        """
        Tipos oficiais de conhecimento.
        """

        return ALLOWED_KNOWLEDGE_TYPES

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro da configuração.
        """

        return {
            "knowledge_directory": (
                self.knowledge_directory
            ),
            "index_file": (
                self.index_file
            ),
            "chunk_size": (
                self.chunk_size
            ),
            "chunk_overlap": (
                self.chunk_overlap
            ),
            "top_k": self.top_k,
            "min_similarity": (
                self.min_similarity
            ),
            "allowed_knowledge_types": (
                self.allowed_knowledge_types
            ),
            "local_only": True,
        }