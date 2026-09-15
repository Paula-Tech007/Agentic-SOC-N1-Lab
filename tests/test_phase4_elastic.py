"""
Testes automatizados da integração Elastic / Elasticsearch
do Agentic SOC N1 Lab.

Fase 4.2 — Elastic / Elasticsearch read-only.

Estes testes validam:

- configuração segura por variáveis de ambiente;
- API key não exposta;
- índices autorizados;
- validação de timeout;
- cliente HTTP read-only;
- pesquisa de alertas;
- pesquisa de eventos;
- consulta de documento;
- bloqueio de índices não autorizados;
- bloqueio de métodos de escrita;
- bloqueio de endpoints de escrita;
- tratamento de HTTP 500;
- tratamento de resposta JSON inválida;
- handlers oficiais;
- registro das ferramentas Elastic;
- integração completa com ToolRuntime;
- deny-by-default por agente.

Nenhum teste realiza conexão externa.
"""

import httpx
import pytest

from tools import (
    ToolExecutionStatus,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from tools.elastic import (
    ElasticClient,
    ElasticConfig,
    ElasticHTTPError,
    ElasticResponseError,
    ElasticToolHandlers,
)


FAKE_API_KEY = "CHAVE-FICTICIA-NAO-REAL"


def create_elastic_config() -> ElasticConfig:
    """
    Cria configuração Elastic fictícia
    para testes sem acesso real à rede.
    """

    return ElasticConfig(
        base_url="https://elastic.lab.local",
        api_key=FAKE_API_KEY,
        alerts_index="alerts-*",
        events_index="events-*",
        verify_ssl=True,
        timeout_seconds=20,
    )


def fake_elastic_server(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula um pequeno servidor Elastic.

    Nenhuma conexão externa é realizada.
    """

    authorization = request.headers.get(
        "Authorization"
    )

    if authorization != f"ApiKey {FAKE_API_KEY}":
        return httpx.Response(
            401,
            json={
                "error": "Unauthorized",
            },
        )

    if (
        request.method == "POST"
        and request.url.path
        == "/alerts-*/_search"
    ):
        return httpx.Response(
            200,
            json={
                "hits": {
                    "total": {
                        "value": 1,
                        "relation": "eq",
                    },
                    "hits": [
                        {
                            "_index": (
                                "alerts-2026.09.15"
                            ),
                            "_id": "ALT-001",
                            "_source": {
                                "event_type": (
                                    "AUTH_BRUTE_FORCE"
                                ),
                                "severity": "HIGH",
                            },
                        }
                    ],
                }
            },
        )

    if (
        request.method == "POST"
        and request.url.path
        == "/events-*/_search"
    ):
        return httpx.Response(
            200,
            json={
                "hits": {
                    "total": {
                        "value": 1,
                        "relation": "eq",
                    },
                    "hits": [
                        {
                            "_index": (
                                "events-2026.09.15"
                            ),
                            "_id": "EVT-001",
                            "_source": {
                                "username": "lab.user",
                                "source_ip": (
                                    "203.0.113.10"
                                ),
                            },
                        }
                    ],
                }
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/alerts-2026.09.15/_doc/ALT-001"
    ):
        return httpx.Response(
            200,
            json={
                "_index": (
                    "alerts-2026.09.15"
                ),
                "_id": "ALT-001",
                "found": True,
                "_source": {
                    "event_type": (
                        "AUTH_BRUTE_FORCE"
                    ),
                    "severity": "HIGH",
                },
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/alerts-2026.09.15/_doc/HTTP500"
    ):
        return httpx.Response(
            500,
            json={
                "error": "Falha simulada.",
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/alerts-2026.09.15/_doc/BADJSON"
    ):
        return httpx.Response(
            200,
            text="NAO-E-JSON",
        )

    return httpx.Response(
        404,
        json={
            "error": (
                "Rota simulada não encontrada."
            ),
        },
    )


def create_elastic_client() -> ElasticClient:
    """
    Cria cliente Elastic utilizando
    httpx.MockTransport.
    """

    return ElasticClient(
        config=create_elastic_config(),
        transport=httpx.MockTransport(
            fake_elastic_server
        ),
    )


def create_runtime() -> ToolRuntime:
    """
    Cria ToolRuntime com as três
    ferramentas Elastic registradas.
    """

    client = create_elastic_client()

    handlers = ElasticToolHandlers(
        client=client
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    return ToolRuntime(
        registry=registry
    )


def test_elastic_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Configuração válida pode ser criada
    por variáveis de ambiente.
    """

    monkeypatch.setenv(
        "ELASTIC_URL",
        "https://elastic.lab.local/",
    )

    monkeypatch.setenv(
        "ELASTIC_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.setenv(
        "ELASTIC_ALERTS_INDEX",
        "alerts-*",
    )

    monkeypatch.setenv(
        "ELASTIC_EVENTS_INDEX",
        "events-*",
    )

    monkeypatch.setenv(
        "ELASTIC_VERIFY_SSL",
        "true",
    )

    monkeypatch.setenv(
        "ELASTIC_TIMEOUT_SECONDS",
        "20",
    )

    config = ElasticConfig.from_env()

    assert (
        config.base_url
        == "https://elastic.lab.local"
    )

    assert (
        config.alerts_index
        == "alerts-*"
    )

    assert (
        config.events_index
        == "events-*"
    )

    assert config.verify_ssl is True

    assert config.timeout_seconds == 20

    assert config.api_key == FAKE_API_KEY


def test_elastic_config_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ELASTIC_URL é obrigatória.
    """

    monkeypatch.delenv(
        "ELASTIC_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "ELASTIC_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.setenv(
        "ELASTIC_ALERTS_INDEX",
        "alerts-*",
    )

    monkeypatch.setenv(
        "ELASTIC_EVENTS_INDEX",
        "events-*",
    )

    with pytest.raises(ValueError):
        ElasticConfig.from_env()


def test_elastic_config_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ELASTIC_API_KEY é obrigatória.
    """

    monkeypatch.setenv(
        "ELASTIC_URL",
        "https://elastic.lab.local",
    )

    monkeypatch.delenv(
        "ELASTIC_API_KEY",
        raising=False,
    )

    monkeypatch.setenv(
        "ELASTIC_ALERTS_INDEX",
        "alerts-*",
    )

    monkeypatch.setenv(
        "ELASTIC_EVENTS_INDEX",
        "events-*",
    )

    with pytest.raises(ValueError):
        ElasticConfig.from_env()


def test_elastic_config_requires_indices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Os dois padrões de índice são obrigatórios.
    """

    monkeypatch.setenv(
        "ELASTIC_URL",
        "https://elastic.lab.local",
    )

    monkeypatch.setenv(
        "ELASTIC_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.delenv(
        "ELASTIC_ALERTS_INDEX",
        raising=False,
    )

    monkeypatch.setenv(
        "ELASTIC_EVENTS_INDEX",
        "events-*",
    )

    with pytest.raises(ValueError):
        ElasticConfig.from_env()

    monkeypatch.setenv(
        "ELASTIC_ALERTS_INDEX",
        "alerts-*",
    )

    monkeypatch.delenv(
        "ELASTIC_EVENTS_INDEX",
        raising=False,
    )

    with pytest.raises(ValueError):
        ElasticConfig.from_env()


def test_elastic_config_does_not_expose_api_key() -> None:
    """
    repr e safe_summary não podem
    expor a API key.
    """

    config = create_elastic_config()

    representation = repr(
        config
    )

    summary = config.safe_summary()

    assert (
        FAKE_API_KEY
        not in representation
    )

    assert (
        FAKE_API_KEY
        not in str(summary)
    )

    assert (
        summary["api_key_configured"]
        is True
    )


def test_elastic_config_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Timeout fora do limite permitido
    precisa ser recusado.
    """

    monkeypatch.setenv(
        "ELASTIC_URL",
        "https://elastic.lab.local",
    )

    monkeypatch.setenv(
        "ELASTIC_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.setenv(
        "ELASTIC_ALERTS_INDEX",
        "alerts-*",
    )

    monkeypatch.setenv(
        "ELASTIC_EVENTS_INDEX",
        "events-*",
    )

    monkeypatch.setenv(
        "ELASTIC_TIMEOUT_SECONDS",
        "999",
    )

    with pytest.raises(ValueError):
        ElasticConfig.from_env()


def test_elastic_search_alerts_read_only() -> None:
    """
    Pesquisa de alertas precisa retornar
    resposta simulada do Elastic.
    """

    client = create_elastic_client()

    result = client.search_alerts(
        {
            "term": {
                "event_type": (
                    "AUTH_BRUTE_FORCE"
                ),
            }
        },
        size=50,
    )

    hits = result["hits"]["hits"]

    assert len(hits) == 1

    assert (
        hits[0]["_id"]
        == "ALT-001"
    )


def test_elastic_search_events_read_only() -> None:
    """
    Pesquisa de eventos precisa retornar
    resposta simulada do Elastic.
    """

    client = create_elastic_client()

    result = client.search_events(
        {
            "term": {
                "username": "lab.user",
            }
        },
        size=100,
    )

    hits = result["hits"]["hits"]

    assert len(hits) == 1

    assert (
        hits[0]["_id"]
        == "EVT-001"
    )


def test_elastic_get_document() -> None:
    """
    Consulta de documento existente.
    """

    client = create_elastic_client()

    result = client.get_document(
        index="alerts-2026.09.15",
        document_id="ALT-001",
    )

    assert result["_id"] == "ALT-001"

    assert result["found"] is True


def test_elastic_blocks_unauthorized_index() -> None:
    """
    Índice fora da allowlist
    precisa ser bloqueado.
    """

    client = create_elastic_client()

    with pytest.raises(PermissionError):
        client.get_document(
            index=(
                "financeiro-secreto-2026"
            ),
            document_id="DOC-001",
        )


def test_elastic_blocks_delete_method() -> None:
    """
    DELETE não faz parte da allowlist.
    """

    client = create_elastic_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="DELETE",
            path=(
                "/alerts-2026.09.15"
                "/_doc/ALT-001"
            ),
            allowed_index=(
                "alerts-2026.09.15"
            ),
            operation="get_document",
        )


def test_elastic_blocks_write_endpoint() -> None:
    """
    Endpoint de escrita precisa ser
    bloqueado antes da chamada HTTP.
    """

    client = create_elastic_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="POST",
            path=(
                "/alerts-*/"
                "_update_by_query"
            ),
            allowed_index="alerts-*",
            operation="search",
            payload={},
        )


