"""
Runtime oficial de ferramentas
do Agentic SOC N1 Lab.

Fase 4.0 — Catálogo e Governança das Ferramentas.

Responsabilidades:

- receber ToolRequest;
- validar autorização;
- localizar implementação registrada;
- executar somente handlers autorizados;
- aplicar timeout;
- aplicar retries controlados;
- validar o ToolResult devolvido;
- transformar falhas em resultados estruturados;
- operar de forma fail-closed.

Princípios:

- deny-by-default;
- least privilege;
- nenhuma ferramenta fora do catálogo;
- nenhuma ferramenta sem implementação registrada;
- nenhuma exceção de integração deve escapar
  diretamente para o agente;
- timeout e retries são limitados pela política;
- nenhuma ferramenta modifica diretamente CaseState.
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)
from time import perf_counter
from typing import Any

from tools.authorization import (
    authorize_tool_request,
)
from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from tools.registry import ToolRegistry


class ToolRuntime:
    """
    Executor controlado das ferramentas SOC.

    O runtime não concede permissões.

    Ele somente executa uma ferramenta depois que
    a ToolRequest passa pela camada oficial
    de autorização.
    """

    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Inicializa o runtime com um ToolRegistry.

        O registry precisa ser uma instância válida.
        """

        if not isinstance(registry, ToolRegistry):
            raise TypeError(
                "registry precisa ser uma instância "
                "de ToolRegistry."
            )

        self._registry = registry

    @property
    def registry(
        self,
    ) -> ToolRegistry:
        """
        Retorna o registry utilizado pelo runtime.
        """

        return self._registry

    def execute(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Executa uma ToolRequest de forma controlada.

        Fluxo:

        1. valida o tipo da request;
        2. valida autorização;
        3. procura implementação registrada;
        4. executa com timeout;
        5. aplica retries permitidos;
        6. valida o contrato do resultado;
        7. devolve ToolResult estruturado.

        Qualquer falha resulta em ToolResult
        sem sucesso.

        Exceções de integração não são propagadas
        para o agente.
        """

        if not isinstance(request, ToolRequest):
            raise TypeError(
                "request precisa ser uma ToolRequest."
            )

        started_at = perf_counter()

        authorization = authorize_tool_request(
            request
        )

        if not authorization.allowed:
            return self._failure_result(
                request=request,
                status=ToolExecutionStatus.DENIED,
                error_code="TOOL_ACCESS_DENIED",
                error_message=authorization.reason,
                attempts=0,
                started_at=started_at,
            )

        handler = self._registry.get(
            request.tool_id
        )

        if handler is None:
            return self._failure_result(
                request=request,
                status=ToolExecutionStatus.UNAVAILABLE,
                error_code="TOOL_NOT_REGISTERED",
                error_message=(
                    "Ferramenta autorizada, porém sem "
                    "implementação registrada no runtime."
                ),
                attempts=0,
                started_at=started_at,
            )

        total_attempts = (
            request.max_retries + 1
        )

        for attempt in range(
            1,
            total_attempts + 1,
        ):
            try:
                raw_result = self._execute_handler(
                    handler=handler,
                    request=request,
                )

            except FutureTimeoutError:
                if attempt < total_attempts:
                    continue

                return self._failure_result(
                    request=request,
                    status=ToolExecutionStatus.TIMEOUT,
                    error_code="TOOL_TIMEOUT",
                    error_message=(
                        "A ferramenta excedeu o timeout "
                        "máximo autorizado."
                    ),
                    attempts=attempt,
                    started_at=started_at,
                )

            except Exception as error:
                if attempt < total_attempts:
                    continue

                return self._failure_result(
                    request=request,
                    status=ToolExecutionStatus.FAILED,
                    error_code="TOOL_EXECUTION_ERROR",
                    error_message=(
                        "Falha interna durante a execução "
                        "da ferramenta: "
                        f"{type(error).__name__}."
                    ),
                    attempts=attempt,
                    started_at=started_at,
                )

            validation_error = (
                self._validate_result_binding(
                    request=request,
                    result=raw_result,
                )
            )

            if validation_error is not None:
                return self._failure_result(
                    request=request,
                    status=ToolExecutionStatus.FAILED,
                    error_code="INVALID_TOOL_RESULT",
                    error_message=validation_error,
                    attempts=attempt,
                    started_at=started_at,
                )

            return self._finalize_result(
                result=raw_result,
                attempts=attempt,
                started_at=started_at,
            )

        return self._failure_result(
            request=request,
            status=ToolExecutionStatus.FAILED,
            error_code="TOOL_RUNTIME_FAILURE",
            error_message=(
                "O runtime encerrou a execução sem "
                "produzir um resultado válido."
            ),
            attempts=total_attempts,
            started_at=started_at,
        )

    def _execute_handler(
        self,
        handler: Any,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Executa um handler respeitando timeout.

        Cada tentativa utiliza um executor isolado.

        Em caso de timeout, o runtime deixa de aguardar
        o resultado e encerra a tentativa de forma
        fail-closed.
        """

        executor = ThreadPoolExecutor(
            max_workers=1
        )

        future = executor.submit(
            handler,
            request,
        )

        try:
            return future.result(
                timeout=request.timeout_seconds
            )

        except FutureTimeoutError:
            future.cancel()

            raise

        finally:
            executor.shutdown(
                wait=False,
                cancel_futures=True,
            )

    @staticmethod
    def _validate_result_binding(
        request: ToolRequest,
        result: Any,
    ) -> str | None:
        """
        Garante que o handler devolveu ToolResult
        pertencente exatamente à ToolRequest atual.

        Um handler não pode devolver resultado
        pertencente a outro agente, caso, execução
        ou ferramenta.
        """

        if not isinstance(result, ToolResult):
            return (
                "Handler retornou objeto diferente "
                "de ToolResult."
            )

        expected_fields = {
            "request_id": request.request_id,
            "execution_id": request.execution_id,
            "agent_id": request.agent_id,
            "case_id": request.case_id,
            "correlation_id": request.correlation_id,
            "tool_id": request.tool_id,
        }

        for field_name, expected_value in (
            expected_fields.items()
        ):
            actual_value = getattr(
                result,
                field_name,
                None,
            )

            if actual_value != expected_value:
                return (
                    "ToolResult não corresponde à "
                    "ToolRequest original: "
                    f"{field_name} esperado="
                    f"{expected_value!r}, "
                    f"recebido={actual_value!r}."
                )

        return None

    @staticmethod
    def _finalize_result(
        result: ToolResult,
        attempts: int,
        started_at: float,
    ) -> ToolResult:
        """
        Recria o ToolResult com métricas calculadas
        pelo runtime.

        O handler não controla attempts nem
        duration_ms finais.
        """

        duration_ms = max(
            0,
            int(
                (
                    perf_counter()
                    - started_at
                )
                * 1000
            ),
        )

        return ToolResult(
            request_id=result.request_id,
            execution_id=result.execution_id,
            agent_id=result.agent_id,
            case_id=result.case_id,
            correlation_id=result.correlation_id,
            tool_id=result.tool_id,
            status=result.status,
            success=result.success,
            output_payload=(
                result.output_payload
            ),
            evidence_payload=(
                result.evidence_payload
            ),
            error_code=result.error_code,
            error_message=result.error_message,
            attempts=attempts,
            duration_ms=duration_ms,
            completed_at=result.completed_at,
        )

    @staticmethod
    def _failure_result(
        request: ToolRequest,
        status: ToolExecutionStatus,
        error_code: str,
        error_message: str,
        attempts: int,
        started_at: float,
    ) -> ToolResult:
        """
        Cria um resultado de falha padronizado.
        """

        duration_ms = max(
            0,
            int(
                (
                    perf_counter()
                    - started_at
                )
                * 1000
            ),
        )

        return ToolResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=request.correlation_id,
            tool_id=request.tool_id,
            status=status,
            success=False,
            output_payload={},
            evidence_payload={},
            error_code=error_code,
            error_message=error_message,
            attempts=attempts,
            duration_ms=duration_ms,
        )