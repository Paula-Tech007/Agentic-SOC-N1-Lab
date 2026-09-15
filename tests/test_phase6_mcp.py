"""
Testes automatizados da Fase 6.0.

Agentic SOC N1 Lab
MCP — Model Context Protocol.

Cobertura:

- configuração MCP;
- guardrails;
- contratos;
- imutabilidade;
- registry MCP;
- política por agente;
- bridge MCP -> ToolRuntime;
- fail-closed;
- limitação de timeout;
- validação de binding;
- servidor MCP;
- exposição seletiva de tools;
- chamada MCP ponta a ponta em memória.

Nenhum teste realiza ação crítica.
Nenhum teste acessa integração real.
Nenhum teste depende de rede externa.
"""

from __future__ import annotations

import asyncio

from datetime import (
    datetime,
    timezone,
)

import pytest

from mcp import (
    Client,
)

from soc_mcp import (
    MCPCallStatus,
    MCPConfig,
    MCPToolCallRequest,
    MCPToolCallResult,
    MCPToolDescriptor,
    MCPToolRegistry,
)

from soc_mcp.server import (
    MCPToolRuntimeBridge,
    create_mcp_server,
)

from tools.contracts import (
    ToolExecutionStatus,
    ToolResult,
)


# ============================================================
# HELPERS
# ============================================================


def _build_mcp_request(
    *,
    agent_id: str = "AG-04",
    tool_id: str = "misp.search_ioc",
    timeout_seconds: int = 30,
) -> MCPToolCallRequest:
    """
    Cria requisição MCP padrão
    para testes.
    """

    return MCPToolCallRequest(
        request_id="MCP-REQ-TEST-0001",
        execution_id="MCP-EXEC-TEST-0001",
        agent_id=agent_id,
        case_id="CASE-MCP-TEST-0001",
        correlation_id="CORR-MCP-TEST-0001",
        tool_id=tool_id,
        arguments={
            "value": "203.0.113.10",
        },
        timeout_seconds=timeout_seconds,
    )


