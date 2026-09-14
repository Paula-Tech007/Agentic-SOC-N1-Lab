"""
Autorização de chamadas de ferramentas
do Agentic SOC N1 Lab.

Fase 4.0 — Catálogo e Governança das Ferramentas.

Este módulo conecta:

- ToolRequest;
- catálogo oficial de ferramentas;
- allowlist por agente;
- limites operacionais.

Princípios:

- deny-by-default;
- least privilege;
- ferramenta não cadastrada é negada;
- agente não autorizado é negado;
- timeout solicitado não pode superar
  o limite oficial da ferramenta;
- retries solicitados não podem superar
  o limite oficial da ferramenta;
- nenhuma execução ocorre neste módulo.

Este módulo somente autoriza ou recusa
uma solicitação.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.permissions import (
    ToolDefinition,
    validate_tool_access,
)
from tools.contracts import ToolRequest


@dataclass(
    frozen=True,
    slots=True,
)
class ToolAuthorizationDecision:
    """
    Resultado imutável da autorização de
    uma ToolRequest.
    """

    allowed: bool
    agent_id: str
    tool_id: str
    reason: str
    definition: ToolDefinition | None = None


def authorize_tool_request(
    request: ToolRequest,
) -> ToolAuthorizationDecision:
    """
    Valida uma ToolRequest contra a política oficial.

    A função aplica:

    1. existência da ferramenta;
    2. allowlist do agente;
    3. limite de timeout;
    4. limite de retries.

    Nenhuma ferramenta é executada aqui.

    A autorização segue fail-closed:
    qualquer problema resulta em allowed=False.
    """

    try:
        definition = validate_tool_access(
            agent_id=request.agent_id,
            tool_id=request.tool_id,
        )

    except PermissionError as error:
        return ToolAuthorizationDecision(
            allowed=False,
            agent_id=request.agent_id,
            tool_id=request.tool_id,
            reason=str(error),
            definition=None,
        )

    if (
        request.timeout_seconds
        > definition.timeout_seconds
    ):
        return ToolAuthorizationDecision(
            allowed=False,
            agent_id=request.agent_id,
            tool_id=request.tool_id,
            reason=(
                "Timeout solicitado excede o limite "
                "oficial da ferramenta: "
                f"{request.timeout_seconds} > "
                f"{definition.timeout_seconds}."
            ),
            definition=definition,
        )

    if request.max_retries > definition.max_retries:
        return ToolAuthorizationDecision(
            allowed=False,
            agent_id=request.agent_id,
            tool_id=request.tool_id,
            reason=(
                "Quantidade de retries solicitada "
                "excede o limite oficial da ferramenta: "
                f"{request.max_retries} > "
                f"{definition.max_retries}."
            ),
            definition=definition,
        )

    return ToolAuthorizationDecision(
        allowed=True,
        agent_id=request.agent_id,
        tool_id=request.tool_id,
        reason="Solicitação autorizada pela política oficial.",
        definition=definition,
    )


def require_tool_authorization(
    request: ToolRequest,
) -> ToolDefinition:
    """
    Exige autorização para continuar.

    Quando permitido, retorna o ToolDefinition oficial.

    Quando negado, gera PermissionError.

    Esta função será utilizada futuramente pelo
    runtime de ferramentas imediatamente antes
    de qualquer integração externa.
    """

    decision = authorize_tool_request(request)

    if not decision.allowed:
        raise PermissionError(
            "ToolRequest recusada: "
            f"agent_id={request.agent_id!r}, "
            f"tool_id={request.tool_id!r}. "
            f"Motivo: {decision.reason}"
        )

    if decision.definition is None:
        raise PermissionError(
            "ToolRequest recusada por ausência "
            "de definição oficial da ferramenta."
        )

    return decision.definition