"""
Índice vetorial local da camada RAG
do Agentic SOC N1 Lab.

Fase 5.4 — Índice Vetorial Local.

Responsabilidades:

- armazenar RAGEmbeddedChunk;
- impedir dimensões incompatíveis;
- impedir mistura de modelos de embedding;
- permitir inclusão e atualização controlada;
- persistir o índice em JSON;
- carregar índice existente com validação;
- manter todo o conteúdo dentro do laboratório.

Estrutura persistida:

{
    "version": 1,
    "embedding_model": "embeddinggemma",
    "dimension": 768,
    "items": [...]
}

Princípios:

- armazenamento local;
- formato JSON;
- nenhum pickle;
- nenhum código executável no índice;
- nenhum serviço externo;
- escrita atômica;
- validação antes de carregar;
- fail-closed em índice inválido.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rag.config import RAGConfig
from rag.contracts import (
    RAGEmbeddedChunk,
)


INDEX_FORMAT_VERSION = 1


class RAGVectorIndex:
    """
    Índice vetorial local em memória
    com persistência JSON.
    """

    def __init__(
        self,
        config: RAGConfig | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        """
        Inicializa o índice vazio.

        O índice não é carregado
        automaticamente do disco.
        """

        self._config = (
            config
            if config is not None
            else RAGConfig()
        )

        if project_root is None:
            self._project_root = (
                Path(__file__)
                .resolve()
                .parents[2]
            )

        else:
            self._project_root = (
                Path(project_root)
                .expanduser()
                .resolve()
            )

        self._index_path = (
            self._project_root
            / self._config.index_file
        ).resolve()

        self._allowed_index_root = (
            self._project_root
            / "rag"
            / "index"
        ).resolve()

        self._validate_index_path()

        self._items: dict[
            str,
            RAGEmbeddedChunk,
        ] = {}

        self._dimension: int | None = None

        self._embedding_model: (
            str | None
        ) = None

    @property
    def config(
        self,
    ) -> RAGConfig:
        """
        Retorna configuração RAG.
        """

        return self._config

    @property
    def index_path(
        self,
    ) -> Path:
        """
        Caminho absoluto do arquivo
        de índice local.
        """

        return self._index_path

    @property
    def count(
        self,
    ) -> int:
        """
        Quantidade de chunks indexados.
        """

        return len(
            self._items
        )

    @property
    def dimension(
        self,
    ) -> int | None:
        """
        Dimensão vetorial do índice.
        """

        return self._dimension

    @property
    def embedding_model(
        self,
    ) -> str | None:
        """
        Modelo de embeddings utilizado.
        """

        return self._embedding_model

    def add(
        self,
        item: RAGEmbeddedChunk,
    ) -> None:
        """
        Adiciona um chunk ao índice.

        chunk_id duplicado não é aceito.
        """

        self._validate_item(
            item
        )

        chunk_id = (
            item.chunk.chunk_id
        )

        if (
            chunk_id
            in self._items
        ):
            raise ValueError(
                "chunk_id já existe "
                "no índice: "
                f"{chunk_id}"
            )

        self._prepare_index_metadata(
            item
        )

        self._items[
            chunk_id
        ] = item

    def upsert(
        self,
        item: RAGEmbeddedChunk,
    ) -> None:
        """
        Insere ou substitui um chunk
        pelo mesmo chunk_id.
        """

        self._validate_item(
            item
        )

        self._prepare_index_metadata(
            item
        )

        self._items[
            item.chunk.chunk_id
        ] = item

    def add_many(
        self,
        items: (
            list[RAGEmbeddedChunk]
            | tuple[
                RAGEmbeddedChunk,
                ...
            ]
        ),
    ) -> None:
        """
        Adiciona vários chunks.

        Antes de alterar o índice,
        todos os itens são validados.
        """

        if not isinstance(
            items,
            (list, tuple),
        ):
            raise TypeError(
                "items precisa ser "
                "lista ou tupla."
            )

        seen_ids: set[str] = set()

        prospective_dimension = (
            self._dimension
        )

        prospective_model = (
            self._embedding_model
        )

        for item in items:
            self._validate_item(
                item
            )

            chunk_id = (
                item.chunk.chunk_id
            )

            if (
                chunk_id
                in seen_ids
            ):
                raise ValueError(
                    "chunk_id duplicado "
                    "na operação: "
                    f"{chunk_id}"
                )

            if (
                chunk_id
                in self._items
            ):
                raise ValueError(
                    "chunk_id já existe "
                    "no índice: "
                    f"{chunk_id}"
                )

            seen_ids.add(
                chunk_id
            )

            dimension = len(
                item.embedding
            )

            if (
                prospective_dimension
                is None
            ):
                prospective_dimension = (
                    dimension
                )

            elif (
                dimension
                != prospective_dimension
            ):
                raise ValueError(
                    "Dimensão do embedding "
                    "é incompatível com "
                    "o índice."
                )

            if prospective_model is None:
                prospective_model = (
                    item.embedding_model
                )

            elif (
                item.embedding_model
                != prospective_model
            ):
                raise ValueError(
                    "Modelo de embedding "
                    "é incompatível com "
                    "o índice."
                )

        for item in items:
            self._items[
                item.chunk.chunk_id
            ] = item

        if items:
            self._dimension = (
                prospective_dimension
            )

            self._embedding_model = (
                prospective_model
            )

    def get(
        self,
        chunk_id: str,
    ) -> RAGEmbeddedChunk | None:
        """
        Recupera item pelo chunk_id.
        """

        if not isinstance(
            chunk_id,
            str,
        ):
            raise TypeError(
                "chunk_id precisa ser "
                "uma string."
            )

        normalized = (
            chunk_id.strip()
        )

        if not normalized:
            raise ValueError(
                "chunk_id não pode "
                "ser vazio."
            )

        return self._items.get(
            normalized
        )

    def all_items(
        self,
    ) -> tuple[
        RAGEmbeddedChunk,
        ...
    ]:
        """
        Retorna snapshot imutável
        dos itens ordenados por chunk_id.
        """

        return tuple(
            self._items[
                chunk_id
            ]
            for chunk_id in sorted(
                self._items
            )
        )

    def clear(
        self,
    ) -> None:
        """
        Limpa somente o índice em memória.

        Não remove arquivo do disco.
        """

        self._items.clear()

        self._dimension = None
        self._embedding_model = None

    def save(
        self,
    ) -> Path:
        """
        Persiste índice em JSON
        utilizando escrita atômica.
        """

        self._index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": (
                INDEX_FORMAT_VERSION
            ),
            "embedding_model": (
                self._embedding_model
            ),
            "dimension": (
                self._dimension
            ),
            "items": [
                item.model_dump(
                    mode="json"
                )
                for item in (
                    self.all_items()
                )
            ],
        }

        temporary_path = (
            self._index_path
            .with_suffix(
                self._index_path.suffix
                + ".tmp"
            )
        )

        try:
            temporary_path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            os.replace(
                temporary_path,
                self._index_path,
            )

        finally:
            if (
                temporary_path.exists()
            ):
                temporary_path.unlink()

        return self._index_path

    def load(
        self,
    ) -> int:
        """
        Carrega e valida índice
        previamente persistido.

        Retorna a quantidade
        de chunks carregados.
        """

        if not self._index_path.exists():
            raise FileNotFoundError(
                "Arquivo de índice RAG "
                "não encontrado."
            )

        if not self._index_path.is_file():
            raise ValueError(
                "Caminho do índice RAG "
                "não é um arquivo."
            )

        try:
            raw_payload = json.loads(
                self._index_path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Índice RAG não contém "
                "JSON válido."
            ) from exc

        if not isinstance(
            raw_payload,
            dict,
        ):
            raise ValueError(
                "Índice RAG precisa "
                "ser um objeto JSON."
            )

        version = raw_payload.get(
            "version"
        )

        if (
            version
            != INDEX_FORMAT_VERSION
        ):
            raise ValueError(
                "Versão do índice RAG "
                "não suportada."
            )

        raw_items = raw_payload.get(
            "items"
        )

        if not isinstance(
            raw_items,
            list,
        ):
            raise ValueError(
                "Índice RAG possui "
                "'items' inválido."
            )

        loaded_items: dict[
            str,
            RAGEmbeddedChunk,
        ] = {}

        loaded_dimension: (
            int | None
        ) = None

        loaded_model: (
            str | None
        ) = None

        for position, raw_item in enumerate(
            raw_items,
            start=1,
        ):
            try:
                item = (
                    RAGEmbeddedChunk
                    .model_validate(
                        raw_item
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "Item inválido no "
                    "índice RAG na posição "
                    f"{position}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ) from exc

            chunk_id = (
                item.chunk.chunk_id
            )

            if (
                chunk_id
                in loaded_items
            ):
                raise ValueError(
                    "Índice RAG possui "
                    "chunk_id duplicado: "
                    f"{chunk_id}"
                )

            dimension = len(
                item.embedding
            )

            if loaded_dimension is None:
                loaded_dimension = (
                    dimension
                )

            elif (
                dimension
                != loaded_dimension
            ):
                raise ValueError(
                    "Índice RAG possui "
                    "dimensões incompatíveis."
                )

            if loaded_model is None:
                loaded_model = (
                    item.embedding_model
                )

            elif (
                item.embedding_model
                != loaded_model
            ):
                raise ValueError(
                    "Índice RAG possui "
                    "modelos de embedding "
                    "incompatíveis."
                )

            loaded_items[
                chunk_id
            ] = item

        metadata_dimension = (
            raw_payload.get(
                "dimension"
            )
        )

        metadata_model = (
            raw_payload.get(
                "embedding_model"
            )
        )

        if raw_items:
            if (
                metadata_dimension
                != loaded_dimension
            ):
                raise ValueError(
                    "Metadado de dimensão "
                    "não corresponde aos "
                    "itens do índice."
                )

            if (
                metadata_model
                != loaded_model
            ):
                raise ValueError(
                    "Metadado de modelo "
                    "não corresponde aos "
                    "itens do índice."
                )

        else:
            if (
                metadata_dimension
                is not None
                or metadata_model
                is not None
            ):
                raise ValueError(
                    "Índice vazio não pode "
                    "possuir metadados de "
                    "modelo ou dimensão."
                )

        self._items = loaded_items

        self._dimension = (
            loaded_dimension
        )

        self._embedding_model = (
            loaded_model
        )

        return len(
            loaded_items
        )

    def _validate_item(
        self,
        item: RAGEmbeddedChunk,
    ) -> None:
        """
        Valida tipo básico do item.
        """

        if not isinstance(
            item,
            RAGEmbeddedChunk,
        ):
            raise TypeError(
                "item precisa ser uma "
                "instância de "
                "RAGEmbeddedChunk."
            )

    def _prepare_index_metadata(
        self,
        item: RAGEmbeddedChunk,
    ) -> None:
        """
        Valida dimensão/modelo e
        inicializa metadados do índice.
        """

        dimension = len(
            item.embedding
        )

        if self._dimension is None:
            self._dimension = dimension

        elif (
            dimension
            != self._dimension
        ):
            raise ValueError(
                "Dimensão do embedding "
                "é incompatível com "
                "o índice."
            )

        if (
            self._embedding_model
            is None
        ):
            self._embedding_model = (
                item.embedding_model
            )

        elif (
            item.embedding_model
            != self._embedding_model
        ):
            raise ValueError(
                "Modelo de embedding "
                "é incompatível com "
                "o índice."
            )

    def _validate_index_path(
        self,
    ) -> None:
        """
        Impede persistência do índice
        fora de rag/index/.
        """

        if not self._is_relative_to(
            self._index_path,
            self._allowed_index_root,
        ):
            raise PermissionError(
                "index_file precisa "
                "permanecer dentro de "
                "rag/index/."
            )

    @staticmethod
    def _is_relative_to(
        path: Path,
        parent: Path,
    ) -> bool:
        """
        Verifica containment seguro
        entre caminhos.
        """

        try:
            path.relative_to(
                parent
            )

        except ValueError:
            return False

        return True

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Retorna resumo seguro do índice.
        """

        return {
            "integration": (
                "RAG_VECTOR_INDEX"
            ),
            "index_file": (
                self._config.index_file
            ),
            "format": "JSON",
            "version": (
                INDEX_FORMAT_VERSION
            ),
            "count": self.count,
            "dimension": (
                self._dimension
            ),
            "embedding_model": (
                self._embedding_model
            ),
            "local_only": True,
            "executable_format": False,
        }