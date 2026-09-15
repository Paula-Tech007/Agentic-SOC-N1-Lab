"""
Handlers oficiais das ferramentas Elastic / Elasticsearch
do Agentic SOC N1 Lab.

Fase 4.2 — Elastic / Elasticsearch read-only.

Este módulo conecta:

- ToolRequest;
- ToolRuntime;
- ToolRegistry;
- ElasticClient.

Ferramentas implementadas:

- elastic.search_alerts;
- elastic.search_events;
- elastic.get_document.

Princípios:

- somente operações read-only;
- tool_id precisa corresponder ao handler;
- payloads são validados antes da execução;
- nenhuma API key aparece no resultado;
- nenhuma operação de escrita é disponibilizada;
- exceções do ElasticClient são entregues ao
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
from tools.elastic.elastic_client import (
    ElasticClient,
)
from tools.registry import ToolRegistry


class ElasticToolHandlers:
    """
    Implementações oficiais das ferramentas Elastic
    utilizadas pelo ToolRuntime.
    """

    SEARCH_ALERTS_TOOL_ID = (
        "elastic.search_alerts"
    )

    SEARCH_EVENTS_TOOL_ID = (
        "elastic.search_events"
    )

    GET_DOCUMENT_TOOL_ID = (
        "elastic.get_document"
    )

    def __init__(
        self,
        client: ElasticClient,
    ) -> None:
        """
        Inicializa os handlers com um
        ElasticClient previamente configurado.
        """

        if not isinstance(
            client,
            ElasticClient,
        ):
            raise TypeError(
                "client precisa ser uma "
                "instância de ElasticClient."
            )

        self._client = client

    @property
    def client(
        self,
    ) -> ElasticClient:
        """
        Retorna o cliente Elastic utilizado
        pelos handlers.
        """

        return self._client

    def search_alerts(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        elastic.search_alerts

        Payload esperado:

        {
            "query": {
                ...
            },
            "size": 50
        }

        size é opcional.
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.SEARCH_ALERTS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        query = self._require_mapping(
            payload=payload,
            field_name="query",
        )

        size = payload.get(
            "size",
            50,
        )

        if not isinstance(
            size,
            int,
        ):
            raise ValueError(
                "Campo 'size' precisa "
                "ser inteiro."
            )

        result = self._client.search_alerts(
            query=query,
            size=size,
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "query": dict(query),
                    "size": size,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ELASTIC",
                "operation": "search_alerts",
                "index_pattern": (
                    self._client
                    .config
                    .alerts_index
                ),
                "read_only": True,
            },
        )

    def search_events(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        elastic.search_events

        Payload esperado:

        {
            "query": {
                ...
            },
            "size": 100
        }

        size é opcional.
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.SEARCH_EVENTS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        query = self._require_mapping(
            payload=payload,
            field_name="query",
        )

        size = payload.get(
            "size",
            100,
        )

        if not isinstance(
            size,
            int,
        ):
            raise ValueError(
                "Campo 'size' precisa "
                "ser inteiro."
            )

        result = self._client.search_events(
            query=query,
            size=size,
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "query": dict(query),
                    "size": size,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ELASTIC",
                "operation": "search_events",
                "index_pattern": (
                    self._client
                    .config
                    .events_index
                ),
                "read_only": True,
            },
        )

    def get_document(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        elastic.get_document

        Payload esperado:

        {
            "index": "alerts-2026.09.15",
            "document_id": "ALT-001"
        }

        O índice precisa ser concreto e pertencer
        aos padrões permitidos pelo ElasticConfig.
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_DOCUMENT_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        index = self._require_string(
            payload=payload,
            field_name="index",
        )

        document_id = self._require_string(
            payload=payload,
            field_name="document_id",
        )

        result = self._client.get_document(
            index=index,
            document_id=document_id,
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "index": index,
                    "document_id": document_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ELASTIC",
                "operation": "get_document",
                "index": index,
                "document_id": document_id,
                "read_only": True,
            },
        )

    def register(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Registra as três implementações Elastic
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
            self.SEARCH_ALERTS_TOOL_ID,
            self.search_alerts,
        )

        registry.register(
            self.SEARCH_EVENTS_TOOL_ID,
            self.search_events,
        )

        registry.register(
            self.GET_DOCUMENT_TOOL_ID,
            self.get_document,
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
        dicionário local de leitura.
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
    def _require_mapping(
        *,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> dict[str, Any]:
        """
        Recupera um campo mapping obrigatório.
        """

        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            Mapping,
        ):
            raise ValueError(
                f"Campo obrigatório "
                f"{field_name!r} precisa "
                "ser mapping."
            )

        if not value:
            raise ValueError(
                f"Campo obrigatório "
                f"{field_name!r} não pode "
                "ser vazio."
            )

        return dict(value)

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