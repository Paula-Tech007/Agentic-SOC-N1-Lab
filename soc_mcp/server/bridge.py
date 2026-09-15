"""
Bridge MCP -> ToolRuntime
do Agentic SOC N1 Lab.

Fase 6.0 — Fundação MCP.

Este módulo conecta a camada MCP ao sistema
oficial de ferramentas já existente.

O MCP NÃO executa integrações diretamente.

Fluxo obrigatório:

MCPToolCallRequest
    ↓
MCPToolRegistry
    ↓
verificação de exposição
    ↓
verificação de agente
    ↓
ToolRequest
    ↓
ToolRuntime
    ↓
ToolAuthorization
    ↓
ToolRegistry / Handler
    ↓
ToolResult
    ↓
MCPToolCallResult

Princípios:

- deny-by-default;
- fail-closed;
- somente ferramentas oficiais;
- somente ferramentas READ_ONLY;
- nenhuma ação crítica;
- nenhuma chamada direta às integrações;
- ToolRuntime continua sendo soberano;
- política oficial continua sendo
  core.permissions.tool_policy;
- o MCP não aumenta permissões de agente;
- o MCP não aumenta timeout da ferramenta;
- o MCP não aumenta retries da ferramenta.

Importante:

O contrato oficial ToolResult utiliza:

    output_payload
    evidence_payload

A camada MCP converte esses campos para:

    output
    evidence

do MCPToolCallResult.
"""

from __future__ import annotations

from typing import (
    Any,
    Mapping,
    Protocol,
)

from core.permissions.tool_policy import (
    get_tool_definition,
)

from soc_mcp.contracts import (
    MCPCallStatus,
    MCPToolCallRequest,
    MCPToolCallResult,
)

from soc_mcp.registry import (
    MCPToolRegistry,
)

from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)


class MCPBridgeError(
    RuntimeError
):
    """
    Erro base da camada bridge MCP.
    """


class MCPRuntimeProtocol(
    Protocol
):
    """
    Contrato mínimo esperado
    do runtime oficial.
    """

    def execute(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        ...


_STATUS_MAP: Mapping[
    ToolExecutionStatus,
    MCPCallStatus,
] = {
    ToolExecutionStatus.COMPLETED: (
        MCPCallStatus.COMPLETED
    ),
    ToolExecutionStatus.FAILED: (
        MCPCallStatus.FAILED
    ),
    ToolExecutionStatus.DENIED: (
        MCPCallStatus.DENIED
    ),
    ToolExecutionStatus.TIMEOUT: (
        MCPCallStatus.TIMEOUT
    ),
    ToolExecutionStatus.UNAVAILABLE: (
        MCPCallStatus.UNAVAILABLE
    ),
}


def _to_plain_data(
    value: Any,
) -> Any:
    """
    Converte estruturas internas
    imutáveis em estruturas simples.

    Mapping -> dict
    tuple -> list
    frozenset -> list
    """

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _to_plain_data(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        tuple,
    ):
        return [
            _to_plain_data(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        frozenset,
    ):
        return [
            _to_plain_data(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        list,
    ):
        return [
            _to_plain_data(
                item
            )
            for item in value
        ]

    return value


def _status_to_mcp(
    status: ToolExecutionStatus,
) -> MCPCallStatus:
    """
    Converte status do ToolRuntime
    em status MCP.

    Status desconhecido falha fechado.
    """

    mapped = _STATUS_MAP.get(
        status
    )

    if mapped is None:
        raise MCPBridgeError(
            "ToolRuntime retornou "
            "status desconhecido."
        )

    return mapped


def _binding_matches(
    *,
    request: MCPToolCallRequest,
    result: ToolResult,
) -> bool:
    """
    Confirma que o ToolResult pertence
    exatamente à requisição MCP atual.
    """

    expected = (
        request.request_id,
        request.execution_id,
        request.agent_id,
        request.case_id,
        request.correlation_id,
        request.tool_id,
    )

    received = (
        result.request_id,
        result.execution_id,
        result.agent_id,
        result.case_id,
        result.correlation_id,
        result.tool_id,
    )

    return (
        expected
        == received
    )


def _denied_result(
    request: MCPToolCallRequest,
    *,
    error_code: str,
    error_message: str,
) -> MCPToolCallResult:
    """
    Cria resultado MCP DENIED.
    """

    return MCPToolCallResult(
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
            MCPCallStatus.DENIED
        ),
        success=False,
        output={},
        evidence={},
        error_code=error_code,
        error_message=error_message,
        attempts=0,
        duration_ms=0,
    )


def _unavailable_result(
    request: MCPToolCallRequest,
    *,
    error_code: str,
    error_message: str,
) -> MCPToolCallResult:
    """
    Cria resultado MCP UNAVAILABLE.
    """

    return MCPToolCallResult(
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
            MCPCallStatus.UNAVAILABLE
        ),
        success=False,
        output={},
        evidence={},
        error_code=error_code,
        error_message=error_message,
        attempts=0,
        duration_ms=0,
    )


def _failed_result(
    request: MCPToolCallRequest,
    *,
    error_code: str,
    error_message: str,
) -> MCPToolCallResult:
    """
    Cria resultado MCP FAILED.
    """

    return MCPToolCallResult(
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
            MCPCallStatus.FAILED
        ),
        success=False,
        output={},
        evidence={},
        error_code=error_code,
        error_message=error_message,
        attempts=0,
        duration_ms=0,
    )