def test_elastic_handles_http_error() -> None:
    """
    HTTP 500 precisa ser convertido
    para ElasticHTTPError.
    """

    client = create_elastic_client()

    with pytest.raises(
        ElasticHTTPError
    ):
        client.get_document(
            index="alerts-2026.09.15",
            document_id="HTTP500",
        )


def test_elastic_handles_invalid_json() -> None:
    """
    Conteúdo inválido precisa gerar
    ElasticResponseError.
    """

    client = create_elastic_client()

    with pytest.raises(
        ElasticResponseError
    ):
        client.get_document(
            index="alerts-2026.09.15",
            document_id="BADJSON",
        )


def test_elastic_handlers_register_three_tools() -> None:
    """
    Os três handlers Elastic precisam
    ser registrados no ToolRegistry.
    """

    handlers = ElasticToolHandlers(
        client=create_elastic_client()
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    assert (
        registry.registered_tool_ids()
        == (
            "elastic.get_document",
            "elastic.search_alerts",
            "elastic.search_events",
        )
    )


def test_elastic_runtime_search_alerts() -> None:
    """
    Testa fluxo completo de search_alerts
    através do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-ELASTIC-0001",
        execution_id="EXEC-ELASTIC-0001",
        agent_id="AG-03",
        case_id="CASE-ELASTIC-0001",
        correlation_id=(
            "CORR-ELASTIC-0001"
        ),
        tool_id="elastic.search_alerts",
        input_payload={
            "query": {
                "term": {
                    "event_type": (
                        "AUTH_BRUTE_FORCE"
                    ),
                }
            },
            "size": 50,
        },
        timeout_seconds=20,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    assert result.attempts == 1

    evidence = (
        result.evidence_payload.to_dict()
    )

    assert (
        evidence["source"]
        == "ELASTIC"
    )

    assert (
        evidence["operation"]
        == "search_alerts"
    )

    assert (
        evidence["read_only"]
        is True
    )


def test_elastic_runtime_search_events() -> None:
    """
    Testa search_events através
    do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-ELASTIC-0002",
        execution_id="EXEC-ELASTIC-0002",
        agent_id="AG-05",
        case_id="CASE-ELASTIC-0001",
        correlation_id=(
            "CORR-ELASTIC-0001"
        ),
        tool_id="elastic.search_events",
        input_payload={
            "query": {
                "term": {
                    "username": "lab.user",
                }
            },
            "size": 100,
        },
        timeout_seconds=20,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    output = (
        result.output_payload.to_dict()
    )

    assert (
        output["result"]
        ["hits"]["hits"][0]["_id"]
        == "EVT-001"
    )


def test_elastic_runtime_get_document() -> None:
    """
    Testa get_document através
    do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-ELASTIC-0003",
        execution_id="EXEC-ELASTIC-0003",
        agent_id="AG-03",
        case_id="CASE-ELASTIC-0001",
        correlation_id=(
            "CORR-ELASTIC-0001"
        ),
        tool_id="elastic.get_document",
        input_payload={
            "index": (
                "alerts-2026.09.15"
            ),
            "document_id": "ALT-001",
        },
        timeout_seconds=15,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    output = (
        result.output_payload.to_dict()
    )

    assert (
        output["result"]["_id"]
        == "ALT-001"
    )


def test_elastic_runtime_denies_unauthorized_agent() -> None:
    """
    AG-05 pode pesquisar eventos,
    mas não possui permissão para
    elastic.get_document.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id=(
            "REQ-ELASTIC-DENIED"
        ),
        execution_id=(
            "EXEC-ELASTIC-DENIED"
        ),
        agent_id="AG-05",
        case_id="CASE-ELASTIC-0001",
        correlation_id=(
            "CORR-ELASTIC-0001"
        ),
        tool_id="elastic.get_document",
        input_payload={
            "index": (
                "alerts-2026.09.15"
            ),
            "document_id": "ALT-001",
        },
        timeout_seconds=15,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.DENIED
    )

    assert result.success is False

    assert (
        result.error_code
        == "TOOL_ACCESS_DENIED"
    )

    assert result.attempts == 0