"""
Testes automatizados da integração Identity / IAM
do Agentic SOC N1 Lab.

Fase 4.3 — Identity / IAM read-only.

Estes testes validam:

- configuração segura por variáveis de ambiente;
- token não exposto;
- provedor IAM;
- timeout;
- cliente HTTP estritamente read-only;
- consulta de usuário;
- estado da conta;
- estado de MFA;
- grupos e privilégios;
- bloqueio de métodos de escrita;
- bloqueio de rotas não autorizadas;
- bloqueio de URL externa;
- bloqueio de operação não autorizada;
- tratamento de HTTP 500;
- tratamento de JSON inválido;
- handlers oficiais;
- registro das quatro ferramentas IAM;
- integração completa com ToolRuntime;
- permissões específicas por agente;
- deny-by-default;
- alinhamento do AG-05 com os IDs oficiais.

Nenhum teste realiza conexão externa.
"""

import httpx
import pytest

from agents.identity import (
    IdentityAnalystAgent,
)
from tools import (
    ToolExecutionStatus,
    ToolRegistry,
    ToolRequest,
    ToolRuntime,
)
from tools.identity import (
    IdentityClient,
    IdentityConfig,
    IdentityHTTPError,
    IdentityResponseError,
    IdentityToolHandlers,
)


FAKE_TOKEN = "TOKEN-FICTICIO-NAO-REAL"


def create_identity_config() -> IdentityConfig:
    """
    Cria configuração IAM fictícia
    para testes sem acesso real à rede.
    """

    return IdentityConfig(
        base_url="https://iam.lab.local",
        api_token=FAKE_TOKEN,
        provider="GENERIC",
        verify_ssl=True,
        timeout_seconds=15,
    )


