"""
Testes automatizados da Fase 4
do Agentic SOC N1 Lab.

Estes testes validam a fundação da camada
de ferramentas e integrações de segurança:

- catálogo oficial de ferramentas;
- deny-by-default;
- allowlist por agente;
- ferramentas explicitamente proibidas;
- contratos ToolRequest e ToolResult;
- imutabilidade dos contratos;
- consistência entre status e success;
- autorização por agente;
- limites de timeout;
- limites de retries;
- registro de ferramentas;
- prevenção de registro duplicado;
- rejeição de ferramenta desconhecida;
- snapshot imutável do registry;
- execução controlada pelo ToolRuntime;
- bloqueio de acesso não autorizado;
- tratamento de ferramenta não registrada;
- validação de vínculo ToolRequest/ToolResult;
- tratamento fail-closed de exceções;
- retries controlados.
"""

import pytest
from pydantic import ValidationError

from core.permissions import (
    TOOL_CATALOG,
    allowed_tools_for_agent,
    is_tool_allowed,
    validate_tool_catalog,
)

from tools import (
    ToolExecutionStatus,
    ToolRegistry,
    ToolRequest,
    ToolResult,
    ToolRuntime,
    authorize_tool_request,
)


def create_tool_request(
    request_id: str = "REQ-PHASE4-0001",
    execution_id: str = "EXEC-PHASE4-0001",
    agent_id: str = "AG-04",
    case_id: str = "CASE-PHASE4-0001",
    correlation_id: str = "CORR-PHASE4-0001",
    tool_id: str = "misp.search_ioc",
    timeout_seconds: int = 15,
    max_retries: int = 1,
) -> ToolRequest:
    """
    Cria uma ToolRequest padrão
    para os testes da Fase 4.
    """

    return ToolRequest(
        request_id=request_id,
        execution_id=execution_id,
        agent_id=agent_id,
        case_id=case_id,
        correlation_id=correlation_id,
        tool_id=tool_id,
        input_payload={
            "ioc": "185.10.20.30",
        },
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


def create_success_result(
    request: ToolRequest,
) -> ToolResult:
    """
    Cria um ToolResult válido
    correspondente à ToolRequest recebida.
    """

    return ToolResult(
        request_id=request.request_id,
        execution_id=request.execution_id,
        agent_id=request.agent_id,
        case_id=request.case_id,
        correlation_id=request.correlation_id,
        tool_id=request.tool_id,
        status=ToolExecutionStatus.COMPLETED,
        success=True,
        output_payload={
            "found": True,
            "ioc": request.input_payload.to_dict().get(
                "ioc"
            ),
        },
        evidence_payload={
            "source": "SIMULATED_MISP",
        },
    )


def test_tool_catalog_is_valid() -> None:
    """
    O catálogo oficial precisa passar
    integralmente por sua própria validação.
    """

    validate_tool_catalog()

    assert len(TOOL_CATALOG) == 18


def test_tool_policy_is_deny_by_default() -> None:
    """
    Agentes e ferramentas desconhecidos
    precisam ser recusados.
    """

    assert (
        is_tool_allowed(
            "AG-99",
            "misp.search_ioc",
        )
        is False
    )

    assert (
        is_tool_allowed(
            "AG-04",
            "unknown.tool",
        )
        is False
    )


def test_tool_policy_respects_agent_allowlist() -> None:
    """
    AG-04 pode utilizar MISP,
    enquanto AG-05 não pode.
    """

    assert (
        is_tool_allowed(
            "AG-04",
            "misp.search_ioc",
        )
        is True
    )

    assert (
        is_tool_allowed(
            "AG-05",
            "misp.search_ioc",
        )
        is False
    )

    assert (
        "misp.search_ioc"
        in allowed_tools_for_agent("AG-04")
    )


def test_forbidden_critical_action_is_not_allowed() -> None:
    """
    Reset real de senha não pertence
    ao catálogo operacional autorizado.
    """

    assert (
        is_tool_allowed(
            "AG-05",
            "iam.reset_password",
        )
        is False
    )


def test_tool_request_is_immutable() -> None:
    """
    ToolRequest precisa permanecer imutável
    depois de criada.
    """

    request = create_tool_request()

    with pytest.raises(ValidationError):
        request.agent_id = "AG-05"


def test_tool_result_requires_status_success_consistency() -> None:
    """
    FAILED com success=True é inconsistente
    e precisa ser recusado.
    """

    request = create_tool_request()

    with pytest.raises(ValidationError):
        ToolResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            tool_id=request.tool_id,
            status=ToolExecutionStatus.FAILED,
            success=True,
            error_message="Falha simulada.",
        )


def test_failed_tool_result_requires_error_message() -> None:
    """
    Resultado sem sucesso precisa explicar
    a falha de forma estruturada.
    """

    request = create_tool_request()

    with pytest.raises(ValidationError):
        ToolResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            tool_id=request.tool_id,
            status=ToolExecutionStatus.FAILED,
            success=False,
        )


def test_authorization_allows_valid_request() -> None:
    """
    Uma ToolRequest compatível com a política
    precisa ser autorizada.
    """

    request = create_tool_request()

    decision = authorize_tool_request(
        request
    )

    assert decision.allowed is True
    assert decision.definition is not None
    assert (
        decision.definition.tool_id
        == "misp.search_ioc"
    )


