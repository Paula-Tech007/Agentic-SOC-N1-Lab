"""
Camada de ingestão do RAG.
"""

from rag.ingestion.chunker import (
    RAGTextChunker,
)
from rag.ingestion.loader import (
    KNOWLEDGE_DIRECTORY_TYPE_MAP,
    MAX_DOCUMENT_BYTES,
    SUPPORTED_DOCUMENT_EXTENSIONS,
    RAGDocumentLoader,
)


__all__ = (
    "RAGDocumentLoader",
    "RAGTextChunker",
    "KNOWLEDGE_DIRECTORY_TYPE_MAP",
    "MAX_DOCUMENT_BYTES",
    "SUPPORTED_DOCUMENT_EXTENSIONS",
)