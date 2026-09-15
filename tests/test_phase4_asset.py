"""
Testes automatizados da integração Asset / CMDB
do Agentic SOC N1 Lab.

Fase 4.4 — Asset / CMDB read-only.

Estes testes validam:

- configuração segura por variáveis de ambiente;
- token não exposto;
- provedor Asset / CMDB;
- timeout;
- cliente HTTP estritamente read-only;
- consulta de ativo;
- consulta de contexto por IP;
- consulta de criticidade;
- consulta de estado EDR;
- bloqueio de métodos de escrita;
- bloqueio de rotas não autorizadas;
- bloqueio de URL externa;
- bloqueio de operação não autorizada;
- tratamento de HTTP 500;
- tratamento de JSON inválido;
- handlers oficiais;
- registro das quatro ferramentas Asset;
- integração completa com ToolRuntime;
- permissões específicas por agente;
- deny-by-default;
- alinhamento do AG-06 com os IDs oficiais.

Nenhum teste realiza conexão externa.
"""

import httpx
import pytest

from agents.asset import (
    AssetContextAgent,
)
from tools import (
    ToolExecutionStatus,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from tools.asset import (
    AssetClient,
    AssetConfig,
    AssetHTTPError,
    AssetResponseError,
    AssetToolHandlers,
)


FAKE_TOKEN = "TOKEN-FICTICIO-NAO-REAL"


def create_asset_config() -> AssetConfig:
    """
    Cria configuração Asset / CMDB fictícia
    para testes sem acesso real à rede.
    """

    return AssetConfig(
        base_url="https://asset.lab.local",
        api_token=FAKE_TOKEN,
        provider="GENERIC",
        verify_ssl=True,
        timeout_seconds=15,
    )


def fake_asset_server(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula um pequeno serviço Asset / CMDB.

    Nenhuma conexão externa é realizada.
    """

    authorization = request.headers.get(
        "Authorization"
    )

    if authorization != f"Bearer {FAKE_TOKEN}":
        return httpx.Response(
            401,
            json={
                "error": "Unauthorized",
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/assets/ASSET-0001"
    ):
        return httpx.Response(
            200,
            json={
                "asset_id": "ASSET-0001",
                "hostname": "srv-finance-01",
                "asset_type": "server",
                "operating_system": "Windows Server",
                "managed": True,
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/assets/by-ip/10.20.30.15"
    ):
        return httpx.Response(
            200,
            json={
                "asset_id": "ASSET-0001",
                "hostname": "srv-finance-01",
                "ip_address": "10.20.30.15",
                "internet_exposed": False,
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/assets/ASSET-0001/criticality"
    ):
        return httpx.Response(
            200,
            json={
                "asset_id": "ASSET-0001",
                "criticality": "CRITICAL",
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/assets/ASSET-0001/edr"
    ):
        return httpx.Response(
            200,
            json={
                "asset_id": "ASSET-0001",
                "edr_installed": True,
            },
        )

    return httpx.Response(
        404,
        json={
            "error": "Not Found",
        },
    )


def create_asset_client() -> AssetClient:
    """
    Cria AssetClient com MockTransport.
    """

    return AssetClient(
        create_asset_config(),
        transport=httpx.MockTransport(
            fake_asset_server
        ),
    )


def create_runtime() -> tuple[
    ToolRuntime,
    AssetClient,
    ToolRegistry,
]:
    """
    Cria ToolRuntime com as quatro
    ferramentas Asset registradas.
    """

    client = create_asset_client()

    registry = ToolRegistry()

    handlers = AssetToolHandlers(
        client
    )

    handlers.register(
        registry
    )

    runtime = ToolRuntime(
        registry
    )

    return (
        runtime,
        client,
        registry,
    )


def test_asset_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    AssetConfig deve carregar
    configuração válida do ambiente.
    """

    monkeypatch.setenv(
        "ASSET_URL",
        "https://asset.lab.local",
    )

    monkeypatch.setenv(
        "ASSET_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.setenv(
        "ASSET_PROVIDER",
        "CMDB-LAB",
    )

    monkeypatch.setenv(
        "ASSET_VERIFY_SSL",
        "true",
    )

    monkeypatch.setenv(
        "ASSET_TIMEOUT_SECONDS",
        "15",
    )

    config = AssetConfig.from_env()

    assert (
        config.base_url
        == "https://asset.lab.local"
    )

    assert (
        config.provider
        == "CMDB-LAB"
    )

    assert config.verify_ssl is True

    assert config.timeout_seconds == 15

    assert config.allowed_operations == (
        "get_asset",
        "get_ip_context",
        "get_criticality",
        "get_edr_status",
    )


def test_asset_config_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ASSET_URL é obrigatória.
    """

    monkeypatch.delenv(
        "ASSET_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "ASSET_API_TOKEN",
        FAKE_TOKEN,
    )

    with pytest.raises(
        ValueError
    ):
        AssetConfig.from_env()


def test_asset_config_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    ASSET_API_TOKEN é obrigatório.
    """

    monkeypatch.setenv(
        "ASSET_URL",
        "https://asset.lab.local",
    )

    monkeypatch.delenv(
        "ASSET_API_TOKEN",
        raising=False,
    )

    with pytest.raises(
        ValueError
    ):
        AssetConfig.from_env()


def test_asset_config_uses_default_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    O provedor padrão deve ser GENERIC.
    """

    monkeypatch.setenv(
        "ASSET_URL",
        "https://asset.lab.local",
    )

    monkeypatch.setenv(
        "ASSET_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.delenv(
        "ASSET_PROVIDER",
        raising=False,
    )

    config = AssetConfig.from_env()

    assert config.provider == "GENERIC"


def test_asset_config_does_not_expose_token() -> None:
    """
    O token não deve aparecer no repr
    nem no safe_summary.
    """

    config = create_asset_config()

    assert FAKE_TOKEN not in repr(
        config
    )

    assert FAKE_TOKEN not in str(
        config.safe_summary()
    )

    summary = config.safe_summary()

    assert (
        summary["access_mode"]
        == "READ_ONLY"
    )

    assert (
        summary["api_token_configured"]
        is True
    )


def test_asset_config_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Timeout fora do limite deve ser rejeitado.
    """

    monkeypatch.setenv(
        "ASSET_URL",
        "https://asset.lab.local",
    )

    monkeypatch.setenv(
        "ASSET_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.setenv(
        "ASSET_TIMEOUT_SECONDS",
        "0",
    )

    with pytest.raises(
        ValueError
    ):
        AssetConfig.from_env()


def test_asset_client_get_asset() -> None:
    """
    Consulta básica de ativo.
    """

    client = create_asset_client()

    try:
        result = client.get_asset(
            "ASSET-0001"
        )

        assert (
            result["asset_id"]
            == "ASSET-0001"
        )

        assert (
            result["hostname"]
            == "srv-finance-01"
        )

        assert result["managed"] is True

    finally:
        client.close()


def test_asset_client_get_ip_context() -> None:
    """
    Consulta contexto de ativo por IP.
    """

    client = create_asset_client()

    try:
        result = client.get_ip_context(
            "10.20.30.15"
        )

        assert (
            result["asset_id"]
            == "ASSET-0001"
        )

        assert (
            result["ip_address"]
            == "10.20.30.15"
        )

        assert (
            result["internet_exposed"]
            is False
        )

    finally:
        client.close()


def test_asset_client_get_criticality() -> None:
    """
    Consulta criticidade do ativo.
    """

    client = create_asset_client()

    try:
        result = client.get_criticality(
            "ASSET-0001"
        )

        assert (
            result["criticality"]
            == "CRITICAL"
        )

    finally:
        client.close()


def test_asset_client_get_edr_status() -> None:
    """
    Consulta estado registrado do EDR.
    """

    client = create_asset_client()

    try:
        result = client.get_edr_status(
            "ASSET-0001"
        )

        assert (
            result["edr_installed"]
            is True
        )

    finally:
        client.close()


def test_asset_client_blocks_post() -> None:
    """
    POST deve ser bloqueado.
    """

    client = create_asset_client()

    try:
        with pytest.raises(
            PermissionError
        ):
            client._validate_request_shape(
                method="POST",
                path="/assets/ASSET-0001",
                operation="get_asset",
                identifier="ASSET-0001",
            )

    finally:
        client.close()


def test_asset_client_blocks_delete() -> None:
    """
    DELETE deve ser bloqueado.
    """

    client = create_asset_client()

    try:
        with pytest.raises(
            PermissionError
        ):
            client._validate_request_shape(
                method="DELETE",
                path="/assets/ASSET-0001",
                operation="get_asset",
                identifier="ASSET-0001",
            )

    finally:
        client.close()


def test_asset_client_blocks_unauthorized_route() -> None:
    """
    Rota não autorizada deve falhar.
    """

    client = create_asset_client()

    try:
        with pytest.raises(
            PermissionError
        ):
            client._validate_request_shape(
                method="GET",
                path=(
                    "/assets/ASSET-0001/delete"
                ),
                operation="get_asset",
                identifier="ASSET-0001",
            )

    finally:
        client.close()


def test_asset_client_blocks_external_url() -> None:
    """
    URL absoluta externa deve ser bloqueada.
    """

    client = create_asset_client()

    try:
        with pytest.raises(
            PermissionError
        ):
            client._validate_request_shape(
                method="GET",
                path=(
                    "https://evil.example/"
                    "assets/ASSET-0001"
                ),
                operation="get_asset",
                identifier="ASSET-0001",
            )

    finally:
        client.close()


def test_asset_client_blocks_unauthorized_operation() -> None:
    """
    Operação fora da allowlist deve falhar.
    """

    client = create_asset_client()

    try:
        with pytest.raises(
            PermissionError
        ):
            client._validate_request_shape(
                method="GET",
                path="/assets/ASSET-0001",
                operation="delete_asset",
                identifier="ASSET-0001",
            )

    finally:
        client.close()


def test_asset_client_handles_http_error() -> None:
    """
    HTTP 500 deve gerar AssetHTTPError.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            500,
            json={
                "error": "Internal Error",
            },
        )

    client = AssetClient(
        create_asset_config(),
        transport=httpx.MockTransport(
            handler
        ),
    )

    try:
        with pytest.raises(
            AssetHTTPError
        ):
            client.get_asset(
                "ASSET-0001"
            )

    finally:
        client.close()


def test_asset_client_handles_invalid_json() -> None:
    """
    Conteúdo não JSON deve gerar
    AssetResponseError.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"nao-e-json",
            headers={
                "Content-Type": "text/plain",
            },
        )

    client = AssetClient(
        create_asset_config(),
        transport=httpx.MockTransport(
            handler
        ),
    )

    try:
        with pytest.raises(
            AssetResponseError
        ):
            client.get_asset(
                "ASSET-0001"
            )

    finally:
        client.close()


def test_asset_handlers_register_four_tools() -> None:
    """
    Os quatro handlers oficiais devem
    ser registrados no ToolRegistry.
    """

    client = create_asset_client()

    try:
        registry = ToolRegistry()

        handlers = AssetToolHandlers(
            client
        )

        handlers.register(
            registry
        )

        assert (
            registry.registered_tool_ids()
            == (
                "asset.get_asset",
                "asset.get_criticality",
                "asset.get_edr_status",
                "asset.get_ip_context",
            )
        )

    finally:
        client.close()


def test_runtime_executes_get_asset_for_ag06() -> None:
    """
    AG-06 deve poder executar
    asset.get_asset.
    """

    runtime, client, _ = (
        create_runtime()
    )

    try:
        request = ToolRequest(
            request_id="REQ-ASSET-0001",
            execution_id="EXEC-ASSET-0001",
            agent_id="AG-06",
            case_id="CASE-ASSET-0001",
            correlation_id="CORR-ASSET-0001",
            tool_id="asset.get_asset",
            input_payload={
                "asset_id": "ASSET-0001",
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

        output = (
            result.output_payload.to_dict()
        )

        assert (
            output["result"]["asset_id"]
            == "ASSET-0001"
        )

    finally:
        client.close()


def test_runtime_executes_ip_context_for_ag06() -> None:
    """
    AG-06 deve poder executar
    asset.get_ip_context.
    """

    runtime, client, _ = (
        create_runtime()
    )

    try:
        request = ToolRequest(
            request_id="REQ-ASSET-0002",
            execution_id="EXEC-ASSET-0002",
            agent_id="AG-06",
            case_id="CASE-ASSET-0001",
            correlation_id="CORR-ASSET-0001",
            tool_id="asset.get_ip_context",
            input_payload={
                "ip_address": "10.20.30.15",
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
            output["query"]["ip_address"]
            == "10.20.30.15"
        )

    finally:
        client.close()


def test_runtime_allows_ag03_get_criticality() -> None:
    """
    O catálogo oficial permite ao AG-03
    executar asset.get_criticality.
    """

    runtime, client, _ = (
        create_runtime()
    )

    try:
        request = ToolRequest(
            request_id="REQ-ASSET-0003",
            execution_id="EXEC-ASSET-0003",
            agent_id="AG-03",
            case_id="CASE-ASSET-0001",
            correlation_id="CORR-ASSET-0001",
            tool_id="asset.get_criticality",
            input_payload={
                "asset_id": "ASSET-0001",
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
            output["result"]["criticality"]
            == "CRITICAL"
        )

    finally:
        client.close()


def test_runtime_executes_edr_status_for_ag06() -> None:
    """
    AG-06 deve poder executar
    asset.get_edr_status.
    """

    runtime, client, _ = (
        create_runtime()
    )

    try:
        request = ToolRequest(
            request_id="REQ-ASSET-0004",
            execution_id="EXEC-ASSET-0004",
            agent_id="AG-06",
            case_id="CASE-ASSET-0001",
            correlation_id="CORR-ASSET-0001",
            tool_id="asset.get_edr_status",
            input_payload={
                "asset_id": "ASSET-0001",
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

        evidence = (
            result.evidence_payload.to_dict()
        )

        assert (
            evidence["operation"]
            == "get_edr_status"
        )

        assert (
            evidence["read_only"]
            is True
        )

    finally:
        client.close()


def test_runtime_denies_ag03_get_asset() -> None:
    """
    AG-03 não possui autorização para
    asset.get_asset.
    """

    runtime, client, _ = (
        create_runtime()
    )

    try:
        request = ToolRequest(
            request_id=(
                "REQ-ASSET-DENIED"
            ),
            execution_id=(
                "EXEC-ASSET-DENIED"
            ),
            agent_id="AG-03",
            case_id="CASE-ASSET-0001",
            correlation_id="CORR-ASSET-0001",
            tool_id="asset.get_asset",
            input_payload={
                "asset_id": "ASSET-0001",
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

    finally:
        client.close()


def test_asset_agent_uses_official_tool_ids() -> None:
    """
    AG-06 deve utilizar somente os IDs
    oficiais atuais da camada Tools.
    """

    agent = AssetContextAgent()

    assert agent.can_use_tool(
        "asset.get_asset"
    ) is True

    assert agent.can_use_tool(
        "asset.get_ip_context"
    ) is True

    assert agent.can_use_tool(
        "asset.get_criticality"
    ) is True

    assert agent.can_use_tool(
        "asset.get_edr_status"
    ) is True

    assert agent.can_use_tool(
        "lookup_asset"
    ) is False

    assert agent.can_use_tool(
        "lookup_asset_criticality"
    ) is False

    assert agent.can_use_tool(
        "lookup_asset_exposure"
    ) is False

    assert agent.can_use_tool(
        "lookup_edr_status"
    ) is False

    assert agent.can_use_tool(
        "lookup_asset_inventory"
    ) is False