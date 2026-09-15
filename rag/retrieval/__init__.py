"""
Camada de retrieval do RAG.
"""

from rag.retrieval.adapter import (
    RAGKnowledgeAdapter,
)
from rag.retrieval.search import (
    EmbeddingFunction,
    RAGRetriever,
)


__all__ = (
    "EmbeddingFunction",
    "RAGKnowledgeAdapter",
    "RAGRetriever",
)