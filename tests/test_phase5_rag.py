"""
Testes formais da Fase 5
do Agentic SOC N1 Lab.

Fase 5 — Knowledge / RAG Local.

Cobertura:

- configuração RAG;
- contratos internos;
- ingestão segura;
- chunking;
- embeddings;
- índice vetorial local;
- persistência JSON;
- retrieval por similaridade;
- adaptação para KnowledgeChunk;
- integração com AG-08;
- guardrails de segurança.

Princípios validados:

- conhecimento local;
- nenhuma busca web;
- nenhuma evidência inventada;
- nenhuma resposta inventada pelo RAG;
- nenhuma confiança inventada pelo RAG;
- caminhos controlados;
- índice JSON não executável;
- integração com AG-08 sem antecipar a Fase 7.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rag import (
    RAGChunk,
    RAGConfig,
    RAGDocument,
    RAGEmbeddedChunk,
    RAGKnowledgeService,
    RAGSearchHit,
    RAGSearchResult,
)
from rag.embeddings import (
    RAGEmbeddingService,
)
from rag.index import (
    RAGVectorIndex,
)
from rag.ingestion import (
    RAGDocumentLoader,
    RAGTextChunker,
)
from rag.retrieval import (
    RAGKnowledgeAdapter,
    RAGRetriever,
)


def create_chunk(
    *,
    chunk_id: str = "CHUNK-0001",
    document_id: str = "DOC-0001",
    document_name: str = "teste.md",
    document_type: str = "playbook",
    content: str = (
        "Investigar falhas repetidas "
        "de autenticação."
    ),
    position: int = 0,
) -> RAGChunk:
    """
    Cria chunk controlado para testes.
    """

    return RAGChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=document_name,
        document_type=document_type,
        section="Triagem",
        content=content,
        source_path=(
            "knowledge/playbooks/"
            + document_name
        ),
        position=position,
        metadata={
            "local_source": True,
        },
    )


def create_embedded_chunk(
    *,
    chunk_id: str = "CHUNK-0001",
    embedding: (
        list[float] | None
    ) = None,
    model: str = "embeddinggemma",
    content: str = (
        "Investigar falhas repetidas "
        "de autenticação."
    ),
) -> RAGEmbeddedChunk:
    """
    Cria chunk vetorizado controlado.
    """

    if embedding is None:
        embedding = [
            1.0,
            0.0,
            0.0,
        ]

    return RAGEmbeddedChunk(
        chunk=create_chunk(
            chunk_id=chunk_id,
            content=content,
        ),
        embedding=embedding,
        embedding_model=model,
    )


def create_config() -> RAGConfig:
    """
    Configuração padrão dos testes.
    """

    return RAGConfig(
        index_file=(
            "rag/index/"
            "knowledge_index.json"
        ),
        chunk_size=220,
        chunk_overlap=40,
        top_k=3,
        min_similarity=0.20,
    )


def test_rag_config_defaults() -> None:
    """
    Configuração padrão deve ser segura.
    """

    config = RAGConfig()

    assert (
        config.knowledge_directory
        == "knowledge"
    )

    assert (
        config.index_file
        == (
            "rag/index/"
            "knowledge_index.json"
        )
    )

    assert config.chunk_size == 1200
    assert config.chunk_overlap == 200
    assert config.top_k == 5

    assert (
        config.min_similarity
        == 0.25
    )

    assert (
        config.allowed_knowledge_types
        == (
            "mitre",
            "playbook",
            "policy",
            "runbook",
        )
    )

    assert (
        config.safe_summary()[
            "local_only"
        ]
        is True
    )


def test_rag_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Variáveis RAG devem ser carregadas.
    """

    monkeypatch.setenv(
        "RAG_KNOWLEDGE_DIRECTORY",
        "knowledge",
    )

    monkeypatch.setenv(
        "RAG_INDEX_FILE",
        (
            "rag/index/"
            "custom.json"
        ),
    )

    monkeypatch.setenv(
        "RAG_CHUNK_SIZE",
        "800",
    )

    monkeypatch.setenv(
        "RAG_CHUNK_OVERLAP",
        "100",
    )

    monkeypatch.setenv(
        "RAG_TOP_K",
        "7",
    )

    monkeypatch.setenv(
        "RAG_MIN_SIMILARITY",
        "0.45",
    )

    config = RAGConfig.from_env()

    assert config.chunk_size == 800
    assert config.chunk_overlap == 100
    assert config.top_k == 7

    assert (
        config.min_similarity
        == 0.45
    )

    assert (
        config.index_file
        == "rag/index/custom.json"
    )


