"""
Knowledge / RAG local do Agentic SOC N1 Lab.

Fase 5.

Exports centrais:

- configuração;
- contratos;
- serviço integrado RAG → AG-08.

As implementações específicas permanecem
organizadas nos subpacotes:

- rag.ingestion;
- rag.embeddings;
- rag.index;
- rag.retrieval.
"""

from rag.config import (
    ALLOWED_KNOWLEDGE_TYPES,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_INDEX_FILE,
    DEFAULT_KNOWLEDGE_DIRECTORY,
    DEFAULT_MIN_SIMILARITY,
    DEFAULT_TOP_K,
    RAGConfig,
)
from rag.contracts import (
    RAGChunk,
    RAGDocument,
    RAGEmbeddedChunk,
    RAGSearchHit,
    RAGSearchResult,
)
from rag.service import (
    RAGKnowledgeService,
)


__all__ = (
    "ALLOWED_KNOWLEDGE_TYPES",
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_INDEX_FILE",
    "DEFAULT_KNOWLEDGE_DIRECTORY",
    "DEFAULT_MIN_SIMILARITY",
    "DEFAULT_TOP_K",
    "RAGChunk",
    "RAGConfig",
    "RAGDocument",
    "RAGEmbeddedChunk",
    "RAGKnowledgeService",
    "RAGSearchHit",
    "RAGSearchResult",
)