"""
Testes da composição operacional
do Agentic SOC N1 Lab.

Valida:

- ToolRuntime completo;
- RAGRetriever injetável;
- FullEnrichmentPayloadProvider;
- Phase7E2ERunner;
- ligação provider -> runner;
- índice RAG não vazio;
- nenhum acesso à rede real;
- fail-closed para RAG vazio.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.operational_bootstrap import (
    OperationalComposition,
    build_operational_composition,
)

from app.full_enrichment_payload_provider import (
    FullEnrichmentPayloadProvider,
)

from core.orchestrator.phase7_runner import (
    Phase7E2ERunner,
)

from rag import (
    RAGChunk,
    RAGConfig,
    RAGEmbeddedChunk,
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


TEST_ENV = {
    "MISP_URL": (
        "https://misp.example.invalid"
    ),
    "MISP_API_KEY": (
        "TEST-MISP-KEY"
    ),
    "MISP_VERIFY_SSL": "true",
    "MISP_TIMEOUT_SECONDS": "15",

    "IAM_URL": (
        "https://iam.example.invalid"
    ),
    "IAM_API_TOKEN": (
        "TEST-IAM-TOKEN"
    ),
    "IAM_PROVIDER": "LAB-IAM",
    "IAM_VERIFY_SSL": "true",
    "IAM_TIMEOUT_SECONDS": "15",

    "ASSET_URL": (
        "https://asset.example.invalid"
    ),
    "ASSET_API_TOKEN": (
        "TEST-ASSET-TOKEN"
    ),
    "ASSET_PROVIDER": "LAB-CMDB",
    "ASSET_VERIFY_SSL": "true",
    "ASSET_TIMEOUT_SECONDS": "15",
}


def _transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Transporte controlado.

    Nenhuma rede real é utilizada.
    """

    return httpx.Response(
        200,
        json={},
        request=request,
    )


def _email_config(
) -> EmailConfig:
    return EmailConfig(
        base_url=(
            "https://email.example.invalid"
        ),
        api_token=(
            "TEST-EMAIL-TOKEN"
        ),
        provider="LAB-EMAIL",
        verify_ssl=True,
        timeout_seconds=15,
    )


def _create_retriever(
    tmp_path: Path,
) -> RAGRetriever:
    """
    Cria índice RAG temporário
    completamente isolado.
    """

    config = RAGConfig(
        index_file=(
            "rag/index/"
            "knowledge_index.json"
        ),
        chunk_size=220,
        chunk_overlap=40,
        top_k=3,
        min_similarity=0.20,
    )

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    chunk = RAGChunk(
        chunk_id=(
            "CHUNK-OPERATIONAL-0001"
        ),
        document_id=(
            "DOC-OPERATIONAL-0001"
        ),
        document_name=(
            "operational_test.md"
        ),
        document_type="runbook",
        section="Triagem",
        content=(
            "Conhecimento defensivo "
            "controlado para teste."
        ),
        source_path=(
            "knowledge/runbooks/"
            "operational_test.md"
        ),
        position=0,
        metadata={
            "local_source": True,
        },
    )

    index.add(
        RAGEmbeddedChunk(
            chunk=chunk,
            embedding=[
                1.0,
                0.0,
                0.0,
            ],
            embedding_model=(
                "embeddinggemma"
            ),
        )
    )

    return RAGRetriever(
        index,
        config,
        embedding_function=(
            lambda text: [
                1.0,
                0.0,
                0.0,
            ]
        ),
    )


def test_build_operational_composition(
    tmp_path: Path,
) -> None:
    """
    Composição precisa conectar
    todos os componentes oficiais.
    """

    retriever = (
        _create_retriever(
            tmp_path
        )
    )

    transport = (
        httpx.MockTransport(
            _transport
        )
    )

    composition = (
        build_operational_composition(
            env=TEST_ENV,
            misp_transport=transport,
            identity_transport=transport,
            asset_transport=transport,
            email_transport=transport,
            email_config=(
                _email_config()
            ),
            rag_retriever=retriever,
        )
    )

    assert isinstance(
        composition,
        OperationalComposition,
    )

    assert isinstance(
        composition.tool_runtime,
        ToolRuntime,
    )

    assert isinstance(
        composition.rag_retriever,
        RAGRetriever,
    )

    assert isinstance(
        composition.payload_provider,
        FullEnrichmentPayloadProvider,
    )

    assert isinstance(
        composition.runner,
        Phase7E2ERunner,
    )

    assert (
        composition.rag_items_loaded
        == 1
    )

    assert (
        composition.runner
        .payload_provider
        is composition
        .payload_provider
    )

    assert (
        composition.runner
        ._enrichment
        .payload_provider
        is composition
        .payload_provider
    )


def test_operational_summary_is_safe(
    tmp_path: Path,
) -> None:
    """
    Summary não deve expor
    tokens ou credenciais.
    """

    retriever = (
        _create_retriever(
            tmp_path
        )
    )

    transport = (
        httpx.MockTransport(
            _transport
        )
    )

    composition = (
        build_operational_composition(
            env=TEST_ENV,
            misp_transport=transport,
            identity_transport=transport,
            asset_transport=transport,
            email_transport=transport,
            email_config=(
                _email_config()
            ),
            rag_retriever=retriever,
        )
    )

    summary = (
        composition.safe_summary()
    )

    assert (
        summary[
            "rag_items_loaded"
        ]
        == 1
    )

    assert (
        summary[
            "rag_local_only"
        ]
        is True
    )

    assert (
        "TEST-EMAIL-TOKEN"
        not in str(summary)
    )

    assert (
        "TEST-MISP-KEY"
        not in str(summary)
    )


def test_operational_composition_rejects_empty_rag(
    tmp_path: Path,
) -> None:
    """
    RAG vazio deve falhar fechado.
    """

    config = RAGConfig(
        index_file=(
            "rag/index/"
            "knowledge_index.json"
        ),
    )

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    retriever = RAGRetriever(
        index,
        config,
        embedding_function=(
            lambda text: [
                1.0,
                0.0,
                0.0,
            ]
        ),
    )

    transport = (
        httpx.MockTransport(
            _transport
        )
    )

    with pytest.raises(
        RuntimeError,
        match="índice vazio",
    ):
        build_operational_composition(
            env=TEST_ENV,
            misp_transport=transport,
            identity_transport=transport,
            asset_transport=transport,
            email_transport=transport,
            email_config=(
                _email_config()
            ),
            rag_retriever=retriever,
        )