def test_rag_config_blocks_path_traversal() -> None:
    """
    Caminhos com traversal devem falhar.
    """

    with pytest.raises(
        ValueError,
    ):
        RAGConfig(
            index_file=(
                "../fora/index.json"
            )
        )


def test_rag_config_rejects_invalid_overlap() -> None:
    """
    Overlap não pode ser igual ou
    maior que chunk_size.
    """

    with pytest.raises(
        ValueError,
        match="chunk_overlap",
    ):
        RAGConfig(
            chunk_size=500,
            chunk_overlap=500,
        )


def test_rag_document_rejects_unknown_type() -> None:
    """
    Documento fora das categorias
    oficiais deve falhar.
    """

    with pytest.raises(
        ValueError,
    ):
        RAGDocument(
            document_id="DOC-INVALID",
            document_name="x.md",
            document_type="unknown",
            source_path=(
                "knowledge/x/x.md"
            ),
            content="Conteúdo.",
        )


def test_embedded_chunk_requires_numeric_vector() -> None:
    """
    Embedding inválido deve ser recusado.
    """

    with pytest.raises(
        ValueError,
    ):
        RAGEmbeddedChunk(
            chunk=create_chunk(),
            embedding=[],
            embedding_model=(
                "embeddinggemma"
            ),
        )


def test_loader_loads_supported_document(
    tmp_path: Path,
) -> None:
    """
    Loader deve carregar documento local
    autorizado.
    """

    directory = (
        tmp_path
        / "knowledge"
        / "playbooks"
    )

    directory.mkdir(
        parents=True
    )

    file_path = (
        directory
        / "auth.md"
    )

    file_path.write_text(
        (
            "Procedimento defensivo "
            "de autenticação."
        ),
        encoding="utf-8",
    )

    loader = RAGDocumentLoader(
        RAGConfig(),
        project_root=tmp_path,
    )

    documents = (
        loader.load_all()
    )

    assert len(documents) == 1

    document = documents[0]

    assert (
        document.document_type
        == "playbook"
    )

    assert (
        document.document_name
        == "auth.md"
    )

    assert (
        document.source_path
        == (
            "knowledge/"
            "playbooks/auth.md"
        )
    )

    assert (
        document.metadata[
            "local_source"
        ]
        is True
    )

    assert (
        document.metadata[
            "read_only"
        ]
        is True
    )


def test_loader_ignores_unsupported_extension(
    tmp_path: Path,
) -> None:
    """
    load_all deve ignorar arquivos
    fora das extensões permitidas.
    """

    directory = (
        tmp_path
        / "knowledge"
        / "playbooks"
    )

    directory.mkdir(
        parents=True
    )

    (
        directory
        / "script.exe"
    ).write_bytes(
        b"not-executable"
    )

    loader = RAGDocumentLoader(
        RAGConfig(),
        project_root=tmp_path,
    )

    assert loader.load_all() == []


def test_loader_blocks_file_outside_knowledge(
    tmp_path: Path,
) -> None:
    """
    Arquivo fora de knowledge/
    deve ser bloqueado.
    """

    outside = (
        tmp_path
        / "outside.txt"
    )

    outside.write_text(
        "Conteúdo fora da base.",
        encoding="utf-8",
    )

    (
        tmp_path
        / "knowledge"
    ).mkdir()

    loader = RAGDocumentLoader(
        RAGConfig(),
        project_root=tmp_path,
    )

    with pytest.raises(
        PermissionError,
    ):
        loader.load_file(
            outside
        )