class SuccessfulFakeRuntime:
    """
    Runtime simulado de sucesso.

    Não acessa nenhuma integração real.
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


class FailingFakeRuntime:
    """
    Runtime simulado que lança erro.
    """

    def execute(
        self,
        request,
    ) -> ToolResult:
        raise RuntimeError(
            "Falha simulada do runtime."
        )


class TrackingFakeRuntime:
    """
    Runtime usado para confirmar
    que chamadas bloqueadas não chegam
    ao ToolRuntime.
    """

    def __init__(
        self,
    ) -> None:
        self.called = False

    def execute(
        self,
        request,
    ) -> ToolResult:
        self.called = True

        raise RuntimeError(
            "Runtime não deveria "
            "ser chamado."
        )


class InvalidBindingFakeRuntime:
    """
    Retorna ToolResult válido,
    mas vinculado a outra requisição.

    O bridge deve bloquear.
    """

    def execute(
        self,
        request,
    ) -> ToolResult:
        return ToolResult(
            request_id="OUTRA-REQUISICAO",
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
            },
            evidence_payload={
                "source": "LAB",
            },
            attempts=1,
            duration_ms=1,
        )


# ============================================================
# CONFIG
# ============================================================


def test_mcp_config_defaults() -> None:
    """
    Configuração padrão deve permanecer
    local, STDIO e read-only.
    """

    config = MCPConfig()

    assert (
        config.server_name
        == "agentic-soc-n1-lab"
    )

    assert (
        config.server_version
        == "0.1.0"
    )

    assert (
        config.transport
        == "stdio"
    )

    assert (
        config.timeout_seconds
        == 30
    )

    assert (
        config.local_only
        is True
    )

    assert (
        config.read_only
        is True
    )

    assert (
        config.fail_closed
        is True
    )

    assert (
        config.allow_network_transport
        is False
    )

    assert (
        config.allow_critical_actions
        is False
    )


def test_mcp_config_blocks_network_transport() -> None:
    """
    Transporte de rede deve ser
    bloqueado nesta fase.
    """

    with pytest.raises(
        ValueError,
        match="Transporte MCP",
    ):
        MCPConfig(
            transport=(
                "streamable-http"
            )
        )


def test_mcp_config_blocks_critical_actions() -> None:
    """
    Ações críticas autônomas
    não podem ser habilitadas.
    """

    with pytest.raises(
        ValueError,
        match="Ações críticas",
    ):
        MCPConfig(
            allow_critical_actions=True
        )


def test_mcp_config_blocks_non_read_only() -> None:
    """
    Fase 6.0 permanece read-only.
    """

    with pytest.raises(
        ValueError,
        match="READ_ONLY",
    ):
        MCPConfig(
            read_only=False
        )


def test_mcp_config_blocks_non_local() -> None:
    """
    Fase 6.0 permanece local-only.
    """

    with pytest.raises(
        ValueError,
        match="local",
    ):
        MCPConfig(
            local_only=False
        )


def test_mcp_config_safe_summary() -> None:
    """
    Safe summary deve refletir
    os guardrails principais.
    """

    summary = (
        MCPConfig().safe_summary()
    )

    assert (
        summary["integration"]
        == "MCP"
    )

    assert (
        summary["transport"]
        == "stdio"
    )

    assert (
        summary["local_only"]
        is True
    )

    assert (
        summary["read_only"]
        is True
    )

    assert (
        summary["network_transport"]
        is False
    )

    assert (
        summary["critical_actions"]
        is False
    )


# ============================================================
# CONTRACTS
# ============================================================


def test_mcp_tool_descriptor_valid() -> None:
    """
    Descriptor read-only válido.
    """

    descriptor = MCPToolDescriptor(
        tool_id="misp.search_ioc",
        title="Search IOC",
        description=(
            "Consulta defensiva."
        ),
        allowed_agents=(
            "AG-04",
            "AG-09",
        ),
        input_schema={
            "type": "object",
        },
    )

    assert (
        descriptor.tool_id
        == "misp.search_ioc"
    )

    assert (
        descriptor.read_only
        is True
    )

    assert (
        descriptor.local_only
        is True
    )

    assert (
        descriptor.critical_action
        is False
    )


def test_mcp_tool_descriptor_blocks_critical_action() -> None:
    """
    Descriptor de ação crítica
    deve falhar fechado.
    """

    with pytest.raises(
        ValueError,
        match="Ações críticas",
    ):
        MCPToolDescriptor(
            tool_id="network.block_ip",
            title="Block IP",
            description=(
                "Ação não autorizada."
            ),
            allowed_agents=(
                "AG-09",
            ),
            critical_action=True,
        )


def test_mcp_request_is_created() -> None:
    """
    Requisição MCP deve preservar
    contexto obrigatório.
    """

    request = (
        _build_mcp_request()
    )

    assert (
        request.agent_id
        == "AG-04"
    )

    assert (
        request.case_id
        == "CASE-MCP-TEST-0001"
    )

    assert (
        request.tool_id
        == "misp.search_ioc"
    )

    assert (
        request.arguments["value"]
        == "203.0.113.10"
    )


def test_mcp_request_arguments_are_immutable() -> None:
    """
    Payload MCP precisa permanecer
    imutável.
    """

    request = (
        _build_mcp_request()
    )

    with pytest.raises(
        TypeError
    ):
        request.arguments[
            "value"
        ] = "198.51.100.10"


def test_mcp_request_requires_timezone() -> None:
    """
    Timestamp sem timezone
    deve ser rejeitado.
    """

    with pytest.raises(
        ValueError,
        match="timezone",
    ):
        MCPToolCallRequest(
            request_id="REQ-1",
            execution_id="EXEC-1",
            agent_id="AG-04",
            case_id="CASE-1",
            correlation_id="CORR-1",
            tool_id="misp.search_ioc",
            requested_at=datetime(
                2026,
                9,
                15,
                20,
                0,
                0,
            ),
        )


def test_mcp_completed_result_requires_success() -> None:
    """
    COMPLETED + success=False
    é inconsistente.
    """

    with pytest.raises(
        ValueError,
        match="success=True",
    ):
        MCPToolCallResult(
            request_id="REQ-1",
            execution_id="EXEC-1",
            agent_id="AG-04",
            case_id="CASE-1",
            correlation_id="CORR-1",
            tool_id="misp.search_ioc",
            status=(
                MCPCallStatus.COMPLETED
            ),
            success=False,
        )


def test_mcp_denied_result_requires_failure() -> None:
    """
    DENIED + success=True
    deve ser rejeitado.
    """

    with pytest.raises(
        ValueError,
        match="success=False",
    ):
        MCPToolCallResult(
            request_id="REQ-1",
            execution_id="EXEC-1",
            agent_id="AG-04",
            case_id="CASE-1",
            correlation_id="CORR-1",
            tool_id="misp.search_ioc",
            status=(
                MCPCallStatus.DENIED
            ),
            success=True,
            error_message=(
                "Acesso negado."
            ),
        )


def test_mcp_failed_result_requires_error_message() -> None:
    """
    Resultado de falha sem mensagem
    deve ser recusado.
    """

    with pytest.raises(
        ValueError,
        match="error_message",
    ):
        MCPToolCallResult(
            request_id="REQ-1",
            execution_id="EXEC-1",
            agent_id="AG-04",
            case_id="CASE-1",
            correlation_id="CORR-1",
            tool_id="misp.search_ioc",
            status=(
                MCPCallStatus.FAILED
            ),
            success=False,
        )


# ============================================================
# REGISTRY
# ============================================================


def test_mcp_registry_has_18_official_tools() -> None:
    """
    Registry atual deve possuir
    exatamente 18 tools defensivas.
    """

    registry = MCPToolRegistry()

    assert (
        len(registry)
        == 18
    )


def test_mcp_registry_contains_expected_tools() -> None:
    """
    Tools oficiais das integrações
    atuais precisam existir.
    """

    registry = MCPToolRegistry()

    assert (
        "misp.search_ioc"
        in registry
    )

    assert (
        "elastic.search_events"
        in registry
    )

    assert (
        "iam.get_user"
        in registry
    )

    assert (
        "asset.get_asset"
        in registry
    )

    assert (
        "email.get_headers"
        in registry
    )


def test_mcp_registry_blocks_forbidden_tools() -> None:
    """
    Ferramentas críticas proibidas
    não podem ser expostas.
    """

    registry = MCPToolRegistry()

    assert (
        "iam.reset_password"
        not in registry
    )

    assert (
        "network.block_ip"
        not in registry
    )

    assert (
        "firewall.add_rule"
        not in registry
    )

    assert (
        "endpoint.isolate_host"
        not in registry
    )


def test_mcp_registry_agent_policy_misp() -> None:
    """
    AG-04 pode consultar MISP;
    AG-03 não pode usar misp.search_ioc.
    """

    registry = MCPToolRegistry()

    assert (
        registry.can_agent_use(
            agent_id="AG-04",
            tool_id="misp.search_ioc",
        )
        is True
    )

    assert (
        registry.can_agent_use(
            agent_id="AG-03",
            tool_id="misp.search_ioc",
        )
        is False
    )


def test_mcp_registry_agent_policy_email() -> None:
    """
    AG-07 pode consultar headers
    de email.
    """

    registry = MCPToolRegistry()

    assert (
        registry.can_agent_use(
            agent_id="AG-07",
            tool_id=(
                "email.get_headers"
            ),
        )
        is True
    )

    assert (
        registry.can_agent_use(
            agent_id="AG-07",
            tool_id=(
                "iam.reset_password"
            ),
        )
        is False
    )


def test_mcp_registry_ag04_tools() -> None:
    """
    AG-04 possui as três tools
    MISP oficiais.
    """

    registry = MCPToolRegistry()

    tool_ids = {
        item.tool_id
        for item
        in registry.allowed_for_agent(
            "AG-04"
        )
    }

    assert tool_ids == {
        "misp.get_attribute",
        "misp.get_event",
        "misp.search_ioc",
    }


# ============================================================
# BRIDGE
# ============================================================


def test_mcp_bridge_blocks_agent_before_runtime() -> None:
    """
    Agente não autorizado deve ser
    barrado antes do ToolRuntime.
    """

    runtime = TrackingFakeRuntime()

    bridge = MCPToolRuntimeBridge(
        runtime=runtime
    )

    result = bridge.execute(
        _build_mcp_request(
            agent_id="AG-03",
        )
    )

    assert (
        result.status
        is MCPCallStatus.DENIED
    )

    assert (
        result.success
        is False
    )

    assert (
        result.error_code
        == "MCP_AGENT_NOT_ALLOWED"
    )

    assert (
        runtime.called
        is False
    )


def test_mcp_bridge_blocks_unknown_tool() -> None:
    """
    Tool inexistente deve falhar
    antes do runtime.
    """

    runtime = TrackingFakeRuntime()

    bridge = MCPToolRuntimeBridge(
        runtime=runtime
    )

    result = bridge.execute(
        _build_mcp_request(
            tool_id=(
                "unknown.tool"
            ),
        )
    )

    assert (
        result.status
        is MCPCallStatus.DENIED
    )

    assert (
        result.error_code
        == "MCP_TOOL_NOT_EXPOSED"
    )

    assert (
        runtime.called
        is False
    )


def test_mcp_bridge_success() -> None:
    """
    Caminho positivo deve converter
    ToolResult em MCPToolCallResult.
    """

    runtime = (
        SuccessfulFakeRuntime()
    )

    bridge = MCPToolRuntimeBridge(
        runtime=runtime
    )

    result = bridge.execute(
        _build_mcp_request()
    )

    assert (
        result.status
        is MCPCallStatus.COMPLETED
    )

    assert (
        result.success
        is True
    )

    assert (
        result.error_code
        is None
    )

    assert (
        result.output["simulated"]
        is True
    )

    assert (
        result.evidence["source"]
        == "LAB"
    )

    assert (
        runtime.called
        is True
    )


def test_mcp_bridge_limits_timeout_to_tool_policy() -> None:
    """
    MCP nunca pode aumentar
    timeout da política oficial.
    """

    runtime = (
        SuccessfulFakeRuntime()
    )

    bridge = MCPToolRuntimeBridge(
        runtime=runtime
    )

    bridge.execute(
        _build_mcp_request(
            timeout_seconds=120,
        )
    )

    assert (
        runtime.last_request
        is not None
    )

    assert (
        runtime.last_request.timeout_seconds
        == 15
    )

    assert (
        runtime.last_request.max_retries
        == 1
    )


def test_mcp_bridge_preserves_context() -> None:
    """
    Contexto de segurança deve chegar
    intacto ao ToolRuntime.
    """

    runtime = (
        SuccessfulFakeRuntime()
    )

    bridge = MCPToolRuntimeBridge(
        runtime=runtime
    )

    request = (
        _build_mcp_request()
    )

    bridge.execute(
        request
    )

    tool_request = (
        runtime.last_request
    )

    assert (
        tool_request.agent_id
        == request.agent_id
    )

    assert (
        tool_request.case_id
        == request.case_id
    )

    assert (
        tool_request.correlation_id
        == request.correlation_id
    )

    assert (
        tool_request.tool_id
        == request.tool_id
    )


def test_mcp_bridge_runtime_exception_fails_closed() -> None:
    """
    Exceção do runtime deve virar
    resultado FAILED.
    """

    bridge = MCPToolRuntimeBridge(
        runtime=(
            FailingFakeRuntime()
        )
    )

    result = bridge.execute(
        _build_mcp_request()
    )

    assert (
        result.status
        is MCPCallStatus.FAILED
    )

    assert (
        result.success
        is False
    )

    assert (
        result.error_code
        == "MCP_RUNTIME_ERROR"
    )


def test_mcp_bridge_invalid_binding_fails_closed() -> None:
    """
    ToolResult ligado a outra requisição
    deve ser recusado.
    """

    bridge = MCPToolRuntimeBridge(
        runtime=(
            InvalidBindingFakeRuntime()
        )
    )

    result = bridge.execute(
        _build_mcp_request()
    )

    assert (
        result.status
        is MCPCallStatus.FAILED
    )

    assert (
        result.error_code
        == (
            "INVALID_TOOL_RESULT_BINDING"
        )
    )


def test_mcp_bridge_summary() -> None:
    """
    Summary precisa mostrar que acesso
    direto às integrações é proibido.
    """

    bridge = MCPToolRuntimeBridge(
        runtime=(
            SuccessfulFakeRuntime()
        )
    )

    summary = (
        bridge.safe_summary()
    )

    assert (
        summary[
            "uses_tool_runtime"
        ]
        is True
    )

    assert (
        summary[
            "direct_integration_access"
        ]
        is False
    )

    assert (
        summary[
            "critical_actions"
        ]
        is False
    )

    assert (
        summary[
            "deny_by_default"
        ]
        is True
    )

    assert (
        summary[
            "fail_closed"
        ]
        is True
    )


# ============================================================
# MCP SERVER
# ============================================================


def test_mcp_server_exposes_only_ag04_tools() -> None:
    """
    Servidor vinculado ao AG-04
    deve publicar somente suas
    três ferramentas MISP.
    """

    async def scenario() -> None:
        server = create_mcp_server(
            runtime=(
                SuccessfulFakeRuntime()
            ),
            agent_id="AG-04",
            case_id="CASE-MCP-0001",
            correlation_id=(
                "CORR-MCP-0001"
            ),
        )

        async with Client(
            server
        ) as client:
            response = (
                await client.list_tools()
            )

            names = {
                tool.name
                for tool
                in response.tools
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

    asyncio.run(
        scenario()
    )


def test_mcp_server_end_to_end_in_memory() -> None:
    """
    Valida:

    MCP Client
        ->
    MCPServer
        ->
    Bridge
        ->
    ToolRuntime simulado
        ->
    MCP Client

    sem rede externa.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulFakeRuntime()
        )

        server = create_mcp_server(
            runtime=runtime,
            agent_id="AG-04",
            case_id="CASE-MCP-0001",
            correlation_id=(
                "CORR-MCP-0001"
            ),
        )

        async with Client(
            server
        ) as client:
            result = (
                await client.call_tool(
                    "misp.search_ioc",
                    {
                        "arguments": {
                            "value": (
                                "203.0.113.10"
                            ),
                        }
                    },
                )
            )

            assert (
                result.is_error
                is False
            )

            assert (
                result.structured_content
                is not None
            )

            assert (
                runtime.last_request
                is not None
            )

            assert (
                runtime.last_request.tool_id
                == "misp.search_ioc"
            )

            assert (
                runtime.last_request.agent_id
                == "AG-04"
            )

            assert (
                runtime.last_request.case_id
                == "CASE-MCP-0001"
            )

            assert (
                runtime.last_request.correlation_id
                == "CORR-MCP-0001"
            )

            assert (
                runtime.last_request.timeout_seconds
                == 15
            )

            assert (
                runtime.last_request.max_retries
                == 1
            )

            assert dict(
                runtime.last_request.input_payload
            ) == {
                "value": "203.0.113.10",
            }

            payload = (
                result.structured_content
            )

            assert (
                payload["status"]
                == "COMPLETED"
            )

            assert (
                payload["success"]
                is True
            )

            assert (
                payload["agent_id"]
                == "AG-04"
            )

            assert (
                payload["case_id"]
                == "CASE-MCP-0001"
            )

            assert (
                payload["evidence"][
                    "read_only"
                ]
                is True
            )

    asyncio.run(
        scenario()
    )


