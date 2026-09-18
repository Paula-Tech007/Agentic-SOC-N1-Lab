"""
Testes formais do FullEnrichmentPayloadProvider.

Valida a composição final de enriquecimento:

- AG-04 Threat Intelligence;
- AG-05 Identity;
- AG-06 Asset;
- AG-07 Phishing;
- AG-08 Knowledge / RAG.

Escopo específico deste arquivo:

- AG-07 recebe somente dados provenientes
  das Tools oficiais de Email;
- nenhuma rede real é acessada;
- nenhuma URL é aberta;
- nenhum anexo é baixado;
- nenhum anexo é executado;
- ausência de classificação explícita
  permanece INCONCLUSIVE;
- severidade é preservada do caso;
- ausência de message_id falha fechado;
- AG-07 fora de PHISHING falha fechado;
- o teste não depende de índice RAG local
  previamente existente.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.full_enrichment_payload_provider import (
    FULL_ENRICHMENT_AGENT_IDS,
    FullEnrichmentPayloadProvider,
)

from app.full_enrichment_tool_bootstrap import (
    build_full_enrichment_tool_runtime,
)

from core.schemas import (
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    Severity,
)

from core.state import (
    CaseState,
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


def _unused_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Transporte neutro para integrações
    que não fazem parte do cenário AG-07.
    """

    return httpx.Response(
        200,
        json={},
        request=request,
    )


