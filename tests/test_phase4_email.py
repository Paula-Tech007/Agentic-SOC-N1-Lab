"""
Testes formais da Fase 4.5 do Agentic SOC N1 Lab.

Fase 4.5 — Email / Phishing Metadata Read-Only.

Estes testes validam:

- configuração por variáveis de ambiente;
- proteção do token;
- validação de timeout;
- operações oficiais de Email / Phishing;
- rotas HTTP autorizadas;
- bloqueio de métodos de escrita;
- bloqueio de rotas não autorizadas;
- bloqueio de URLs externas;
- tratamento de erro HTTP;
- tratamento de JSON inválido;
- registro dos handlers;
- integração com ToolRuntime;
- autorização por agente;
- alinhamento do AG-07 com os IDs oficiais;
- remoção dos aliases antigos do AG-07.
"""

from __future__ import annotations

import httpx
import pytest

from agents.phishing import (
    PhishingAnalystAgent,
)
from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
)
from tools.email import (
    DEFAULT_EMAIL_PROVIDER,
    DEFAULT_EMAIL_TIMEOUT_SECONDS,
    EmailClient,
    EmailConfig,
    EmailHTTPError,
    EmailResponseError,
    EmailToolHandlers,
)
from tools.registry import ToolRegistry
from tools.runtime import ToolRuntime


def create_email_config(
    *,
    provider: str = "MAIL-LAB",
) -> EmailConfig:
    """
    Cria configuração controlada para testes.
    """

    return EmailConfig(
        base_url=(
            "https://email-lab.example"
        ),
        api_token="token-email-lab",
        provider=provider,
        verify_ssl=True,
        timeout_seconds=15,
    )


def create_tool_request(
    *,
    tool_id: str,
    agent_id: str = "AG-07",
    request_id: str = "REQ-EMAIL-0001",
) -> ToolRequest:
    """
    Cria ToolRequest controlada.
    """

    return ToolRequest(
        request_id=request_id,
        execution_id="EXEC-EMAIL-0001",
        agent_id=agent_id,
        case_id="CASE-EMAIL-0001",
        correlation_id=(
            "CORR-EMAIL-0001"
        ),
        tool_id=tool_id,
        input_payload={
            "message_id": "MSG-0001",
        },
        timeout_seconds=15,
        max_retries=1,
    )