def test_mcp_server_context_cannot_be_selected_by_client() -> None:
    """
    O agente e o caso utilizados pelo
    ToolRuntime devem ser os vinculados
    ao servidor, não enviados pelo cliente.
    """

    async def scenario() -> None:
        runtime = (
            SuccessfulFakeRuntime()
        )

        server = create_mcp_server(
            runtime=runtime,
            agent_id="AG-04",
            case_id="CASE-FIXED-0001",
            correlation_id=(
                "CORR-FIXED-0001"
            ),
        )

        async with Client(
            server
        ) as client:
            await client.call_tool(
                "misp.search_ioc",
                {
                    "arguments": {
                        "value": (
                            "203.0.113.10"
                        ),
                    }
                },
            )

        assert (
            runtime.last_request.agent_id
            == "AG-04"
        )

        assert (
            runtime.last_request.case_id
            == "CASE-FIXED-0001"
        )

        assert (
            runtime.last_request.correlation_id
            == "CORR-FIXED-0001"
        )

    asyncio.run(
        scenario()
    )


# ============================================================
# IMPORT / SANITY
# ============================================================


def test_mcp_timestamp_is_utc() -> None:
    """
    Timestamp automático deve possuir
    timezone UTC.
    """

    request = (
        _build_mcp_request()
    )

    assert (
        request.requested_at.tzinfo
        is not None
    )

    assert (
        request.requested_at.utcoffset()
        == datetime.now(
            timezone.utc
        ).utcoffset()
    )


def test_phase6_mcp_sanity() -> None:
    """
    Marca final da fundação MCP.
    """

    registry = MCPToolRegistry()

    config = MCPConfig()

    assert (
        len(registry)
        == 18
    )

    assert (
        config.transport
        == "stdio"
    )

    assert (
        config.read_only
        is True
    )

    assert (
        config.allow_critical_actions
        is False
    )