def test_authorization_denies_unauthorized_agent() -> None:
    """
    AG-05 não possui acesso
    a misp.search_ioc.
    """

    request = create_tool_request(
        agent_id="AG-05"
    )

    decision = authorize_tool_request(
        request
    )

    assert decision.allowed is False
    assert decision.definition is None


def test_authorization_denies_timeout_above_policy() -> None:
    """
    Timeout solicitado não pode superar
    o limite oficial da ferramenta.
    """

    request = create_tool_request(
        timeout_seconds=99
    )

    decision = authorize_tool_request(
        request
    )

    assert decision.allowed is False
    assert "99 > 15" in decision.reason


def test_authorization_denies_retries_above_policy() -> None:
    """
    Retries solicitados não podem superar
    o limite oficial da ferramenta.
    """

    request = create_tool_request(
        max_retries=99
    )

    decision = authorize_tool_request(
        request
    )

    assert decision.allowed is False
    assert "99 > 1" in decision.reason


def test_registry_registers_official_tool() -> None:
    """
    Ferramenta oficial pode receber
    uma implementação registrada.
    """

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        create_success_result,
    )

    assert (
        registry.is_registered(
            "misp.search_ioc"
        )
        is True
    )

    assert len(registry) == 1

    assert (
        registry.registered_tool_ids()
        == ("misp.search_ioc",)
    )


def test_registry_rejects_duplicate_registration() -> None:
    """
    Uma implementação não pode ser
    registrada duas vezes.
    """

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        create_success_result,
    )

    with pytest.raises(ValueError):
        registry.register(
            "misp.search_ioc",
            create_success_result,
        )


def test_registry_rejects_unknown_tool() -> None:
    """
    Ferramenta fora do catálogo oficial
    não pode ser registrada.
    """

    registry = ToolRegistry()

    with pytest.raises(ValueError):
        registry.register(
            "unknown.tool",
            create_success_result,
        )


def test_registry_snapshot_is_read_only() -> None:
    """
    O snapshot externo do registry
    precisa ser imutável.
    """

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        create_success_result,
    )

    snapshot = registry.snapshot()

    with pytest.raises(TypeError):
        snapshot[
            "misp.search_ioc"
        ] = create_success_result


def test_runtime_executes_authorized_registered_tool() -> None:
    """
    Runtime precisa executar uma ferramenta
    autorizada e registrada.
    """

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        create_success_result,
    )

    runtime = ToolRuntime(
        registry=registry
    )

    request = create_tool_request()

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    assert (
        result.output_payload.to_dict()
        ["found"]
        is True
    )

    assert result.attempts == 1


def test_runtime_denies_unauthorized_agent() -> None:
    """
    Runtime não pode executar handler
    para agente sem autorização.
    """

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        create_success_result,
    )

    runtime = ToolRuntime(
        registry=registry
    )

    request = create_tool_request(
        agent_id="AG-05"
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


def test_runtime_returns_unavailable_for_unregistered_tool() -> None:
    """
    Ferramenta autorizada mas ainda sem
    implementação precisa retornar UNAVAILABLE.
    """

    registry = ToolRegistry()

    runtime = ToolRuntime(
        registry=registry
    )

    request = ToolRequest(
        request_id="REQ-PHASE4-ELASTIC",
        execution_id="EXEC-PHASE4-ELASTIC",
        agent_id="AG-03",
        case_id="CASE-PHASE4-0001",
        correlation_id="CORR-PHASE4-0001",
        tool_id="elastic.search_alerts",
        input_payload={
            "case_id": "CASE-PHASE4-0001",
        },
        timeout_seconds=20,
        max_retries=1,
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.UNAVAILABLE
    )

    assert result.success is False

    assert (
        result.error_code
        == "TOOL_NOT_REGISTERED"
    )

    assert result.attempts == 0


def test_runtime_rejects_result_bound_to_other_case() -> None:
    """
    Handler não pode devolver resultado
    pertencente a outro caso.
    """

    def invalid_handler(
        request: ToolRequest,
    ) -> ToolResult:
        return ToolResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id="CASE-ERRADO",
            correlation_id=request.correlation_id,
            tool_id=request.tool_id,
            status=ToolExecutionStatus.COMPLETED,
            success=True,
            output_payload={
                "found": True,
            },
            evidence_payload={
                "source": "SIMULATED_MISP",
            },
        )

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        invalid_handler,
    )

    runtime = ToolRuntime(
        registry=registry
    )

    result = runtime.execute(
        create_tool_request()
    )

    assert (
        result.status
        == ToolExecutionStatus.FAILED
    )

    assert result.success is False

    assert (
        result.error_code
        == "INVALID_TOOL_RESULT"
    )


def test_runtime_handles_exception_fail_closed() -> None:
    """
    Exceções internas da integração
    não podem escapar para o agente.
    """

    execution_counter = {
        "count": 0,
    }

    def failing_handler(
        request: ToolRequest,
    ) -> ToolResult:
        execution_counter["count"] += 1

        raise RuntimeError(
            "Falha simulada da integração."
        )

    registry = ToolRegistry()

    registry.register(
        "misp.search_ioc",
        failing_handler,
    )

    runtime = ToolRuntime(
        registry=registry
    )

    request = create_tool_request(
        max_retries=1
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        == ToolExecutionStatus.FAILED
    )

    assert result.success is False

    assert (
        result.error_code
        == "TOOL_EXECUTION_ERROR"
    )

    assert result.attempts == 2

    assert execution_counter["count"] == 2
