"""
Handlers oficiais das ferramentas Identity / IAM
do Agentic SOC N1 Lab.

Fase 4.3 — Identity / IAM read-only.

Este módulo conecta:

- ToolRequest;
- ToolRuntime;
- ToolRegistry;
- IdentityClient.

Ferramentas implementadas:

- iam.get_user;
- iam.get_account_status;
- iam.get_mfa_status;
- iam.get_group_membership.

Princípios:

- somente operações read-only;
- tool_id precisa corresponder ao handler;
- username é obrigatório;
- nenhuma credencial aparece no resultado;
- nenhuma operação de escrita é disponibilizada;
- exceções do IdentityClient são entregues ao
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
from tools.identity.identity_client import (
    IdentityClient,
)
from tools.registry import ToolRegistry


class IdentityToolHandlers:
    """
    Implementações oficiais das ferramentas IAM
    utilizadas pelo ToolRuntime.
    """

    GET_USER_TOOL_ID = (
        "iam.get_user"
    )

    GET_ACCOUNT_STATUS_TOOL_ID = (
        "iam.get_account_status"
    )

    GET_MFA_STATUS_TOOL_ID = (
        "iam.get_mfa_status"
    )

    GET_GROUP_MEMBERSHIP_TOOL_ID = (
        "iam.get_group_membership"
    )

    def __init__(
        self,
        client: IdentityClient,
    ) -> None:
        """
        Inicializa os handlers com um
        IdentityClient previamente configurado.
        """

        if not isinstance(
            client,
            IdentityClient,
        ):
            raise TypeError(
                "client precisa ser uma "
                "instância de IdentityClient."
            )

        self._client = client

    @property
    def client(
        self,
    ) -> IdentityClient:
        """
        Retorna o cliente IAM utilizado
        pelos handlers.
        """

        return self._client

    def get_user(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        iam.get_user

        Payload esperado:

        {
            "username": "lab.user"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_USER_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        username = self._require_string(
            payload=payload,
            field_name="username",
        )

        result = self._client.get_user(
            username=username
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "username": username,
                },
                "result": result,
            },
            evidence_payload={
                "source": "IAM",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": "get_user",
                "username": username,
                "read_only": True,
            },
        )

    def get_account_status(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        iam.get_account_status

        Payload esperado:

        {
            "username": "lab.user"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_ACCOUNT_STATUS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        username = self._require_string(
            payload=payload,
            field_name="username",
        )

        result = (
            self._client
            .get_account_status(
                username=username
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "username": username,
                },
                "result": result,
            },
            evidence_payload={
                "source": "IAM",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_account_status"
                ),
                "username": username,
                "read_only": True,
            },
        )

    def get_mfa_status(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        iam.get_mfa_status

        Payload esperado:

        {
            "username": "lab.user"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_MFA_STATUS_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        username = self._require_string(
            payload=payload,
            field_name="username",
        )

        result = (
            self._client
            .get_mfa_status(
                username=username
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "username": username,
                },
                "result": result,
            },
            evidence_payload={
                "source": "IAM",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_mfa_status"
                ),
                "username": username,
                "read_only": True,
            },
        )

    def get_group_membership(
        self,
        request: ToolRequest,
    ) -> ToolResult:
        """
        Implementa:

        iam.get_group_membership

        Payload esperado:

        {
            "username": "lab.user"
        }
        """

        self._validate_request(
            request=request,
            expected_tool_id=(
                self.GET_GROUP_MEMBERSHIP_TOOL_ID
            ),
        )

        payload = self._payload_dict(
            request
        )

        username = self._require_string(
            payload=payload,
            field_name="username",
        )

        result = (
            self._client
            .get_group_membership(
                username=username
            )
        )

        return self._success_result(
            request=request,
            output_payload={
                "query": {
                    "username": username,
                },
                "result": result,
            },
            evidence_payload={
                "source": "IAM",
                "provider": (
                    self._client
                    .config
                    .provider
                ),
                "operation": (
                    "get_group_membership"
                ),
                "username": username,
                "read_only": True,
            },
        )

    def register(
        self,
        registry: ToolRegistry,
    ) -> None:
        """
        Registra as quatro implementações IAM
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
            self.GET_USER_TOOL_ID,
            self.get_user,
        )

        registry.register(
            self.GET_ACCOUNT_STATUS_TOOL_ID,
            self.get_account_status,
        )

        registry.register(
            self.GET_MFA_STATUS_TOOL_ID,
            self.get_mfa_status,
        )

        registry.register(
            self.GET_GROUP_MEMBERSHIP_TOOL_ID,
            self.get_group_membership,
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