def fake_iam_server(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula um pequeno serviço IAM.

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
        == "/users/lab.user"
    ):
        return httpx.Response(
            200,
            json={
                "username": "lab.user",
                "email": (
                    "lab.user@example.local"
                ),
                "display_name": "Lab User",
                "department": "Security",
                "role": "Analyst",
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/users/lab.user/status"
    ):
        return httpx.Response(
            200,
            json={
                "username": "lab.user",
                "account_exists": True,
                "account_enabled": True,
                "last_login": (
                    "2026-09-15T10:30:00Z"
                ),
                "failed_login_count": 3,
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/users/lab.user/mfa"
    ):
        return httpx.Response(
            200,
            json={
                "username": "lab.user",
                "mfa_enabled": True,
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/users/lab.user/groups"
    ):
        return httpx.Response(
            200,
            json={
                "username": "lab.user",
                "groups": [
                    "SOC-Analysts",
                    "VPN-Users",
                ],
                "privileged": False,
            },
        )

    if (
        request.method == "GET"
        and request.url.path
        == "/users/http500"
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
        == "/users/badjson"
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


def create_identity_client() -> IdentityClient:
    """
    Cria cliente IAM utilizando
    httpx.MockTransport.
    """

    return IdentityClient(
        config=create_identity_config(),
        transport=httpx.MockTransport(
            fake_iam_server
        ),
    )


def create_runtime() -> ToolRuntime:
    """
    Cria ToolRuntime com as quatro
    ferramentas IAM registradas.
    """

    client = create_identity_client()

    handlers = IdentityToolHandlers(
        client=client
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    return ToolRuntime(
        registry=registry
    )


def test_identity_config_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Configuração válida pode ser criada
    por variáveis de ambiente.
    """

    monkeypatch.setenv(
        "IAM_URL",
        "https://iam.lab.local/",
    )

    monkeypatch.setenv(
        "IAM_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.setenv(
        "IAM_PROVIDER",
        "generic",
    )

    monkeypatch.setenv(
        "IAM_VERIFY_SSL",
        "true",
    )

    monkeypatch.setenv(
        "IAM_TIMEOUT_SECONDS",
        "15",
    )

    config = IdentityConfig.from_env()

    assert (
        config.base_url
        == "https://iam.lab.local"
    )

    assert config.provider == "GENERIC"

    assert config.verify_ssl is True

    assert config.timeout_seconds == 15

    assert config.api_token == FAKE_TOKEN


def test_identity_config_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    IAM_URL é obrigatória.
    """

    monkeypatch.delenv(
        "IAM_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "IAM_API_TOKEN",
        FAKE_TOKEN,
    )

    with pytest.raises(ValueError):
        IdentityConfig.from_env()


def test_identity_config_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    IAM_API_TOKEN é obrigatório.
    """

    monkeypatch.setenv(
        "IAM_URL",
        "https://iam.lab.local",
    )

    monkeypatch.delenv(
        "IAM_API_TOKEN",
        raising=False,
    )

    with pytest.raises(ValueError):
        IdentityConfig.from_env()


def test_identity_config_default_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Provedor padrão precisa ser GENERIC.
    """

    monkeypatch.setenv(
        "IAM_URL",
        "https://iam.lab.local",
    )

    monkeypatch.setenv(
        "IAM_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.delenv(
        "IAM_PROVIDER",
        raising=False,
    )

    config = IdentityConfig.from_env()

    assert config.provider == "GENERIC"


def test_identity_config_does_not_expose_token() -> None:
    """
    repr e safe_summary não podem
    expor o token.
    """

    config = create_identity_config()

    representation = repr(
        config
    )

    summary = config.safe_summary()

    assert (
        FAKE_TOKEN
        not in representation
    )

    assert (
        FAKE_TOKEN
        not in str(summary)
    )

    assert (
        summary["api_token_configured"]
        is True
    )


def test_identity_config_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Timeout fora do limite permitido
    precisa ser recusado.
    """

    monkeypatch.setenv(
        "IAM_URL",
        "https://iam.lab.local",
    )

    monkeypatch.setenv(
        "IAM_API_TOKEN",
        FAKE_TOKEN,
    )

    monkeypatch.setenv(
        "IAM_TIMEOUT_SECONDS",
        "999",
    )

    with pytest.raises(ValueError):
        IdentityConfig.from_env()


def test_identity_get_user_read_only() -> None:
    """
    Consulta básica de usuário.
    """

    client = create_identity_client()

    result = client.get_user(
        "lab.user"
    )

    assert (
        result["username"]
        == "lab.user"
    )

    assert (
        result["department"]
        == "Security"
    )

    client.close()


def test_identity_get_account_status_read_only() -> None:
    """
    Consulta do estado da conta.
    """

    client = create_identity_client()

    result = client.get_account_status(
        "lab.user"
    )

    assert (
        result["account_exists"]
        is True
    )

    assert (
        result["account_enabled"]
        is True
    )

    assert (
        result["failed_login_count"]
        == 3
    )

    client.close()


def test_identity_get_mfa_status_read_only() -> None:
    """
    Consulta do estado de MFA.
    """

    client = create_identity_client()

    result = client.get_mfa_status(
        "lab.user"
    )

    assert (
        result["mfa_enabled"]
        is True
    )

    client.close()


def test_identity_get_group_membership_read_only() -> None:
    """
    Consulta de grupos e privilégios.
    """

    client = create_identity_client()

    result = (
        client.get_group_membership(
            "lab.user"
        )
    )

    assert (
        result["privileged"]
        is False
    )

    assert (
        "SOC-Analysts"
        in result["groups"]
    )

    client.close()


def test_identity_blocks_post_method() -> None:
    """
    POST não faz parte da allowlist.
    """

    client = create_identity_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="POST",
            path="/users/lab.user",
            operation="get_user",
            username="lab.user",
        )

    client.close()


def test_identity_blocks_delete_method() -> None:
    """
    DELETE não faz parte da allowlist.
    """

    client = create_identity_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="DELETE",
            path="/users/lab.user",
            operation="get_user",
            username="lab.user",
        )

    client.close()


def test_identity_blocks_unauthorized_route() -> None:
    """
    Rota diferente da rota oficial
    precisa ser bloqueada.
    """

    client = create_identity_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="GET",
            path=(
                "/users/lab.user/disable"
            ),
            operation="get_user",
            username="lab.user",
        )

    client.close()


def test_identity_blocks_external_url() -> None:
    """
    URL absoluta interna não pode
    substituir a base configurada.
    """

    client = create_identity_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="GET",
            path=(
                "https://externo.example/"
                "users/lab.user"
            ),
            operation="get_user",
            username="lab.user",
        )

    client.close()


def test_identity_blocks_unauthorized_operation() -> None:
    """
    Operação inexistente na allowlist
    precisa ser recusada.
    """

    client = create_identity_client()

    with pytest.raises(PermissionError):
        client._request_json(
            method="GET",
            path="/users/lab.user",
            operation="reset_password",
            username="lab.user",
        )

    client.close()


def test_identity_handles_http_error() -> None:
    """
    HTTP 500 precisa ser convertido
    para IdentityHTTPError.
    """

    client = create_identity_client()

    with pytest.raises(
        IdentityHTTPError
    ):
        client.get_user(
            "http500"
        )

    client.close()


def test_identity_handles_invalid_json() -> None:
    """
    Conteúdo inválido precisa gerar
    IdentityResponseError.
    """

    client = create_identity_client()

    with pytest.raises(
        IdentityResponseError
    ):
        client.get_user(
            "badjson"
        )

    client.close()


def test_identity_handlers_register_four_tools() -> None:
    """
    Os quatro handlers IAM precisam
    ser registrados no ToolRegistry.
    """

    handlers = IdentityToolHandlers(
        client=create_identity_client()
    )

    registry = ToolRegistry()

    handlers.register(
        registry
    )

    assert (
        registry.registered_tool_ids()
        == (
            "iam.get_account_status",
            "iam.get_group_membership",
            "iam.get_mfa_status",
            "iam.get_user",
        )
    )


def test_identity_runtime_get_user() -> None:
    """
    Testa iam.get_user através
    do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-IAM-0001",
        execution_id="EXEC-IAM-0001",
        agent_id="AG-05",
        case_id="CASE-IAM-0001",
        correlation_id="CORR-IAM-0001",
        tool_id="iam.get_user",
        input_payload={
            "username": "lab.user",
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

    assert evidence["source"] == "IAM"

    assert (
        evidence["operation"]
        == "get_user"
    )

    assert evidence["read_only"] is True


def test_identity_runtime_account_status_for_ag03() -> None:
    """
    AG-03 possui autorização explícita
    para iam.get_account_status.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-IAM-0002",
        execution_id="EXEC-IAM-0002",
        agent_id="AG-03",
        case_id="CASE-IAM-0001",
        correlation_id="CORR-IAM-0001",
        tool_id="iam.get_account_status",
        input_payload={
            "username": "lab.user",
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
        output["result"]
        ["account_enabled"]
        is True
    )


def test_identity_runtime_mfa_status() -> None:
    """
    Testa iam.get_mfa_status através
    do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-IAM-0003",
        execution_id="EXEC-IAM-0003",
        agent_id="AG-05",
        case_id="CASE-IAM-0001",
        correlation_id="CORR-IAM-0001",
        tool_id="iam.get_mfa_status",
        input_payload={
            "username": "lab.user",
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
        output["result"]
        ["mfa_enabled"]
        is True
    )


def test_identity_runtime_group_membership() -> None:
    """
    Testa iam.get_group_membership
    através do ToolRuntime.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-IAM-0004",
        execution_id="EXEC-IAM-0004",
        agent_id="AG-05",
        case_id="CASE-IAM-0001",
        correlation_id="CORR-IAM-0001",
        tool_id="iam.get_group_membership",
        input_payload={
            "username": "lab.user",
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
        == "get_group_membership"
    )


def test_identity_runtime_denies_ag03_get_user() -> None:
    """
    AG-03 pode consultar estado da conta,
    mas não pode executar iam.get_user.
    """

    runtime = create_runtime()

    request = ToolRequest(
        request_id="REQ-IAM-DENIED",
        execution_id="EXEC-IAM-DENIED",
        agent_id="AG-03",
        case_id="CASE-IAM-0001",
        correlation_id="CORR-IAM-0001",
        tool_id="iam.get_user",
        input_payload={
            "username": "lab.user",
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


def test_identity_agent_uses_official_tool_ids() -> None:
    """
    AG-05 precisa utilizar os IDs oficiais
    definidos na camada de ferramentas.
    """

    agent = IdentityAnalystAgent()

    assert agent.allowed_tools == (
        "iam.get_user",
        "iam.get_account_status",
        "iam.get_mfa_status",
        "iam.get_group_membership",
        "elastic.search_events",
    )

    assert agent.can_use_tool(
        "iam.get_user"
    ) is True

    assert agent.can_use_tool(
        "elastic.search_events"
    ) is True

    assert agent.can_use_tool(
        "lookup_identity"
    ) is False