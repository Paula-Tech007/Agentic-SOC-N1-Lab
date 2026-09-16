"""
Testes formais do cliente MCP
do Agentic SOC N1 Lab.

Fase 6.1 — Cliente/uso controlado do MCP.

Escopo:

- contratos do cliente;
- ciclo de vida local;
- listagem de tools autorizadas;
- execução read-only;
- preservação de contexto;
- fail-closed;
- bloqueio antes do ToolRuntime;
- ausência de elevação de privilégio.

Regras preservadas:

- local-only;
- read-only;
- deny-by-default;
- fail-closed;
- nenhuma ação crítica autônoma;
- ToolRuntime permanece soberano;
- cliente não escolhe agent_id;
- cliente não escolhe case_id;
- cliente não escolhe correlation_id.
"""

from __future__ import annotations

import asyncio

from dataclasses import (
    FrozenInstanceError,
    fields,
)

import pytest

from soc_mcp.client.contracts import (
    MCPClientToolCallRequest,
)

from soc_mcp.client.local import (
    LocalMCPClient,
)

from soc_mcp.server import (
    create_mcp_server,
)

from tools.contracts import (
    ToolExecutionStatus,
    ToolResult,
)


class SuccessfulClientFakeRuntime:
    """
    Runtime simulado de sucesso.

    Não acessa integração real.
    """

    def __init__(
        self,
    ) -> None:
        self.called = False

        self.last_request = None

    def execute(
        self,
        request,
    ) -> ToolResult:
        """
        Simula execução read-only
        concluída com sucesso.
        """

        self.called = True

        self.last_request = request

        return ToolResult(
            request_id=(
                request.request_id
            ),
            execution_id=(
                request.execution_id
            ),
            agent_id=(
                request.agent_id
            ),
            case_id=(
                request.case_id
            ),
            correlation_id=(
                request.correlation_id
            ),
            tool_id=(
                request.tool_id
            ),
            status=(
                ToolExecutionStatus.COMPLETED
            ),
            success=True,
            output_payload={
                "simulated": True,
                "tool_id": (
                    request.tool_id
                ),
                "agent_id": (
                    request.agent_id
                ),
                "case_id": (
                    request.case_id
                ),
                "correlation_id": (
                    request.correlation_id
                ),
                "input_payload": dict(
                    request.input_payload
                ),
            },
            evidence_payload={
                "source": "LAB",
                "read_only": True,
                "via_mcp": True,
            },
            attempts=1,
            duration_ms=7,
        )


class TrackingClientFakeRuntime:
    """
    Runtime de rastreamento.

    Se execute() for chamado em um
    cenário que deveria ser bloqueado,
    o teste deve falhar.
    """

    def __init__(
        self,
    ) -> None:
        self.called = False

    def execute(
        self,
        request,
    ) -> ToolResult:
        """
        Nunca deveria ser executado
        nos testes de bloqueio.
        """

        self.called = True

        raise RuntimeError(
            "Runtime não deveria "
            "ser chamado."
        )


def _create_ag04_server(
    runtime,
    *,
    case_id: str = (
        "CASE-MCP-CLIENT-0001"
    ),
    correlation_id: str = (
        "CORR-MCP-CLIENT-0001"
    ),
):
    """
    Cria servidor MCP local
    vinculado ao AG-04.
    """

    return create_mcp_server(
        runtime=runtime,
        agent_id="AG-04",
        case_id=case_id,
        correlation_id=(
            correlation_id
        ),
    )


def test_phase6_1_client_request_has_no_security_context() -> None:
    """
    Contrato do cliente não pode
    permitir escolha de contexto.
    """

    names = [
        item.name
        for item
        in fields(
            MCPClientToolCallRequest
        )
    ]

    assert names == [
        "tool_id",
        "arguments",
    ]

    assert "agent_id" not in names

    assert "case_id" not in names

    assert (
        "correlation_id"
        not in names
    )


def test_phase6_1_client_request_is_immutable() -> None:
    """
    Contrato do cliente deve ser
    imutável após criação.
    """

    request = MCPClientToolCallRequest(
        tool_id="misp.search_ioc",
        arguments={
            "value": "203.0.113.10",
        },
    )

    with pytest.raises(
        FrozenInstanceError
    ):
        request.tool_id = (
            "misp.get_event"
        )

    with pytest.raises(
        TypeError
    ):
        request.arguments[
            "value"
        ] = "198.51.100.10"


def test_phase6_1_client_rejects_invalid_server() -> None:
    """
    Cliente aceita somente
    MCPServer oficial.
    """

    with pytest.raises(
        TypeError,
        match="MCPServer",
    ):
        LocalMCPClient(
            object()
        )


def test_phase6_1_session_requires_connection() -> None:
    """
    Acesso à sessão fora de conexão
    deve falhar fechado.
    """

    runtime = (
        SuccessfulClientFakeRuntime()
    )

    server = _create_ag04_server(
        runtime
    )

    client = LocalMCPClient(
        server
    )

    with pytest.raises(
        RuntimeError,
        match="não está conectado",
    ):
        client.session


def test_phase6_1_client_connection_lifecycle() -> None:
    """
    Cliente deve conectar e encerrar
    a sessão corretamente.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime
        )

        client = LocalMCPClient(
            server
        )

        assert (
            client.connected
            is False
        )

        async with client:
            assert (
                client.connected
                is True
            )

            assert (
                client.session
                is not None
            )

            assert (
                runtime.called
                is False
            )

        assert (
            client.connected
            is False
        )

        assert (
            runtime.called
            is False
        )

    asyncio.run(
        scenario()
    )


def test_phase6_1_duplicate_connection_is_rejected() -> None:
    """
    Conexão duplicada deve ser
    rejeitada explicitamente.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime
        )

        client = LocalMCPClient(
            server
        )

        await client.connect()

        try:
            with pytest.raises(
                RuntimeError,
                match="já está conectado",
            ):
                await client.connect()

        finally:
            await client.close()

    asyncio.run(
        scenario()
    )


