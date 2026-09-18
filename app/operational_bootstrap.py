"""
Composition root operacional
do Agentic SOC N1 Lab.

Esta camada conecta oficialmente:

ToolRuntime
    ↓
RAG local
    ↓
FullEnrichmentPayloadProvider
    ↓
Phase7E2ERunner

Responsabilidades:

- montar as Tools oficiais
  de enriquecimento;
- carregar o índice RAG local;
- criar o RAGRetriever;
- criar o provider completo;
- criar o runner oficial;
- preservar fail-closed;
- não executar alertas durante
  a construção da composição;
- não expor segredos.

Nenhuma dependência core -> app
é introduzida.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.bootstrap import (
    build_phase7_runner,
)

from app.full_enrichment_payload_provider import (
    FullEnrichmentPayloadProvider,
)

from app.full_enrichment_tool_bootstrap import (
    build_full_enrichment_tool_runtime,
)

from core.orchestrator.phase7_runner import (
    Phase7E2ERunner,
)

from rag import (
    RAGConfig,
)

from rag.index import (
    RAGVectorIndex,
)

from rag.retrieval import (
    RAGRetriever,
)

from tools import (
    ToolRuntime,
)

from tools.email import (
    EmailConfig,
)


@dataclass(
    frozen=True,
    slots=True,
)
class OperationalComposition:
    """
    Componentes operacionais oficiais
    construídos pela aplicação.
    """

    tool_runtime: ToolRuntime

    rag_retriever: RAGRetriever

    payload_provider: (
        FullEnrichmentPayloadProvider
    )

    runner: Phase7E2ERunner

    rag_items_loaded: int

    def safe_summary(
        self,
    ) -> dict[str, Any]:
        """
        Resumo operacional sem segredos.
        """

        return {
            "tool_runtime": (
                type(
                    self.tool_runtime
                ).__name__
            ),
            "rag_items_loaded": (
                self.rag_items_loaded
            ),
            "payload_provider": (
                type(
                    self.payload_provider
                ).__name__
            ),
            "runner": (
                type(
                    self.runner
                ).__name__
            ),
            "rag_local_only": True,
        }


def build_operational_composition(
    *,
    max_cycles: int = 32,
    project_root: (
        str
        | Path
        | None
    ) = None,
    env: (
        Mapping[str, str]
        | None
    ) = None,
    misp_transport: Any | None = None,
    identity_transport: Any | None = None,
    asset_transport: Any | None = None,
    email_transport: Any | None = None,
    email_config: (
        EmailConfig
        | None
    ) = None,
    rag_config: (
        RAGConfig
        | None
    ) = None,
    rag_retriever: (
        RAGRetriever
        | None
    ) = None,
) -> OperationalComposition:
    """
    Monta a composição operacional
    completa do projeto.

    Em produção:

    - configurações vêm do ambiente;
    - índice RAG é carregado do disco;
    - ToolRuntime usa integrações oficiais.

    Em testes:

    - transports podem ser simulados;
    - RAGRetriever pode ser injetado;
    - nenhuma rede real é necessária.
    """

    if (
        isinstance(
            max_cycles,
            bool,
        )
        or not isinstance(
            max_cycles,
            int,
        )
        or max_cycles < 1
        or max_cycles > 100
    ):
        raise ValueError(
            "max_cycles precisa estar "
            "entre 1 e 100."
        )

    tool_runtime = (
        build_full_enrichment_tool_runtime(
            env=env,
            misp_transport=(
                misp_transport
            ),
            identity_transport=(
                identity_transport
            ),
            asset_transport=(
                asset_transport
            ),
            email_transport=(
                email_transport
            ),
            email_config=(
                email_config
            ),
        )
    )

    resolved_retriever: RAGRetriever

    rag_items_loaded: int

    if rag_retriever is not None:
        if not isinstance(
            rag_retriever,
            RAGRetriever,
        ):
            raise TypeError(
                "rag_retriever precisa ser "
                "RAGRetriever ou None."
            )

        resolved_retriever = (
            rag_retriever
        )

        rag_items_loaded = (
            rag_retriever
            .index
            .count
        )

        if rag_items_loaded < 1:
            raise RuntimeError(
                "RAGRetriever fornecido "
                "possui índice vazio."
            )

    else:
        resolved_rag_config = (
            rag_config
            if rag_config is not None
            else RAGConfig.from_env()
        )

        if not isinstance(
            resolved_rag_config,
            RAGConfig,
        ):
            raise TypeError(
                "rag_config precisa ser "
                "RAGConfig ou None."
            )

        resolved_project_root = (
            Path(project_root)
            .expanduser()
            .resolve()
            if project_root is not None
            else Path.cwd().resolve()
        )

        rag_index = RAGVectorIndex(
            resolved_rag_config,
            project_root=(
                resolved_project_root
            ),
        )

        try:
            rag_items_loaded = (
                rag_index.load()
            )

        except FileNotFoundError as exc:
            raise RuntimeError(
                "Índice RAG operacional "
                "não encontrado."
            ) from exc

        if rag_items_loaded < 1:
            raise RuntimeError(
                "Índice RAG operacional "
                "está vazio."
            )

        resolved_retriever = (
            RAGRetriever(
                rag_index,
                resolved_rag_config,
            )
        )

    payload_provider = (
        FullEnrichmentPayloadProvider(
            tool_runtime,
            resolved_retriever,
        )
    )

    runner = build_phase7_runner(
        max_cycles=max_cycles,
        payload_provider=(
            payload_provider
        ),
    )

    return OperationalComposition(
        tool_runtime=tool_runtime,
        rag_retriever=(
            resolved_retriever
        ),
        payload_provider=(
            payload_provider
        ),
        runner=runner,
        rag_items_loaded=(
            rag_items_loaded
        ),
    )


__all__ = [
    "OperationalComposition",
    "build_operational_composition",
]