def build_runtime(
    transport: httpx.BaseTransport,
) -> tuple[
    ToolRuntime,
    ToolRegistry,
    EmailClient,
]:
    """
    Monta integração completa de Email
    com transporte controlado.
    """

    client = EmailClient(
        create_email_config(),
        transport=transport,
    )

    handlers = EmailToolHandlers(
        client
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    runtime = ToolRuntime(
        registry
    )

    return (
        runtime,
        registry,
        client,
    )


def test_email_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    EmailConfig deve carregar todas
    as configurações oficiais do ambiente.
    """

    monkeypatch.setenv(
        "EMAIL_URL",
        "https://email.example",
    )

    monkeypatch.setenv(
        "EMAIL_API_TOKEN",
        "secret-token",
    )

    monkeypatch.setenv(
        "EMAIL_PROVIDER",
        "mail-provider",
    )

    monkeypatch.setenv(
        "EMAIL_VERIFY_SSL",
        "true",
    )

    monkeypatch.setenv(
        "EMAIL_TIMEOUT_SECONDS",
        "20",
    )

    config = EmailConfig.from_env()

    assert (
        config.base_url
        == "https://email.example"
    )

    assert (
        config.provider
        == "MAIL-PROVIDER"
    )

    assert config.verify_ssl is True

    assert (
        config.timeout_seconds
        == 20
    )

    assert config.api_token == (
        "secret-token"
    )


def test_email_config_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    EMAIL_URL é obrigatória.
    """

    monkeypatch.delenv(
        "EMAIL_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "EMAIL_API_TOKEN",
        "secret-token",
    )

    with pytest.raises(
        ValueError,
        match="EMAIL_URL",
    ):
        EmailConfig.from_env()


def test_email_config_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    EMAIL_API_TOKEN é obrigatório.
    """

    monkeypatch.setenv(
        "EMAIL_URL",
        "https://email.example",
    )

    monkeypatch.delenv(
        "EMAIL_API_TOKEN",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="EMAIL_API_TOKEN",
    ):
        EmailConfig.from_env()


def test_email_config_uses_default_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Provider padrão deve ser GENERIC.
    """

    monkeypatch.setenv(
        "EMAIL_URL",
        "https://email.example",
    )

    monkeypatch.setenv(
        "EMAIL_API_TOKEN",
        "secret-token",
    )

    monkeypatch.delenv(
        "EMAIL_PROVIDER",
        raising=False,
    )

    config = EmailConfig.from_env()

    assert (
        config.provider
        == DEFAULT_EMAIL_PROVIDER
    )

    assert (
        config.provider
        == "GENERIC"
    )


def test_email_config_does_not_expose_token() -> None:
    """
    Token não pode aparecer em repr
    nem no safe_summary.
    """

    secret = "email-super-secret"

    config = EmailConfig(
        base_url=(
            "https://email.example"
        ),
        api_token=secret,
    )

    assert secret not in repr(config)

    assert (
        secret
        not in str(
            config.safe_summary()
        )
    )

    assert (
        config.safe_summary()[
            "api_token_configured"
        ]
        is True
    )


def test_email_config_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Timeout fora do limite deve falhar.
    """

    monkeypatch.setenv(
        "EMAIL_URL",
        "https://email.example",
    )

    monkeypatch.setenv(
        "EMAIL_API_TOKEN",
        "secret-token",
    )

    monkeypatch.setenv(
        "EMAIL_TIMEOUT_SECONDS",
        "999",
    )

    with pytest.raises(
        ValueError,
        match="EMAIL_TIMEOUT_SECONDS",
    ):
        EmailConfig.from_env()


def test_email_client_get_message_metadata() -> None:
    """
    Cliente deve consultar somente
    metadados da mensagem.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"

        assert (
            request.url.path
            == "/messages/MSG-0001/metadata"
        )

        return httpx.Response(
            200,
            json={
                "message_id": "MSG-0001",
                "sender": (
                    "sender@example.invalid"
                ),
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        result = (
            client.get_message_metadata(
                "MSG-0001"
            )
        )

    assert (
        result["message_id"]
        == "MSG-0001"
    )


def test_email_client_get_headers() -> None:
    """
    Cliente deve consultar
    cabeçalhos técnicos.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"

        assert (
            request.url.path
            == "/messages/MSG-0001/headers"
        )

        return httpx.Response(
            200,
            json={
                "from": (
                    "sender@example.invalid"
                ),
                "subject": "Teste",
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        result = client.get_headers(
            "MSG-0001"
        )

    assert (
        result["subject"]
        == "Teste"
    )


def test_email_client_get_authentication_results() -> None:
    """
    Cliente deve consultar
    SPF, DKIM e DMARC.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"

        assert (
            request.url.path
            == (
                "/messages/MSG-0001/"
                "authentication-results"
            )
        )

        return httpx.Response(
            200,
            json={
                "spf": "pass",
                "dkim": "pass",
                "dmarc": "pass",
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        result = (
            client
            .get_authentication_results(
                "MSG-0001"
            )
        )

    assert result["spf"] == "pass"
    assert result["dkim"] == "pass"
    assert result["dmarc"] == "pass"


def test_email_client_get_attachment_metadata() -> None:
    """
    Cliente deve consultar somente
    metadados de anexos.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"

        assert (
            request.url.path
            == (
                "/messages/MSG-0001/"
                "attachments/metadata"
            )
        )

        return httpx.Response(
            200,
            json={
                "attachments": [
                    {
                        "name": (
                            "documento.pdf"
                        ),
                        "size": 1024,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        result = (
            client
            .get_attachment_metadata(
                "MSG-0001"
            )
        )

    assert (
        result["attachments"][0][
            "name"
        ]
        == "documento.pdf"
    )


def test_email_client_blocks_post() -> None:
    """
    POST deve ser bloqueado.
    """

    config = create_email_config()

    with EmailClient(
        config
    ) as client:
        path = (
            "/messages/"
            "MSG-0001"
            "/metadata"
        )

        with pytest.raises(
            PermissionError,
            match="somente HTTP GET",
        ):
            client._validate_request_shape(
                method="POST",
                operation=(
                    client
                    .GET_MESSAGE_METADATA
                ),
                path=path,
                expected_path=path,
            )


def test_email_client_blocks_delete() -> None:
    """
    DELETE deve ser bloqueado.
    """

    config = create_email_config()

    with EmailClient(
        config
    ) as client:
        path = (
            "/messages/"
            "MSG-0001"
            "/metadata"
        )

        with pytest.raises(
            PermissionError,
            match="somente HTTP GET",
        ):
            client._validate_request_shape(
                method="DELETE",
                operation=(
                    client
                    .GET_MESSAGE_METADATA
                ),
                path=path,
                expected_path=path,
            )


def test_email_client_blocks_unauthorized_route() -> None:
    """
    Rota diferente da autorizada
    deve ser bloqueada.
    """

    config = create_email_config()

    with EmailClient(
        config
    ) as client:
        expected_path = (
            "/messages/"
            "MSG-0001"
            "/metadata"
        )

        with pytest.raises(
            PermissionError,
            match="Rota não autorizada",
        ):
            client._validate_request_shape(
                method="GET",
                operation=(
                    client
                    .GET_MESSAGE_METADATA
                ),
                path=(
                    "/messages/"
                    "MSG-0001"
                    "/download"
                ),
                expected_path=(
                    expected_path
                ),
            )


def test_email_client_blocks_external_url() -> None:
    """
    URL externa deve ser bloqueada.
    """

    config = create_email_config()

    with EmailClient(
        config
    ) as client:
        with pytest.raises(
            PermissionError,
            match="URL externa",
        ):
            client._normalize_path(
                "https://external.example"
            )


def test_email_client_blocks_unauthorized_operation() -> None:
    """
    Operação fora do catálogo
    deve ser bloqueada.
    """

    config = create_email_config()

    with EmailClient(
        config
    ) as client:
        path = (
            "/messages/"
            "MSG-0001"
            "/metadata"
        )

        with pytest.raises(
            PermissionError,
            match="Operação não autorizada",
        ):
            client._validate_request_shape(
                method="GET",
                operation="open_url",
                path=path,
                expected_path=path,
            )


def test_email_client_handles_http_error() -> None:
    """
    Status HTTP de erro deve gerar
    EmailHTTPError.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            500,
            json={
                "error": (
                    "internal_error"
                )
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        with pytest.raises(
            EmailHTTPError,
            match="status HTTP 500",
        ):
            client.get_message_metadata(
                "MSG-0001"
            )


def test_email_client_handles_invalid_json() -> None:
    """
    Conteúdo inválido deve gerar
    EmailResponseError.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-json",
            headers={
                "Content-Type": (
                    "application/json"
                ),
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with EmailClient(
        create_email_config(),
        transport=transport,
    ) as client:
        with pytest.raises(
            EmailResponseError,
            match="JSON válido",
        ):
            client.get_message_metadata(
                "MSG-0001"
            )


def test_email_handlers_register_four_tools() -> None:
    """
    Handlers devem registrar exatamente
    as quatro tools oficiais de e-mail.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={},
        )

    transport = httpx.MockTransport(
        handler
    )

    client = EmailClient(
        create_email_config(),
        transport=transport,
    )

    registry = ToolRegistry()

    EmailToolHandlers(
        client
    ).register(
        registry
    )

    assert (
        registry.registered_tool_ids()
        == (
            "email.get_attachment_metadata",
            "email.get_authentication_results",
            "email.get_headers",
            "email.get_message_metadata",
        )
    )

    client.close()


def test_email_runtime_get_message_metadata() -> None:
    """
    AG-07 deve executar
    email.get_message_metadata.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message_id": "MSG-0001",
                "sender": (
                    "sender@example.invalid"
                ),
            },
        )

    runtime, _, client = build_runtime(
        httpx.MockTransport(
            handler
        )
    )

    result = runtime.execute(
        create_tool_request(
            tool_id=(
                "email.get_message_metadata"
            ),
        )
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

    assert evidence["source"] == "EMAIL"
    assert evidence["read_only"] is True
    assert evidence["opens_urls"] is False

    client.close()


def test_email_runtime_get_headers() -> None:
    """
    AG-07 deve executar
    email.get_headers.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "subject": "Teste",
            },
        )

    runtime, _, client = build_runtime(
        httpx.MockTransport(
            handler
        )
    )

    result = runtime.execute(
        create_tool_request(
            tool_id="email.get_headers",
        )
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True
    assert result.attempts == 1

    client.close()


def test_email_runtime_get_authentication_results() -> None:
    """
    AG-07 deve executar consulta
    de autenticação da mensagem.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "spf": "pass",
                "dkim": "pass",
                "dmarc": "pass",
            },
        )

    runtime, _, client = build_runtime(
        httpx.MockTransport(
            handler
        )
    )

    result = runtime.execute(
        create_tool_request(
            tool_id=(
                "email."
                "get_authentication_results"
            ),
        )
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True
    assert result.attempts == 1

    client.close()


def test_email_runtime_get_attachment_metadata() -> None:
    """
    AG-07 deve consultar somente
    metadados de anexos.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "attachments": [
                    {
                        "name": (
                            "documento.pdf"
                        ),
                    }
                ]
            },
        )

    runtime, _, client = build_runtime(
        httpx.MockTransport(
            handler
        )
    )

    result = runtime.execute(
        create_tool_request(
            tool_id=(
                "email."
                "get_attachment_metadata"
            ),
        )
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
        evidence[
            "downloads_attachments"
        ]
        is False
    )

    assert (
        evidence[
            "executes_attachments"
        ]
        is False
    )

    client.close()


def test_email_runtime_denies_ag03() -> None:
    """
    AG-03 não possui autorização para
    email.get_message_metadata.
    """

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={},
        )

    runtime, _, client = build_runtime(
        httpx.MockTransport(
            handler
        )
    )

    result = runtime.execute(
        create_tool_request(
            tool_id=(
                "email.get_message_metadata"
            ),
            agent_id="AG-03",
            request_id=(
                "REQ-EMAIL-DENIED"
            ),
        )
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

    client.close()


def test_ag07_uses_only_official_email_tools() -> None:
    """
    AG-07 deve utilizar exclusivamente
    os quatro IDs oficiais da Fase 4.5.
    """

    agent = PhishingAnalystAgent()

    expected = (
        "email.get_message_metadata",
        "email.get_headers",
        "email.get_authentication_results",
        "email.get_attachment_metadata",
    )

    assert (
        agent.allowed_tools
        == expected
    )

    for tool_id in expected:
        assert (
            agent.can_use_tool(
                tool_id
            )
            is True
        )

    old_aliases = (
        "read_case_context",
        "read_email_metadata",
        "read_email_authentication",
        "read_url_reputation",
        "read_attachment_metadata",
        "read_hash_reputation",
        "read_evidence",
    )

    for tool_id in old_aliases:
        assert (
            agent.can_use_tool(
                tool_id
            )
            is False
        )

    assert (
        agent.can_use_tool(
            "email.open_url"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "email.execute_attachment"
        )
        is False
    )

    assert (
        agent.can_use_tool(
            "email.download_attachment"
        )
        is False
    )