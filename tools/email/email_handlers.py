"""
Handlers oficiais das ferramentas Email / Phishing
do Agentic SOC N1 Lab.

Fase 4.5 — Email / Phishing Metadata Read-Only.

Este módulo conecta:

- ToolRequest;
- ToolRuntime;
- ToolRegistry;
- EmailClient.

Ferramentas implementadas:

- email.get_message_metadata;
- email.get_headers;
- email.get_authentication_results;
- email.get_attachment_metadata.

Princípios:

- somente operações read-only;
- tool_id precisa corresponder ao handler;
- message_id é obrigatório;
- nenhuma URL presente na mensagem é aberta;
- nenhum anexo é baixado;
- nenhum anexo é executado;
- nenhuma credencial aparece no resultado;
- nenhuma operação de escrita é disponibilizada;
- exceções do EmailClient são entregues ao
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
from tools.email.email_client import (
    EmailClient,
)
from tools.registry import ToolRegistry


class EmailToolHandlers:
    """
    Implementações oficiais das ferramentas
    Email / Phishing utilizadas pelo ToolRuntime.
    """

    GET_MESSAGE_METADATA_TOOL_ID = (
        "email.get_message_metadata"
    )

    GET_HEADERS_TOOL_ID = (
        "email.get_headers"
    )

    GET_AUTHENTICATION_RESULTS_TOOL_ID = (
        "email.get_authentication_results"
    )

    GET_ATTACHMENT_METADATA_TOOL_ID = (
        "email.get_attachment_metadata"
    )

    def __init__(
        self,
        client: EmailClient,
    ) -> None:
        """
        Inicializa os handlers com um
        EmailClient previamente configurado.
        """

        if not isinstance(
            client,
            EmailClient,
        ):
            raise TypeError(
                "client precisa ser uma "
                "instância de EmailClient."
            )

        self._client = client

    @property
    def client(
        self,
    ) -> EmailClient:
        """
        Retorna o cliente Email / Phishing
        utilizado pelos handlers.
        """

        return self._client

    def get_message_metadata(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        email.get_message_metadata

        Payload esperado:

        {
            "message_id": "MSG-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_MESSAGE_METADATA_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        message_id = self._require_string(
            payload=payload,
            field_name="message_id",
        )

        result = (
            self._client
            .get_message_metadata(
                message_id=message_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "message_id": message_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "EMAIL",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_message_metadata"
                ),
                "message_id": message_id,
                "read_only": True,
                "opens_urls": False,
                "downloads_attachments": False,
                "executes_attachments": False,
            },
        )

    def get_headers(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        email.get_headers

        Payload esperado:

        {
            "message_id": "MSG-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_HEADERS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        message_id = self._require_string(
            payload=payload,
            field_name="message_id",
        )

        result = (
            self._client
            .get_headers(
                message_id=message_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "message_id": message_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "EMAIL",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": "get_headers",
                "message_id": message_id,
                "read_only": True,
                "opens_urls": False,
                "downloads_attachments": False,
                "executes_attachments": False,
            },
        )

    def get_authentication_results(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        email.get_authentication_results

        Payload esperado:

        {
            "message_id": "MSG-0001"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self
                .GET_AUTHENTICATION_RESULTS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        message_id = self._require_string(
            payload=payload,
            field_name="message_id",
        )

        result = (
            self._client
            .get_authentication_results(
                message_id=message_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "message_id": message_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "EMAIL",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_authentication_results"
                ),
                "message_id": message_id,
                "read_only": True,
                "opens_urls": False,
                "downloads_attachments": False,
                "executes_attachments": False,
            },
        )

    def get_attachment_metadata(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        email.get_attachment_metadata

        Payload esperado:

        {
            "message_id": "MSG-0001"
        }

        Somente metadados são consultados.
        O conteúdo binário do anexo não é baixado.
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_ATTACHMENT_METADATA_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        message_id = self._require_string(
            payload=payload,
            field_name="message_id",
        )

        result = (
            self._client
            .get_attachment_metadata(
                message_id=message_id
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "message_id": message_id,
                },
                "result": result,
            },
            evidence_payload={
                "source": "EMAIL",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_attachment_metadata"
                ),
                "message_id": message_id,
                "read_only": True,
                "opens_urls": False,
                "downloads_attachments": False,
                "executes_attachments": False,
            },
        )

    def register(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Registra as quatro implementações
        Email / Phishing no ToolRegistry oficial.
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
            self.GET_MESSAGE_METADATA_TOOL_ID,
            self.get_message_metadata,
        )

        registry.register(
            self.GET_HEADERS_TOOL_ID,
            self.get_headers,
        )

        registry.register(
            self.GET_AUTHENTICATION_RESULTS_TOOL_ID,
            self.get_authentication_results,
        )

        registry.register(
            self.GET_ATTACHMENT_METADATA_TOOL_ID,
            self.get_attachment_metadata,
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