"""
Handlers oficiais das ferramentas MISP
do Agentic SOC N1 Lab.

Fase 4.1 — Threat Intelligence / MISP.

Este módulo conecta:

- ToolRequest;
- ToolRuntime;
- ToolRegistry;
- MISPClient.

Ferramentas implementadas:

- misp.search_ioc;
- misp.get_event;
- misp.get_attribute.

Princípios:

- somente operações read-only;
- tool_id precisa corresponder ao handler;
- payload obrigatório é validado;
- nenhuma API key aparece no resultado;
- nenhuma escrita é realizada;
- exceções do cliente são entregues ao
  ToolRuntime, que aplica retry e fail-closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from tools.registry import ToolRegistry
from tools.threat_intel.misp_client import (
    MISPClient,
)


class MISPToolHandlers:
    """
    Implementações das ferramentas MISP
    utilizadas pelo ToolRuntime.
    """

    SEARCH_IOC_TOOL_ID = "misp.search_ioc"

    GET_EVENT_TOOL_ID = "misp.get_event"

    GET_ATTRIBUTE_TOOL_ID = (
        "misp.get_attribute"
    )

    def __init__(
        self,
        client: MISPClient,
    ) -> None:
        """
        Inicializa os handlers com um
        MISPClient previamente configurado.
        """

        if not isinstance(
            client,
            MISPClient,
        ):
            raise TypeError(
                "client precisa ser uma "
                "instância de MISPClient."
            )

        self._client = client

    @property
    def client(
        self,
    ) -> MISPClient:
        """
        Retorna o cliente MISP utilizado
        pelos handlers.
        """

        return self._client

    def search_ioc(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        misp.search_ioc

        Payload esperado:

        {
            "ioc": "...",
            "limit": 50
        }

        limit é opcional.
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.SEARCH_IOC_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        ioc = self._require_string(
            payload=payload,
            field_name="ioc",
        )

        limit = payload.get(
            "limit",
            50,
        )

        if not isinstance(
            limit,
            int,
        ):
            raise ValueError(
                "Campo 'limit' precisa "
                "ser inteiro."
            )

        result = self._client.search_ioc(
            value=ioc,
            limit=limit,
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "ioc": ioc,
                    "limit": limit,
                },
                "result": result,
            },
            evidence_payload={
                "source": "MISP",
                "operation": "search_ioc",
                "ioc": ioc,
                "read_only": True,
            },
        )

    def get_event(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        misp.get_event

        Payload esperado:

        {
            "event_identifier": "..."
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_EVENT_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        event_identifier = (
            self._require_string(
                payload=payload,
                field_name=(
                    "event_identifier"
                ),
            )
        )

        result = self._client.get_event(
            event_identifier
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "event_identifier": (
                        event_identifier
                    ),
                },
                "result": result,
            },
            evidence_payload={
                "source": "MISP",
                "operation": "get_event",
                "event_identifier": (
                    event_identifier
                ),
                "read_only": True,
            },
        )

    def get_attribute(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        misp.get_attribute

        Payload esperado:

        {
            "attribute_identifier": "..."
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_ATTRIBUTE_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        attribute_identifier = (
            self._require_string(
                payload=payload,
                field_name=(
                    "attribute_identifier"
                ),
            )
        )

        result = (
            self._client.get_attribute(
                attribute_identifier
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "attribute_identifier": (
                        attribute_identifier
                    ),
                },
                "result": result,
            },
            evidence_payload={
                "source": "MISP",
                "operation": "get_attribute",
                "attribute_identifier": (
                    attribute_identifier
                ),
                "read_only": True,
            },
        )

    def register(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Registra as três implementações MISP
        no ToolRegistry oficial.
        """

        if not isinstance(
            registry,
            ToolRegistry,
        ):
            raise TypeError(
                "registry precisa ser uma "
                "instância de ToolRegistry."
            )

        registry.register(
            self.SEARCH_IOC_TOOL_ID,
            self.search_ioc,
        )

        registry.register(
            self.GET_EVENT_TOOL_ID,
            self.get_event,
        )

        registry.register(
            self.GET_ATTRIBUTE_TOOL_ID,
            self.get_attribute,
        )

    @staticmethod
    def _validate_request(
        *,
        request: ToolRequest,
        expected_tool_id: str,
    ) -> None:
        """
        Garante que o handler recebeu
        exatamente a ferramenta esperada.
        """

        if not isinstance(
            request,
            ToolRequest,
        ):
            raise TypeError(
                "request precisa ser "
                "uma ToolRequest."
            )

        if (
            request.tool_id
            != expected_tool_id
        ):
            raise ValueError(
                "ToolRequest entregue ao "
                "handler incorreto: "
                f"esperado={expected_tool_id!r}, "
                f"recebido={request.tool_id!r}."
            )

    @staticmethod
    def _payload_dict(
        request: ToolRequest,
    ) -> dict[str, Any]:
        """
        Converte input_payload para
        dicionário de leitura local.
        """

        payload = (
            request.input_payload.to_dict()
        )

        if not isinstance(
            payload,
            Mapping,
        ):
            raise ValueError(
                "input_payload inválido."
            )

        return dict(payload)

    @staticmethod
    def _require_string(
        *,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> str:
        """
        Recupera um campo textual obrigatório.
        """

        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"Campo obrigatório "
                f"{field_name!r} precisa "
                "ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"Campo obrigatório "
                f"{field_name!r} não pode "
                "ser vazio."
            )

        return normalized

    @staticmethod
    def _success_result(
        *,
        request: ToolRequest,
        output_payload: Mapping[str, Any],
        evidence_payload: Mapping[str, Any],
    ) -> ToolResult:
        """
        Cria ToolResult de sucesso
        vinculado exatamente à ToolRequest.
        """

        return ToolResult(
            request_id=request.request_id,
            execution_id=request.execution_id,
            agent_id=request.agent_id,
            case_id=request.case_id,
            correlation_id=(
                request.correlation_id
            ),
            tool_id=request.tool_id,
            status=(
                ToolExecutionStatus.COMPLETED
            ),
            success=True,
            output_payload=dict(
                output_payload
            ),
            evidence_payload=dict(
                evidence_payload
            ),
        )