def test_phase6_1_lists_only_ag04_authorized_tools() -> None:
    """
    Cliente deve enxergar somente
    tools publicadas para AG-04.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime
        )

        async with LocalMCPClient(
            server
        ) as client:
            tools = (
                await client
                .list_authorized_tools()
            )

        names = {
            tool.tool_id
            for tool
            in tools
        }

        assert names == {
            "misp.get_attribute",
            "misp.get_event",
            "misp.search_ioc",
        }

        assert (
            "email.get_headers"
            not in names
        )

        assert (
            "iam.reset_password"
            not in names
        )

        assert (
            runtime.called
            is False
        )

    asyncio.run(
        scenario()
    )


def test_phase6_1_executes_read_only_tool() -> None:
    """
    Tool autorizada read-only
    deve executar com sucesso.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime
        )

        request = (
            MCPClientToolCallRequest(
                tool_id=(
                    "misp.search_ioc"
                ),
                arguments={
                    "value": (
                        "203.0.113.10"
                    ),
                },
            )
        )

        async with LocalMCPClient(
            server
        ) as client:
            result = (
                await client
                .execute_read_only_tool(
                    request
                )
            )

        assert (
            result.success
            is True
        )

        assert (
            result.status.value
            == "COMPLETED"
        )

        assert (
            result.tool_id
            == "misp.search_ioc"
        )

        assert (
            result.evidence[
                "read_only"
            ]
            is True
        )

        assert (
            runtime.called
            is True
        )

    asyncio.run(
        scenario()
    )


def test_phase6_1_server_context_is_preserved() -> None:
    """
    agent/case/correlation utilizados
    devem vir do servidor.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime,
            case_id=(
                "CASE-FIXED-610"
            ),
            correlation_id=(
                "CORR-FIXED-610"
            ),
        )

        request = (
            MCPClientToolCallRequest(
                tool_id=(
                    "misp.search_ioc"
                ),
                arguments={
                    "value": (
                        "203.0.113.10"
                    ),
                },
            )
        )

        async with LocalMCPClient(
            server
        ) as client:
            result = (
                await client
                .execute_read_only_tool(
                    request
                )
            )

        assert (
            runtime.last_request
            is not None
        )

        assert (
            runtime.last_request.agent_id
            == "AG-04"
        )

        assert (
            runtime.last_request.case_id
            == "CASE-FIXED-610"
        )

        assert (
            runtime.last_request
            .correlation_id
            == "CORR-FIXED-610"
        )

        assert (
            result.agent_id
            == "AG-04"
        )

        assert (
            result.case_id
            == "CASE-FIXED-610"
        )

        assert (
            result.correlation_id
            == "CORR-FIXED-610"
        )

        assert dict(
            runtime.last_request
            .input_payload
        ) == {
            "value": "203.0.113.10",
        }

    asyncio.run(
        scenario()
    )


def test_phase6_1_blocks_tool_not_allowed_for_agent() -> None:
    """
    Tool válida no catálogo, mas não
    publicada para AG-04, deve falhar
    antes do ToolRuntime.
    """

    async def scenario() -> None:
        runtime = (
            TrackingClientFakeRuntime()
        )

        server = _create_ag04_server(
            runtime
        )

        request = (
            MCPClientToolCallRequest(
                tool_id=(
                    "email.get_headers"
                ),
                arguments={},
            )
        )

        async with LocalMCPClient(
            server
        ) as client:
            await client.execute_read_only_tool(
                request
            )

    with pytest.raises(
        RuntimeError,
        match=(
            "não autorizada "
            "ou não publicada"
        ),
    ):
        asyncio.run(
            scenario()
        )


def test_phase6_1_blocked_tool_never_reaches_runtime() -> None:
    """
    Negação client-side deve impedir
    chegada ao ToolRuntime.
    """

    async def scenario(
        runtime,
    ) -> None:
        server = _create_ag04_server(
            runtime
        )

        request = (
            MCPClientToolCallRequest(
                tool_id=(
                    "email.get_headers"
                ),
                arguments={},
            )
        )

        async with LocalMCPClient(
            server
        ) as client:
            await client.execute_read_only_tool(
                request
            )

    runtime = TrackingClientFakeRuntime()

    with pytest.raises(
        RuntimeError
    ):
        asyncio.run(
            scenario(
                runtime
            )
        )

    assert (
        runtime.called
        is False
    )


def test_phase6_1_blocks_critical_tool_without_exception_group() -> None:
    """
    Ação crítica não publicada deve
    resultar em RuntimeError simples.

    ExceptionGroup do TaskGroup MCP
    não pode mascarar a negação.
    """

    async def scenario(
        runtime,
    ) -> None:
        server = _create_ag04_server(
            runtime
        )

        request = (
            MCPClientToolCallRequest(
                tool_id=(
                    "iam.reset_password"
                ),
                arguments={},
            )
        )

        async with LocalMCPClient(
            server
        ) as client:
            await client.execute_read_only_tool(
                request
            )

    runtime = TrackingClientFakeRuntime()

    with pytest.raises(
        RuntimeError,
        match="iam.reset_password",
    ):
        asyncio.run(
            scenario(
                runtime
            )
        )

    assert (
        runtime.called
        is False
    )