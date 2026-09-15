"""
Handlers oficiais das ferramentas Asset / CMDB
do Agentic SOC N1 Lab.

Fase 4.4 — Asset / CMDB read-only.

Este módulo conecta:

- ToolRequest;
- ToolRuntime;
- ToolRegistry;
- AssetClient.

Ferramentas implementadas:

- asset.get_asset;
- asset.get_ip_context;
- asset.get_criticality;
- asset.get_edr_status.

Princípios:

- somente operações read-only;
- tool_id precisa corresponder ao handler;
- asset_id ou ip_address são obrigatórios conforme
  a operação;
- nenhuma credencial aparece no resultado;
- nenhuma operação de escrita é disponibilizada;
- nenhuma ação real sobre EDR é executada;
- exceções do AssetClient são entregues ao
  ToolRuntime, que aplica retry e fail-closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tools.asset.asset_client import (
    AssetClient,
)
from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
    ToolResult,
)
from tools.registry import ToolRegistry


class AssetToolHandlers:
    """
    Implementações oficiais das ferramentas Asset / CMDB
    utilizadas pelo ToolRuntime.
    """

    GET_ASSET_TOOL_ID = (
        "asset.get_asset"
    )

    GET_IP_CONTEXT_TOOL_ID = (
        "asset.get_ip_context"
    )

    GET_CRITICALITY_TOOL_ID = (
        "asset.get_criticality"
    )

    GET_EDR_STATUS_TOOL_ID = (
        "asset.get_edr_status"
    )

    def __init__(
        self,
        client: AssetClient,
    ) -> None:
        """
        Inicializa os handlers com um
        AssetClient previamente configurado.
        """

        if not isinstance(
            client,
            AssetClient,
        ):
            raise TypeError(
                "client precisa ser uma "
                "instância de AssetClient."
            )

        self._client = client

    @property
    def client(
        self,
    ) -> AssetClient:
        """
        Retorna o cliente Asset / CMDB utilizado
        pelos handlers.
        """

        return self._client

    def get_asset(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        asset.get_asset

        Payload esperado:

        {
            "asset_id": "ASSET-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_ASSET_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        asset_id = self._require_string(
            payload=payload,
            field_name="asset_id",
        )

        result = self._client.get_asset(
            asset_id=asset_id
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "asset_id": asset_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ASSET",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": "get_asset",
                "asset_id": asset_id,
                "read_only": True,
            },
        )

    def get_ip_context(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        asset.get_ip_context

        Payload esperado:

        {
            "ip_address": "10.20.30.15"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_IP_CONTEXT_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        ip_address = self._require_string(
            payload=payload,
            field_name="ip_address",
        )

        result = self._client.get_ip_context(
            ip_value=ip_address
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "ip_address": ip_address,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ASSET",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_ip_context"
                ),
                "ip_address": ip_address,
                "read_only": True,
            },
        )

    def get_criticality(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        asset.get_criticality

        Payload esperado:

        {
            "asset_id": "ASSET-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_CRITICALITY_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        asset_id = self._require_string(
            payload=payload,
            field_name="asset_id",
        )

        result = (
            self._client
            .get_criticality(
                asset_id=asset_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "asset_id": asset_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ASSET",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_criticality"
                ),
                "asset_id": asset_id,
                "read_only": True,
            },
        )

    def get_edr_status(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        asset.get_edr_status

        Payload esperado:

        {
            "asset_id": "ASSET-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_EDR_STATUS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        asset_id = self._require_string(
            payload=payload,
            field_name="asset_id",
        )

        result = (
            self._client
            .get_edr_status(
                asset_id=asset_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "asset_id": asset_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "ASSET",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_edr_status"
                ),
                "asset_id": asset_id,
                "read_only": True,
            },
        )

    def register(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Registra as quatro implementações Asset / CMDB
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
            self.GET_ASSET_TOOL_ID,
            self.get_asset,
        )

        registry.register(
            self.GET_IP_CONTEXT_TOOL_ID,
            self.get_ip_context,
        )

        registry.register(
            self.GET_CRITICALITY_TOOL_ID,
            self.get_criticality,
        )

        registry.register(
            self.GET_EDR_STATUS_TOOL_ID,
            self.get_edr_status,
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

        return dict(
            payload
        )

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