def test_loader_rejects_empty_document(
    tmp_path: Path,
) -> None:
    """
    Documento vazio não entra no RAG.
    """

    directory = (
        tmp_path
        / "knowledge"
        / "policies"
    )

    directory.mkdir(
        parents=True
    )

    file_path = (
        directory
        / "empty.md"
    )

    file_path.write_text(
        "",
        encoding="utf-8",
    )

    loader = RAGDocumentLoader(
        RAGConfig(),
        project_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="não pode estar vazio",
    ):
        loader.load_file(
            file_path
        )


def test_chunker_splits_large_document() -> None:
    """
    Documento grande deve gerar
    múltiplos chunks.
    """

    document = RAGDocument(
        document_id="DOC-CHUNK",
        document_name="auth.md",
        document_type="playbook",
        source_path=(
            "knowledge/playbooks/"
            "auth.md"
        ),
        content=(
            "Falhas de autenticação "
            "precisam ser analisadas. "
            * 40
        ),
    )

    chunker = RAGTextChunker(
        create_config()
    )

    chunks = (
        chunker.chunk_document(
            document
        )
    )

    assert len(chunks) > 1

    assert all(
        len(chunk.content)
        <= 220
        for chunk in chunks
    )

    assert [
        chunk.position
        for chunk in chunks
    ] == list(
        range(
            len(chunks)
        )
    )


def test_chunker_recognizes_markdown_section() -> None:
    """
    Cabeçalho Markdown deve virar section.
    """

    document = RAGDocument(
        document_id="DOC-MD",
        document_name="auth.md",
        document_type="playbook",
        source_path=(
            "knowledge/playbooks/"
            "auth.md"
        ),
        content=(
            "# Triagem\n"
            "Validar usuário, IP e ativo."
        ),
    )

    chunks = (
        RAGTextChunker()
        .chunk_document(
            document
        )
    )

    assert len(chunks) == 1

    assert (
        chunks[0].section
        == "Triagem"
    )


def test_chunk_ids_are_deterministic() -> None:
    """
    Mesmo documento deve produzir
    os mesmos IDs.
    """

    document = RAGDocument(
        document_id="DOC-ID",
        document_name="id.md",
        document_type="runbook",
        source_path=(
            "knowledge/runbooks/id.md"
        ),
        content=(
            "Procedimento defensivo "
            "e controlado."
        ),
    )

    chunker = RAGTextChunker()

    first = (
        chunker.chunk_document(
            document
        )
    )

    second = (
        chunker.chunk_document(
            document
        )
    )

    assert [
        item.chunk_id
        for item in first
    ] == [
        item.chunk_id
        for item in second
    ]


def test_embedding_service_embeds_chunk() -> None:
    """
    Serviço deve transformar chunk
    em RAGEmbeddedChunk.
    """

    service = RAGEmbeddingService(
        embedding_function=(
            lambda text: [
                0.1,
                0.2,
                0.3,
            ]
        ),
        embedding_model=(
            "embeddinggemma"
        ),
    )

    result = service.embed_chunk(
        create_chunk()
    )

    assert (
        result.embedding
        == [
            0.1,
            0.2,
            0.3,
        ]
    )

    assert (
        result.embedding_model
        == "embeddinggemma"
    )


def test_embedding_service_accepts_same_dimension() -> None:
    """
    Batch de dimensões iguais deve passar.
    """

    service = RAGEmbeddingService(
        embedding_function=(
            lambda text: [
                float(
                    len(text)
                ),
                0.5,
            ]
        )
    )

    results = service.embed_chunks(
        [
            create_chunk(
                chunk_id="CHUNK-A"
            ),
            create_chunk(
                chunk_id="CHUNK-B",
                position=1,
            ),
        ]
    )

    assert len(results) == 2

    assert (
        len(
            results[0].embedding
        )
        == len(
            results[1].embedding
        )
    )