def _email_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula as quatro consultas oficiais
    de Email / Phishing sem rede real.
    """

    path = request.url.path

    if path.endswith(
        "/attachments/metadata"
    ):
        payload = {
            "attachments": [
                {
                    "name": "documento.pdf",
                    "sha256": (
                        "A" * 64
                    ),
                }
            ],
        }

    elif path.endswith(
        "/authentication-results"
    ):
        payload = {
            "spf": "fail",
            "dkim": "pass",
            "dmarc": "fail",
            "confidence": 85,
            "suspicious_indicators": [
                "spf_fail",
                "dmarc_fail",
            ],
        }

    elif path.endswith(
        "/headers"
    ):
        payload = {
            "from": (
                "sender@example.test"
            ),
            "to": [
                "user@example.test",
            ],
            "subject": (
                "Mensagem suspeita "
                "de laboratorio"
            ),
        }

    elif path.endswith(
        "/metadata"
    ):
        payload = {
            "message_id": (
                "MSG-FULL-0001"
            ),
            "sender": (
                "sender@example.test"
            ),
            "recipients": [
                "user@example.test",
            ],
            "subject": (
                "Mensagem suspeita "
                "de laboratorio"
            ),
            "urls": [
                (
                    "https://"
                    "example.invalid/test"
                ),
            ],
            "confidence": 88,
        }

    else:
        return httpx.Response(
            404,
            json={
                "error": "unexpected_path",
            },
            request=request,
        )

    return httpx.Response(
        200,
        json=payload,
        request=request,
    )


def _create_test_rag_retriever(
    tmp_path: Path,
) -> RAGRetriever:
    """
    Cria índice RAG temporário e isolado.

    O teste não depende de:

    - rag/index local;
    - arquivo previamente gerado;
    - Ollama;
    - rede;
    - ambiente externo.
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
        chunk_id="CHUNK-TEST-PHISH-0001",
        document_id="DOC-TEST-PHISH-0001",
        document_name=(
            "phishing_test.md"
        ),
        document_type="runbook",
        section="Triagem",
        content=(
            "Runbook defensivo para "
            "analise de phishing."
        ),
        source_path=(
            "knowledge/runbooks/"
            "phishing_test.md"
        ),
        position=0,
        metadata={
            "local_source": True,
        },
    )

    embedded = RAGEmbeddedChunk(
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

    index.add(
        embedded
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


def _build_provider(
    tmp_path: Path,
) -> FullEnrichmentPayloadProvider:
    """
    Cria provider completo com:

    - ToolRuntime oficial;
    - integrações simuladas;
    - índice RAG temporário;
    - nenhuma rede real.
    """

    email_config = EmailConfig(
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

    runtime = (
        build_full_enrichment_tool_runtime(
            env=TEST_ENV,
            misp_transport=(
                httpx.MockTransport(
                    _unused_transport
                )
            ),
            identity_transport=(
                httpx.MockTransport(
                    _unused_transport
                )
            ),
            asset_transport=(
                httpx.MockTransport(
                    _unused_transport
                )
            ),
            email_transport=(
                httpx.MockTransport(
                    _email_transport
                )
            ),
            email_config=email_config,
        )
    )

    retriever = (
        _create_test_rag_retriever(
            tmp_path
        )
    )

    return (
        FullEnrichmentPayloadProvider(
            runtime,
            retriever,
        )
    )


def _create_case(
    *,
    event_type: AlertType = (
        AlertType.PHISHING
    ),
    raw_event: (
        dict[str, object]
        | None
    ) = None,
) -> CaseState:
    """
    Cria caso controlado para AG-07.
    """

    if raw_event is None:
        raw_event = {
            "message_id": (
                "MSG-FULL-0001"
            ),
        }

    alert = Alert(
        alert_id=(
            "ALT-FULL-PHISH-0001"
        ),
        correlation_id=(
            "CORR-FULL-PHISH-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Full Provider Phishing Test"
            ),
        ),
        event=AlertEvent(
            event_type=event_type,
            category="email",
            message=(
                "Mensagem suspeita "
                "simulada no laboratorio."
            ),
            raw_event=raw_event,
        ),
        initial_severity=(
            Severity.HIGH
        ),
    )

    return CaseState(
        case_id=(
            "CASE-FULL-PHISH-0001"
        ),
        correlation_id=(
            "CORR-FULL-PHISH-0001"
        ),
        alert=alert,
    )


def test_full_enrichment_agent_catalog(
) -> None:
    """
    Provider completo deve cobrir
    exatamente AG-04 até AG-08.
    """

    assert (
        FULL_ENRICHMENT_AGENT_IDS
        == (
            "AG-04",
            "AG-05",
            "AG-06",
            "AG-07",
            "AG-08",
        )
    )


def test_ag07_builds_valid_phishing_payload(
    tmp_path: Path,
) -> None:
    """
    AG-07 deve receber payload
    defensivo completo e rastreável.
    """

    provider = _build_provider(
        tmp_path
    )

    case_state = _create_case()

    payload = provider.build_payload(
        case_state=case_state,
        agent_id="AG-07",
    )

    assert (
        payload["sender"]
        == "sender@example.test"
    )

    assert (
        payload["recipients"]
        == [
            "user@example.test",
        ]
    )

    assert (
        payload["subject"]
        == (
            "Mensagem suspeita "
            "de laboratorio"
        )
    )

    assert (
        payload["authentication"]
        == {
            "spf": "fail",
            "dkim": "pass",
            "dmarc": "fail",
        }
    )

    assert (
        payload[
            "attachment_names"
        ]
        == [
            "documento.pdf",
        ]
    )

    assert (
        payload[
            "attachment_hashes"
        ]
        == [
            "A" * 64,
        ]
    )

    assert (
        payload["classification"]
        == "INCONCLUSIVE"
    )

    assert (
        payload["severity"]
        == "HIGH"
    )

    assert (
        payload["confidence"]
        == 88
    )

    assert (
        "spf_fail"
        in payload[
            "suspicious_indicators"
        ]
    )

    assert (
        "dmarc_fail"
        in payload[
            "suspicious_indicators"
        ]
    )


def test_ag07_without_message_id_fails_closed(
    tmp_path: Path,
) -> None:
    """
    AG-07 não pode consultar e-mail
    sem identificador explícito.
    """

    provider = _build_provider(
        tmp_path
    )

    case_state = _create_case(
        raw_event={},
    )

    with pytest.raises(
        RuntimeError,
        match="message_id",
    ):
        provider.build_payload(
            case_state=case_state,
            agent_id="AG-07",
        )


def test_ag07_rejects_non_phishing_alert(
    tmp_path: Path,
) -> None:
    """
    AG-07 não deve operar em alerta
    de outro tipo.
    """

    provider = _build_provider(
        tmp_path
    )

    case_state = _create_case(
        event_type=(
            AlertType.AUTH_BRUTE_FORCE
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="PHISHING",
    ):
        provider.build_payload(
            case_state=case_state,
            agent_id="AG-07",
        )