class MCPToolRuntimeBridge:
    """
    Ponte segura entre MCP e ToolRuntime.

    Esta classe nunca acessa diretamente:

    - MISP;
    - Elastic;
    - IAM;
    - Asset / CMDB;
    - Email.

    Toda execução precisa atravessar
    o ToolRuntime oficial.
    """

    def __init__(
        self,
        *,
        runtime: MCPRuntimeProtocol,
        registry: MCPToolRegistry
        | None = None,
    ) -> None:
        """
        Inicializa o bridge.
        """

        execute_method = getattr(
            runtime,
            "execute",
            None,
        )

        if not callable(
            execute_method
        ):
            raise TypeError(
                "runtime precisa possuir "
                "método execute() chamável."
            )

        if (
            registry is not None
            and not isinstance(
                registry,
                MCPToolRegistry,
            )
        ):
            raise TypeError(
                "registry precisa ser "
                "MCPToolRegistry."
            )

        self._runtime = runtime

        self._registry = (
            MCPToolRegistry()
            if registry is None
            else registry
        )

    @property
    def registry(
        self,
    ) -> MCPToolRegistry:
        """
        Registry MCP utilizado.
        """

        return self._registry

    def execute(
        self,
        request: MCPToolCallRequest,
    ) -> MCPToolCallResult:
        """
        Executa uma chamada MCP
        pelo ToolRuntime oficial.

        Qualquer inconsistência
        resulta em fail-closed.
        """

        if not isinstance(
            request,
            MCPToolCallRequest,
        ):
            raise TypeError(
                "request precisa ser "
                "MCPToolCallRequest."
            )

        descriptor = (
            self._registry.get(
                request.tool_id
            )
        )

        if descriptor is None:
            return _denied_result(
                request,
                error_code=(
                    "MCP_TOOL_NOT_EXPOSED"
                ),
                error_message=(
                    "A ferramenta solicitada "
                    "não está disponível "
                    "para exposição MCP."
                ),
            )

        if not self._registry.can_agent_use(
            agent_id=(
                request.agent_id
            ),
            tool_id=(
                request.tool_id
            ),
        ):
            return _denied_result(
                request,
                error_code=(
                    "MCP_AGENT_NOT_ALLOWED"
                ),
                error_message=(
                    "O agente não possui "
                    "permissão para utilizar "
                    "esta ferramenta."
                ),
            )

        definition = (
            get_tool_definition(
                request.tool_id
            )
        )

        if definition is None:
            return _unavailable_result(
                request,
                error_code=(
                    "TOOL_DEFINITION_NOT_FOUND"
                ),
                error_message=(
                    "A definição oficial "
                    "da ferramenta não "
                    "foi encontrada."
                ),
            )

        if (
            descriptor.read_only
            is not True
        ):
            return _denied_result(
                request,
                error_code=(
                    "MCP_READ_ONLY_REQUIRED"
                ),
                error_message=(
                    "Somente ferramentas "
                    "READ_ONLY podem ser "
                    "executadas pelo MCP."
                ),
            )

        if (
            descriptor.critical_action
            is not False
        ):
            return _denied_result(
                request,
                error_code=(
                    "MCP_CRITICAL_ACTION_BLOCKED"
                ),
                error_message=(
                    "Ações críticas não "
                    "podem ser executadas "
                    "pela camada MCP."
                ),
            )

        effective_timeout = min(
            request.timeout_seconds,
            definition.timeout_seconds,
        )

        try:
            tool_request = ToolRequest(
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
                input_payload=(
                    _to_plain_data(
                        request.arguments
                    )
                ),
                timeout_seconds=(
                    effective_timeout
                ),
                max_retries=(
                    definition.max_retries
                ),
                requested_at=(
                    request.requested_at
                ),
            )

        except Exception as exc:
            return _failed_result(
                request,
                error_code=(
                    "MCP_TOOL_REQUEST_ERROR"
                ),
                error_message=(
                    "Falha ao construir "
                    "ToolRequest: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

        try:
            tool_result = (
                self._runtime.execute(
                    tool_request
                )
            )

        except Exception as exc:
            return _failed_result(
                request,
                error_code=(
                    "MCP_RUNTIME_ERROR"
                ),
                error_message=(
                    "ToolRuntime falhou "
                    "durante a execução: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

        if not isinstance(
            tool_result,
            ToolResult,
        ):
            return _failed_result(
                request,
                error_code=(
                    "INVALID_TOOL_RESULT"
                ),
                error_message=(
                    "ToolRuntime retornou "
                    "objeto diferente de "
                    "ToolResult."
                ),
            )

        if not _binding_matches(
            request=request,
            result=tool_result,
        ):
            return _failed_result(
                request,
                error_code=(
                    "INVALID_TOOL_RESULT_BINDING"
                ),
                error_message=(
                    "ToolResult não pertence "
                    "à requisição MCP atual."
                ),
            )

        try:
            mcp_status = (
                _status_to_mcp(
                    tool_result.status
                )
            )

        except MCPBridgeError as exc:
            return _failed_result(
                request,
                error_code=(
                    "INVALID_TOOL_STATUS"
                ),
                error_message=str(
                    exc
                ),
            )

        error_message = (
            tool_result.error_message
        )

        if (
            mcp_status
            is not MCPCallStatus.COMPLETED
            and not error_message
        ):
            error_message = (
                "A execução da ferramenta "
                "não foi concluída."
            )

        try:
            return MCPToolCallResult(
                request_id=(
                    tool_result.request_id
                ),
                execution_id=(
                    tool_result.execution_id
                ),
                agent_id=(
                    tool_result.agent_id
                ),
                case_id=(
                    tool_result.case_id
                ),
                correlation_id=(
                    tool_result.correlation_id
                ),
                tool_id=(
                    tool_result.tool_id
                ),
                status=mcp_status,
                success=(
                    tool_result.success
                ),
                output=(
                    _to_plain_data(
                        tool_result.output_payload
                    )
                ),
                evidence=(
                    _to_plain_data(
                        tool_result.evidence_payload
                    )
                ),
                error_code=(
                    tool_result.error_code
                ),
                error_message=(
                    error_message
                ),
                attempts=(
                    tool_result.attempts
                ),
                duration_ms=(
                    tool_result.duration_ms
                ),
                completed_at=(
                    tool_result.completed_at
                ),
            )

        except Exception as exc:
            return _failed_result(
                request,
                error_code=(
                    "MCP_RESULT_CONVERSION_ERROR"
                ),
                error_message=(
                    "Falha ao converter "
                    "ToolResult para resultado "
                    "MCP: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna informações seguras
        do bridge.
        """

        return {
            "integration": (
                "MCP_TOOLRUNTIME_BRIDGE"
            ),
            "tool_count": len(
                self._registry
            ),
            "read_only_only": True,
            "critical_actions": False,
            "direct_integration_access": False,
            "uses_tool_runtime": True,
            "deny_by_default": True,
            "fail_closed": True,
        }