def test_embedding_service_rejects_dimension_change() -> None:
    """
    Vetores do mesmo batch precisam
    possuir mesma dimensão.
    """

    calls = {
        "count": 0
    }

    def fake_embedding(
        text: str,
    ) -> list[float]:
        calls["count"] += 1

        if calls["count"] == 1:
            return [
                1.0,
                0.0,
            ]

        return [
            1.0,
            0.0,
            0.0,
        ]

    service = RAGEmbeddingService(
        embedding_function=(
            fake_embedding
        )
    )

    with pytest.raises(
        ValueError,
        match="mesma dimensão",
    ):
        service.embed_chunks(
            [
                create_chunk(
                    chunk_id="CHUNK-A"
                ),
                create_chunk(
                    chunk_id="CHUNK-B",
                    position=1,
                ),
            ]
        )


def test_vector_index_add_and_get(
    tmp_path: Path,
) -> None:
    """
    Índice deve armazenar e recuperar
    chunk vetorizado.
    """

    index = RAGVectorIndex(
        create_config(),
        project_root=tmp_path,
    )

    item = (
        create_embedded_chunk()
    )

    index.add(
        item
    )

    assert index.count == 1
    assert index.dimension == 3

    assert (
        index.embedding_model
        == "embeddinggemma"
    )

    restored = index.get(
        "CHUNK-0001"
    )

    assert restored is not None

    assert (
        restored.chunk.chunk_id
        == "CHUNK-0001"
    )


def test_vector_index_rejects_duplicate(
    tmp_path: Path,
) -> None:
    """
    add não aceita chunk_id duplicado.
    """

    index = RAGVectorIndex(
        create_config(),
        project_root=tmp_path,
    )

    item = (
        create_embedded_chunk()
    )

    index.add(
        item
    )

    with pytest.raises(
        ValueError,
        match="já existe",
    ):
        index.add(
            item
        )


def test_vector_index_rejects_wrong_dimension(
    tmp_path: Path,
) -> None:
    """
    Índice não pode misturar
    dimensões vetoriais.
    """

    index = RAGVectorIndex(
        create_config(),
        project_root=tmp_path,
    )

    index.add(
        create_embedded_chunk(
            chunk_id="CHUNK-A",
            embedding=[
                1.0,
                0.0,
                0.0,
            ],
        )
    )

    with pytest.raises(
        ValueError,
        match="Dimensão",
    ):
        index.add(
            create_embedded_chunk(
                chunk_id="CHUNK-B",
                embedding=[
                    1.0,
                    0.0,
                ],
            )
        )


def test_vector_index_save_and_load(
    tmp_path: Path,
) -> None:
    """
    Índice deve persistir e restaurar
    JSON local.
    """

    config = create_config()

    first = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    first.add(
        create_embedded_chunk()
    )

    path = first.save()

    assert path.exists()

    second = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    loaded = second.load()

    assert loaded == 1
    assert second.count == 1
    assert second.dimension == 3

    assert (
        second.embedding_model
        == "embeddinggemma"
    )

    assert (
        second.safe_summary()[
            "format"
        ]
        == "JSON"
    )

    assert (
        second.safe_summary()[
            "executable_format"
        ]
        is False
    )


def test_vector_index_blocks_outside_index_path(
    tmp_path: Path,
) -> None:
    """
    Índice não pode ser persistido
    fora de rag/index/.
    """

    config = RAGConfig(
        index_file=(
            "storage/"
            "knowledge.json"
        )
    )

    with pytest.raises(
        PermissionError,
    ):
        RAGVectorIndex(
            config,
            project_root=tmp_path,
        )


