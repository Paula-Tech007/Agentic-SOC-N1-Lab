"""
Chunking controlado da camada RAG
do Agentic SOC N1 Lab.

Fase 5.2 — Chunking e normalização.

Responsabilidades:

- receber RAGDocument validado;
- dividir conteúdo em chunks;
- aplicar overlap configurável;
- preservar origem e metadados;
- reconhecer seções Markdown;
- gerar IDs determinísticos;
- produzir RAGChunk.

Princípios:

- nenhum conteúdo é inventado;
- nenhum dado externo é consultado;
- chunks possuem tamanho controlado;
- overlap nunca pode impedir progresso;
- origem do documento é preservada;
- processamento totalmente local.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from rag.config import RAGConfig
from rag.contracts import (
    RAGChunk,
    RAGDocument,
)


class RAGTextChunker:
    """
    Divide documentos autorizados
    em chunks utilizados pelo RAG.
    """

    def __init__(
        self,
        config: RAGConfig | None = None,
    ) -> None:
        """
        Inicializa o chunker.
        """

        self._config = (
            config
            if config is not None
            else RAGConfig()
        )

    @property
    def config(
        self,
    ) -> RAGConfig:
        """
        Retorna configuração RAG.
        """

        return self._config

    def chunk_document(
        self,
        document: RAGDocument,
    ) -> list[RAGChunk]:
        """
        Divide um documento em chunks.

        A posição dos chunks é global
        dentro do documento.
        """

        if not isinstance(
            document,
            RAGDocument,
        ):
            raise TypeError(
                "document precisa ser "
                "uma instância de RAGDocument."
            )

        sections = (
            self._split_sections(
                document
            )
        )

        chunks: list[RAGChunk] = []

        position = 0

        for (
            section_name,
            section_content,
        ) in sections:

            pieces = self._chunk_text(
                section_content
            )

            for piece in pieces:
                chunk_id = (
                    self._create_chunk_id(
                        document_id=(
                            document.document_id
                        ),
                        position=position,
                        section=section_name,
                        content=piece,
                    )
                )

                metadata = dict(
                    document.metadata
                )

                metadata.update(
                    {
                        "chunk_index": (
                            position
                        ),
                        "chunk_length": (
                            len(piece)
                        ),
                        "chunk_size_limit": (
                            self._config
                            .chunk_size
                        ),
                        "chunk_overlap": (
                            self._config
                            .chunk_overlap
                        ),
                        "local_source": True,
                    }
                )

                chunk = RAGChunk(
                    chunk_id=chunk_id,
                    document_id=(
                        document.document_id
                    ),
                    document_name=(
                        document.document_name
                    ),
                    document_type=(
                        document.document_type
                    ),
                    section=section_name,
                    content=piece,
                    source_path=(
                        document.source_path
                    ),
                    position=position,
                    metadata=metadata,
                )

                chunks.append(
                    chunk
                )

                position += 1

        if not chunks:
            raise ValueError(
                "O documento não produziu "
                "nenhum chunk válido."
            )

        return chunks

    def chunk_documents(
        self,
        documents: (
            list[RAGDocument]
            | tuple[RAGDocument, ...]
        ),
    ) -> list[RAGChunk]:
        """
        Executa chunking para vários documentos.
        """

        if not isinstance(
            documents,
            (list, tuple),
        ):
            raise TypeError(
                "documents precisa ser "
                "lista ou tupla."
            )

        chunks: list[RAGChunk] = []

        for document in documents:
            if not isinstance(
                document,
                RAGDocument,
            ):
                raise TypeError(
                    "documents contém item "
                    "que não é RAGDocument."
                )

            chunks.extend(
                self.chunk_document(
                    document
                )
            )

        return chunks

    def _split_sections(
        self,
        document: RAGDocument,
    ) -> list[
        tuple[str | None, str]
    ]:
        """
        Identifica seções Markdown.

        Para TXT, JSON, YAML e YML,
        todo o documento é tratado
        como uma única seção.
        """

        content = (
            document.content.strip()
        )

        extension = (
            Path(
                document.source_path
            )
            .suffix
            .lower()
        )

        if extension != ".md":
            return [
                (
                    None,
                    content,
                )
            ]

        sections: list[
            tuple[str | None, str]
        ] = []

        current_section: (
            str | None
        ) = None

        buffer: list[str] = []

        def flush_buffer() -> None:
            """
            Salva conteúdo acumulado
            da seção atual.
            """

            text = "\n".join(
                buffer
            ).strip()

            if text:
                sections.append(
                    (
                        current_section,
                        text,
                    )
                )

            buffer.clear()

        for raw_line in (
            content.splitlines()
        ):
            stripped = (
                raw_line.strip()
            )

            heading_level = (
                len(stripped)
                - len(
                    stripped.lstrip(
                        "#"
                    )
                )
            )

            is_heading = (
                stripped.startswith("#")
                and 1 <= heading_level <= 6
                and bool(
                    stripped[
                        heading_level:
                    ].strip()
                )
            )

            if is_heading:
                flush_buffer()

                current_section = (
                    stripped[
                        heading_level:
                    ].strip()
                )

                continue

            buffer.append(
                raw_line
            )

        flush_buffer()

        if not sections:
            return [
                (
                    None,
                    content,
                )
            ]

        return sections

    def _chunk_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Divide um texto utilizando
        chunk_size e chunk_overlap.

        Sempre tenta terminar em uma
        quebra natural antes do limite.
        """

        normalized = text.strip()

        if not normalized:
            return []

        chunk_size = (
            self._config.chunk_size
        )

        overlap = (
            self._config.chunk_overlap
        )

        if len(normalized) <= chunk_size:
            return [
                normalized
            ]

        chunks: list[str] = []

        start = 0
        text_length = len(
            normalized
        )

        while start < text_length:
            hard_end = min(
                start + chunk_size,
                text_length,
            )

            end = hard_end

            if hard_end < text_length:
                candidate = (
                    normalized[
                        start:hard_end
                    ]
                )

                minimum_break = int(
                    len(candidate)
                    * 0.60
                )

                for delimiter in (
                    "\n\n",
                    "\n",
                    " ",
                ):
                    break_position = (
                        candidate.rfind(
                            delimiter,
                            minimum_break,
                        )
                    )

                    if break_position > 0:
                        end = (
                            start
                            + break_position
                        )

                        break

            piece = (
                normalized[
                    start:end
                ]
                .strip()
            )

            if piece:
                chunks.append(
                    piece
                )

            if end >= text_length:
                break

            next_start = max(
                0,
                end - overlap,
            )

            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    @staticmethod
    def _create_chunk_id(
        *,
        document_id: str,
        position: int,
        section: str | None,
        content: str,
    ) -> str:
        """
        Gera ID determinístico para o chunk.
        """

        source = (
            f"{document_id}|"
            f"{position}|"
            f"{section or ''}|"
            f"{content}"
        )

        digest = sha256(
            source.encode(
                "utf-8"
            )
        ).hexdigest()

        return (
            "CHUNK-"
            + digest[:16].upper()
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro do chunker.
        """

        return {
            "integration": (
                "RAG_CHUNKING"
            ),
            "chunk_size": (
                self._config
                .chunk_size
            ),
            "chunk_overlap": (
                self._config
                .chunk_overlap
            ),
            "markdown_sections": True,
            "deterministic_ids": True,
            "local_only": True,
        }