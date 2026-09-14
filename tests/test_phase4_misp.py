"""
Testes automatizados da integração MISP
do Agentic SOC N1 Lab.

Fase 4.1 — Threat Intelligence / MISP.

Estes testes validam:

- configuração segura por variáveis de ambiente;
- API key não exposta em repr;
- normalização da URL;
- SSL habilitado por padrão;
- validação de timeout;
- cliente HTTP read-only;
- pesquisa de IOC;
- consulta de evento;
- consulta de atributo;
- bloqueio de endpoints de escrita;
- bloqueio de métodos HTTP não autorizados;
- tratamento de HTTP 500;
- tratamento de resposta JSON inválida;
- handlers oficiais;
- registro das ferramentas MISP;
- integração completa com ToolRuntime;
- deny-by-default por agente.
"""

import os

import httpx
import pytest

from tools import (
    ToolExecutionStatus,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from tools.threat_intel import (
    MISPClient,
    MISPConfig,
    MISPHTTPError,
    MISPResponseError,
    MISPToolHandlers,
)


FAKE_API_KEY = "CHAVE-FICTICIA-NAO-REAL"


def create_misp_config() -> MISPConfig:
    """
    Cria configuração MISP fictícia
    para testes sem acesso real à rede.
    """

    return MISPConfig(
        base_url="https://misp.lab.local",
        api_key=FAKE_API_KEY,
        verify_ssl=True,
        timeout_seconds=15,
    )


def fake_misp_server(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula um pequeno servidor MISP.

    Nenhuma conexão externa é realizada.
    """

    if (
        request.method == "POST"
        and request.url.path
        == "/attributes/restSearch"
    ):
        authorization = request.headers.get(
            "Authorization"
        )

        if authorization != FAKE_API_KEY:
            return httpx.Response(
                401,
                json={
                    "error": "Unauthorized",
                },
            )

        return httpx.Response(
            200,
            json={
                "response": {
                    "Attribute": [
                        {
                            "id": "123",
                            "type": "ip-dst",
                            "value": "185.10.20.30",
                            "category": (
                                "Network activity"
                            ),
                        }
                    ]
                }
            },
        )

    if (
        request.method == "GET"
        and request.url.path == "/events/42"
    ):
        return httpx.Response(
            200,
            json={
                "Event": {
                    "id": "42",
                    "info": (
                        "Evento MISP simulado"
                    ),
                }
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/attributes/123"
    ):
        return httpx.Response(
            200,
            json={
                "Attribute": {
                    "id": "123",
                    "type": "ip-dst",
                    "value": "185.10.20.30",
                }
            },
        )

    if (
        request.method == "GET"
        and request.url.path == "/events/500"
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
        == "/events/bad-json"
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


def create_misp_client() -> MISPClient:
    """
    Cria cliente MISP utilizando
    httpx.MockTransport.
    """

    return MISPClient(
        config=create_misp_config(),
        transport=httpx.MockTransport(
            fake_misp_server
        ),
    )


def create_runtime() -> ToolRuntime:
    """
    Cria ToolRuntime com as três
    ferramentas MISP registradas.
    """

    client = create_misp_client()

    handlers = MISPToolHandlers(
        client=client
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    return ToolRuntime(
        registry=registry
    )


def test_misp_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Configuração válida pode ser
    criada por variáveis de ambiente.
    """

    monkeypatch.setenv(
        "MISP_URL",
        "https://misp.lab.local/",
    )

    monkeypatch.setenv(
        "MISP_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.setenv(
        "MISP_VERIFY_SSL",
        "true",
    )

    monkeypatch.setenv(
        "MISP_TIMEOUT_SECONDS",
        "20",
    )

    config = MISPConfig.from_env()

    assert (
        config.base_url
        == "https://misp.lab.local"
    )

    assert config.verify_ssl is True

    assert config.timeout_seconds == 20

    assert (
        config.api_key
        == FAKE_API_KEY
    )


def test_misp_config_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    MISP_URL é obrigatória.
    """

    monkeypatch.delenv(
        "MISP_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "MISP_API_KEY",
        FAKE_API_KEY,
    )

    with pytest.raises(ValueError):
        MISPConfig.from_env()


def test_misp_config_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    MISP_API_KEY é obrigatória.
    """

    monkeypatch.setenv(
        "MISP_URL",
        "https://misp.lab.local",
    )

    monkeypatch.delenv(
        "MISP_API_KEY",
        raising=False,
    )

    with pytest.raises(ValueError):
        MISPConfig.from_env()


def test_misp_config_does_not_expose_api_key() -> None:
    """
    repr e safe_summary não podem
    expor a API key.
    """

    config = create_misp_config()

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


def test_misp_config_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Timeout fora do limite permitido
    precisa ser recusado.
    """

    monkeypatch.setenv(
        "MISP_URL",
        "https://misp.lab.local",
    )

    monkeypatch.setenv(
        "MISP_API_KEY",
        FAKE_API_KEY,
    )

    monkeypatch.setenv(
        "MISP_TIMEOUT_SECONDS",
        "999",
    )

    with pytest.raises(ValueError):
        MISPConfig.from_env()


def test_misp_search_ioc_read_only() -> None:
    """
    Pesquisa de IOC precisa retornar
    resposta simulada do MISP.
    """

    client = create_misp_client()

    result = client.search_ioc(
        "185.10.20.30"
    )

    attributes = (
        result["response"]["Attribute"]
    )

    assert len(attributes) == 1

    assert (
        attributes[0]["value"]
        == "185.10.20.30"
    )


def test_misp_get_event() -> None:
    """
    Consulta de evento existente.
    """

    client = create_misp_client()

    result = client.get_event(
        "42"
    )

    assert (
        result["Event"]["id"]
        == "42"
    )


def test_misp_get_attribute() -> None:
    """
    Consulta de atributo existente.
    """

    client = create_misp_client()

    result = client.get_attribute(
        "123"
    )

    assert (
        result["Attribute"]["id"]
        == "123"
    )


def test_misp_blocks_write_endpoint() -> None:
    """
    Endpoint de escrita precisa ser
    bloqueado antes da chamada HTTP.
    """

    client = create_misp_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="POST",
            path="/events/add",
            payload={},
        )


def test_misp_blocks_delete_method() -> None:
    """
    DELETE não faz parte da allowlist.
    """

    client = create_misp_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="DELETE",
            path="/attributes/123",
        )


def test_misp_handles_http_error() -> None:
    """
    Erro HTTP do MISP precisa ser
    convertido para MISPHTTPError.
    """

    client = create_misp_client()

    with pytest.raises(
        MISPHTTPError
    ):
        client.get_event(
            "500"
        )


def test_misp_handles_invalid_json() -> None:
    """
    Conteúdo inválido precisa gerar
    MISPResponseError.
    """

    client = create_misp_client()

    with pytest.raises(
        MISPResponseError
    ):
        client.get_event(
            "bad-json"
        )


def test_misp_handlers_register_three_tools() -> None:
    """
    Os três handlers MISP precisam
    ser registrados no ToolRegistry.
    """

    handlers = MISPToolHandlers(
        client=create_misp_client()
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    assert (
        registry.registered_tool_ids()
        == (
            "misp.get_attribute",
            "misp.get_event",
            "misp.search_ioc",
        )
    )


def test_misp_runtime_search_ioc() -> None:
    """
    Testa o fluxo completo:

    ToolRequest
    -> autorização
    -> registry
    -> runtime
    -> handler
    -> cliente MISP simulado
    -> ToolResult.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-MISP-0001",
        execution_id="EXEC-MISP-0001",
        agent_id="AG-04",
        case_id="CASE-MISP-0001",
        correlation_id=(
            "CORR-MISP-0001"
        ),
        tool_id="misp.search_ioc",
        input_payload={
            "ioc": "185.10.20.30",
            "limit": 50,
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

    assert result.attempts == 1

    evidence = (
        result.evidence_payload.to_dict()
    )

    assert (
        evidence["source"]
        == "MISP"
    )

    assert (
        evidence["operation"]
        == "search_ioc"
    )

    assert (
        evidence["read_only"]
        is True
    )


def test_misp_runtime_get_event() -> None:
    """
    Testa get_event através do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-MISP-0002",
        execution_id="EXEC-MISP-0002",
        agent_id="AG-04",
        case_id="CASE-MISP-0001",
        correlation_id=(
            "CORR-MISP-0001"
        ),
        tool_id="misp.get_event",
        input_payload={
            "event_identifier": "42",
        },
        timeout_seconds=15,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert result.success is True

    output = (
        result.output_payload.to_dict()
    )

    assert (
        output["result"]["Event"]["id"]
        == "42"
    )


def test_misp_runtime_get_attribute() -> None:
    """
    Testa get_attribute através
    do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-MISP-0003",
        execution_id="EXEC-MISP-0003",
        agent_id="AG-04",
        case_id="CASE-MISP-0001",
        correlation_id=(
            "CORR-MISP-0001"
        ),
        tool_id="misp.get_attribute",
        input_payload={
            "attribute_identifier": "123",
        },
        timeout_seconds=15,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert result.success is True

    output = (
        result.output_payload.to_dict()
    )

    assert (
        output["result"]
        ["Attribute"]["id"]
        == "123"
    )


def test_misp_runtime_denies_unauthorized_agent() -> None:
    """
    AG-05 não possui permissão
    para misp.search_ioc.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-MISP-DENIED",
        execution_id=(
            "EXEC-MISP-DENIED"
        ),
        agent_id="AG-05",
        case_id="CASE-MISP-0001",
        correlation_id=(
            "CORR-MISP-0001"
        ),
        tool_id="misp.search_ioc",
        input_payload={
            "ioc": "185.10.20.30",
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