def test_retriever_ranks_most_similar_first(
    tmp_path: Path,
) -> None:
    """
    Maior similaridade deve ficar
    na primeira posição.
    """

    config = create_config()

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add_many(
        [
            create_embedded_chunk(
                chunk_id="CHUNK-AUTH",
                embedding=[
                    1.0,
                    0.0,
                    0.0,
                ],
            ),
            create_embedded_chunk(
                chunk_id="CHUNK-OTHER",
                embedding=[
                    0.0,
                    1.0,
                    0.0,
                ],
            ),
        ]
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

    result = retriever.search(
        "Falhas de login"
    )

    assert len(result.hits) >= 1

    assert (
        result.hits[0]
        .chunk
        .chunk_id
        == "CHUNK-AUTH"
    )

    assert (
        result.hits[0]
        .similarity_score
        == 1.0
    )


def test_retriever_applies_similarity_threshold(
    tmp_path: Path,
) -> None:
    """
    Resultado abaixo do limite
    não deve ser retornado.
    """

    config = RAGConfig(
        index_file=(
            "rag/index/"
            "knowledge_index.json"
        ),
        min_similarity=0.90,
    )

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add(
        create_embedded_chunk(
            embedding=[
                0.0,
                1.0,
                0.0,
            ]
        )
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

    result = retriever.search(
        "Consulta"
    )

    assert result.hits == []


def test_retriever_rejects_wrong_query_dimension(
    tmp_path: Path,
) -> None:
    """
    Vetor da consulta precisa ter
    dimensão igual ao índice.
    """

    config = create_config()

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add(
        create_embedded_chunk(
            embedding=[
                1.0,
                0.0,
                0.0,
            ]
        )
    )

    retriever = RAGRetriever(
        index,
        config,
        embedding_function=(
            lambda text: [
                1.0,
                0.0,
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="incompatível",
    ):
        retriever.search(
            "Consulta"
        )


def test_adapter_converts_hit_to_knowledge_chunk() -> None:
    """
    Adapter deve preservar fonte,
    conteúdo e score.
    """

    chunk = create_chunk(
        chunk_id="CHUNK-ADAPTER"
    )

    hit = RAGSearchHit(
        chunk=chunk,
        similarity_score=0.97,
    )

    result = RAGSearchResult(
        query="Como investigar?",
        hits=[
            hit,
        ],
        top_k=5,
        min_similarity=0.25,
    )

    adapter = (
        RAGKnowledgeAdapter()
    )

    chunks = (
        adapter.to_knowledge_chunks(
            result
        )
    )

    assert len(chunks) == 1

    converted = chunks[0]

    assert (
        converted.chunk_id
        == "CHUNK-ADAPTER"
    )

    assert (
        converted.similarity_score
        == 0.97
    )

    assert (
        converted.metadata[
            "retrieval_source"
        ]
        == "LOCAL_RAG_INDEX"
    )


def test_adapter_rejects_agent_payload_without_hits() -> None:
    """
    AG-08 não deve receber payload RAG
    sem conhecimento recuperado.
    """

    result = RAGSearchResult(
        query="Consulta sem resposta",
        hits=[],
        top_k=5,
        min_similarity=0.25,
    )

    adapter = (
        RAGKnowledgeAdapter()
    )

    with pytest.raises(
        ValueError,
        match="sem chunks",
    ):
        adapter.build_agent_payload(
            result=result,
            answer="Resposta",
            confidence=50,
        )


def test_adapter_deduplicates_evidence_references() -> None:
    """
    Referências repetidas devem ser
    normalizadas sem invenção.
    """

    hit = RAGSearchHit(
        chunk=create_chunk(),
        similarity_score=0.95,
    )

    result = RAGSearchResult(
        query="Consulta",
        hits=[
            hit,
        ],
        top_k=5,
        min_similarity=0.25,
    )

    payload = (
        RAGKnowledgeAdapter()
        .build_agent_payload(
            result=result,
            answer="Resposta baseada na fonte.",
            confidence=90,
            evidence_references=[
                "EVID-1",
                "EVID-1",
                "EVID-2",
            ],
        )
    )

    assert (
        payload[
            "evidence_references"
        ]
        == [
            "EVID-1",
            "EVID-2",
        ]
    )


def test_rag_knowledge_service_executes_ag08(
    tmp_path: Path,
) -> None:
    """
    Serviço integrado deve executar
    retrieval e AG-08.
    """

    config = create_config()

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add(
        create_embedded_chunk(
            chunk_id="CHUNK-AUTH",
            embedding=[
                1.0,
                0.0,
                0.0,
            ],
        )
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

    service = RAGKnowledgeService(
        retriever
    )

    result = service.execute(
        query=(
            "Como investigar "
            "falhas de login?"
        ),
        answer=(
            "Correlacionar usuário, "
            "IP e ativo."
        ),
        confidence=94,
        case_snapshot={
            "alert": {
                "alert_id": (
                    "ALT-RAG-0001"
                ),
                "event": {
                    "event_type": (
                        "AUTH_BRUTE_FORCE"
                    ),
                },
            },
        },
        execution_id=(
            "EXEC-RAG-0001"
        ),
        case_id=(
            "CASE-RAG-0001"
        ),
        correlation_id=(
            "CORR-RAG-0001"
        ),
        case_version=1,
        evidence_references=[
            "EVID-RAG-0001",
        ],
        knowledge_id=(
            "KNOW-RAG-0001"
        ),
    )

    search_result = (
        result[
            "search_result"
        ]
    )

    agent_result = (
        result[
            "agent_result"
        ]
    )

    assert len(
        search_result.hits
    ) == 1

    assert agent_result.success is True

    assert (
        "knowledge_result"
        in agent_result.output
    )

    assert (
        service.safe_summary()[
            "local_only"
        ]
        is True
    )

    assert (
        service.safe_summary()[
            "web_search"
        ]
        is False
    )

    assert (
        service.safe_summary()[
            "phase7_orchestration"
        ]
        is False
    )


def test_rag_knowledge_service_requires_alert(
    tmp_path: Path,
) -> None:
    """
    Serviço deve falhar fechado
    sem alerta no snapshot.
    """

    config = create_config()

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add(
        create_embedded_chunk()
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

    service = RAGKnowledgeService(
        retriever
    )

    with pytest.raises(
        ValueError,
        match="objeto 'alert'",
    ):
        service.execute(
            query="Consulta",
            answer="Resposta",
            confidence=90,
            case_snapshot={},
            execution_id="EXEC-1",
            case_id="CASE-1",
            correlation_id="CORR-1",
            case_version=1,
        )


def test_complete_local_rag_pipeline(
    tmp_path: Path,
) -> None:
    """
    Valida o pipeline local:

    arquivo
    -> documento
    -> chunk
    -> embedding
    -> índice
    -> retrieval.
    """

    knowledge_directory = (
        tmp_path
        / "knowledge"
        / "playbooks"
    )

    knowledge_directory.mkdir(
        parents=True
    )

    document_path = (
        knowledge_directory
        / "bruteforce.md"
    )

    document_path.write_text(
        (
            "# Triagem\n"
            "Investigar falhas repetidas "
            "de autenticação. Validar "
            "usuário, IP e ativo."
        ),
        encoding="utf-8",
    )

    config = create_config()

    loader = RAGDocumentLoader(
        config,
        project_root=tmp_path,
    )

    documents = loader.load_all()

    assert len(documents) == 1

    chunker = RAGTextChunker(
        config
    )

    chunks = (
        chunker.chunk_documents(
            documents
        )
    )

    assert len(chunks) >= 1

    embedding_service = (
        RAGEmbeddingService(
            embedding_function=(
                lambda text: [
                    1.0,
                    0.0,
                    0.0,
                ]
            ),
            embedding_model=(
                "embeddinggemma"
            ),
        )
    )

    embedded = (
        embedding_service
        .embed_chunks(
            chunks
        )
    )

    index = RAGVectorIndex(
        config,
        project_root=tmp_path,
    )

    index.add_many(
        embedded
    )

    assert index.count == len(
        embedded
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

    search_result = (
        retriever.search(
            "Como investigar "
            "falhas de login?"
        )
    )

    assert len(
        search_result.hits
    ) >= 1

    assert (
        search_result
        .hits[0]
        .chunk
        .document_name
        == "bruteforce.md"
    )