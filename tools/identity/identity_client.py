"""
Cliente HTTP read-only da integração Identity / IAM
do Agentic SOC N1 Lab.

Fase 4.3 — Identity / IAM read-only.

Operações disponibilizadas:

- get_user;
- get_account_status;
- get_mfa_status;
- get_group_membership.

Princípios de segurança:

- somente HTTP GET;
- nenhuma operação de escrita;
- nenhuma alteração de conta;
- nenhuma alteração de senha;
- nenhuma alteração de grupos;
- nenhuma credencial em logs ou resultados;
- redirects desabilitados;
- proxy de ambiente desabilitado;
- endpoints validados antes da chamada;
- fail-closed para rotas ou métodos não autorizados.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from tools.identity.identity_config import (
    IdentityConfig,
)


class IdentityClientError(RuntimeError):
    """
    Erro base da integração Identity / IAM.
    """


class IdentityConnectionError(
    IdentityClientError
):
    """
    Falha de conexão com o serviço IAM.
    """


class IdentityTimeoutError(
    IdentityClientError
):
    """
    Timeout durante consulta IAM.
    """


class IdentityHTTPError(
    IdentityClientError
):
    """
    Resposta HTTP não bem-sucedida.
    """


class IdentityResponseError(
    IdentityClientError
):
    """
    Resposta IAM inválida ou inesperada.
    """


class IdentityClient:
    """
    Cliente HTTP defensivo e estritamente
    read-only para consultas de identidade.
    """

    GET_USER_OPERATION = "get_user"

    GET_ACCOUNT_STATUS_OPERATION = (
        "get_account_status"
    )

    GET_MFA_STATUS_OPERATION = (
        "get_mfa_status"
    )

    GET_GROUP_MEMBERSHIP_OPERATION = (
        "get_group_membership"
    )

    def __init__(
        self,
        config: IdentityConfig,
        *,
        transport: (
            httpx.BaseTransport
            | httpx.AsyncBaseTransport
            | None
        ) = None,
    ) -> None:
        """
        Inicializa o cliente IAM.

        transport é opcional e permite
        httpx.MockTransport nos testes.
        """

        if not isinstance(
            config,
            IdentityConfig,
        ):
            raise TypeError(
                "config precisa ser uma "
                "instância de IdentityConfig."
            )

        self._config = config

        self._client = httpx.Client(
            base_url=config.base_url,
            headers=(
                config.authorization_headers
            ),
            timeout=config.timeout_seconds,
            verify=config.verify_ssl,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    @property
    def config(
        self,
    ) -> IdentityConfig:
        """
        Retorna a configuração utilizada
        pelo cliente.
        """

        return self._config

    def close(
        self,
    ) -> None:
        """
        Fecha o cliente HTTP interno.
        """

        self._client.close()

    def __enter__(
        self,
    ) -> "IdentityClient":
        """
        Permite uso com context manager.
        """

        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        """
        Fecha o cliente ao sair do contexto.
        """

        self.close()

    def get_user(
        self,
        username: str,
    ) -> dict[str, Any]:
        """
        Consulta informações básicas
        de uma identidade.

        Endpoint lógico:

        GET /users/{username}
        """

        normalized_username = (
            self._normalize_username(
                username
            )
        )

        encoded_username = quote(
            normalized_username,
            safe="",
        )

        path = (
            f"/users/{encoded_username}"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_USER_OPERATION
            ),
            username=normalized_username,
        )

    def get_account_status(
        self,
        username: str,
    ) -> dict[str, Any]:
        """
        Consulta o estado defensivo
        da conta.

        Endpoint lógico:

        GET /users/{username}/status
        """

        normalized_username = (
            self._normalize_username(
                username
            )
        )

        encoded_username = quote(
            normalized_username,
            safe="",
        )

        path = (
            f"/users/{encoded_username}"
            "/status"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_ACCOUNT_STATUS_OPERATION
            ),
            username=normalized_username,
        )

    def get_mfa_status(
        self,
        username: str,
    ) -> dict[str, Any]:
        """
        Consulta o estado de MFA
        da identidade.

        Endpoint lógico:

        GET /users/{username}/mfa
        """

        normalized_username = (
            self._normalize_username(
                username
            )
        )

        encoded_username = quote(
            normalized_username,
            safe="",
        )

        path = (
            f"/users/{encoded_username}"
            "/mfa"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_MFA_STATUS_OPERATION
            ),
            username=normalized_username,
        )

    def get_group_membership(
        self,
        username: str,
    ) -> dict[str, Any]:
        """
        Consulta grupos e privilégios
        associados à identidade.

        Endpoint lógico:

        GET /users/{username}/groups
        """

        normalized_username = (
            self._normalize_username(
                username
            )
        )

        encoded_username = quote(
            normalized_username,
            safe="",
        )

        path = (
            f"/users/{encoded_username}"
            "/groups"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_GROUP_MEMBERSHIP_OPERATION
            ),
            username=normalized_username,
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        operation: str,
        username: str,
    ) -> dict[str, Any]:
        """
        Executa uma chamada IAM após
        validar método, rota e operação.
        """

        self._validate_request_shape(
            method=method,
            path=path,
            operation=operation,
            username=username,
        )

        try:
            response = self._client.request(
                method=method,
                url=path,
            )

        except httpx.TimeoutException as exc:
            raise IdentityTimeoutError(
                "Timeout durante consulta IAM."
            ) from exc

        except httpx.RequestError as exc:
            raise IdentityConnectionError(
                "Falha de conexão durante "
                "consulta IAM."
            ) from exc

        if not (
            200
            <= response.status_code
            < 300
        ):
            raise IdentityHTTPError(
                "IAM retornou status HTTP "
                f"{response.status_code}."
            )

        try:
            payload = response.json()

        except ValueError as exc:
            raise IdentityResponseError(
                "IAM retornou conteúdo que "
                "não é JSON válido."
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise IdentityResponseError(
                "IAM precisa retornar "
                "um objeto JSON."
            )

        return dict(payload)

    def _validate_request_shape(
        self,
        *,
        method: str,
        path: str,
        operation: str,
        username: str,
    ) -> None:
        """
        Valida a chamada antes de qualquer
        comunicação HTTP.

        Somente quatro rotas GET oficiais
        são aceitas.
        """

        if not isinstance(
            method,
            str,
        ):
            raise TypeError(
                "method precisa ser string."
            )

        normalized_method = (
            method.strip().upper()
        )

        if normalized_method != "GET":
            raise PermissionError(
                "IdentityClient permite "
                "somente operações HTTP GET."
            )

        if operation not in (
            self._config.allowed_operations
        ):
            raise PermissionError(
                "Operação IAM não autorizada: "
                f"{operation!r}."
            )

        normalized_username = (
            self._normalize_username(
                username
            )
        )

        encoded_username = quote(
            normalized_username,
            safe="",
        )

        expected_paths = {
            self.GET_USER_OPERATION: (
                f"/users/{encoded_username}"
            ),
            self.GET_ACCOUNT_STATUS_OPERATION: (
                f"/users/{encoded_username}"
                "/status"
            ),
            self.GET_MFA_STATUS_OPERATION: (
                f"/users/{encoded_username}"
                "/mfa"
            ),
            self.GET_GROUP_MEMBERSHIP_OPERATION: (
                f"/users/{encoded_username}"
                "/groups"
            ),
        }

        expected_path = (
            expected_paths.get(
                operation
            )
        )

        if expected_path is None:
            raise PermissionError(
                "Operação IAM sem rota "
                "read-only autorizada."
            )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        if normalized_path != expected_path:
            raise PermissionError(
                "Rota IAM não autorizada para "
                f"a operação {operation!r}."
            )

    @staticmethod
    def _normalize_username(
        value: str,
    ) -> str:
        """
        Normaliza identificador de usuário.

        O username é tratado como um único
        segmento de URL e será percent-encoded.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "username precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "username não pode ser vazio."
            )

        if len(normalized) > 256:
            raise ValueError(
                "username não pode possuir "
                "mais de 256 caracteres."
            )

        if any(
            ord(character) < 32
            or ord(character) == 127
            for character in normalized
        ):
            raise ValueError(
                "username contém caractere "
                "de controle inválido."
            )

        return normalized

    @staticmethod
    def _normalize_path(
        value: str,
    ) -> str:
        """
        Valida uma rota HTTP relativa interna.

        URLs absolutas são proibidas.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "path precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "path não pode ser vazio."
            )

        parsed = urlparse(
            normalized
        )

        if (
            parsed.scheme
            or parsed.netloc
        ):
            raise PermissionError(
                "IdentityClient não aceita "
                "URLs absolutas internas."
            )

        if parsed.query:
            raise PermissionError(
                "Rotas IAM não podem conter "
                "query string nesta fase."
            )

        if parsed.fragment:
            raise PermissionError(
                "Rotas IAM não podem conter "
                "fragmento."
            )

        if not normalized.startswith("/"):
            raise PermissionError(
                "Rota IAM precisa ser relativa "
                "à URL base configurada."
            )

        return normalized

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna descrição segura
        do cliente IAM.

        Nenhum token é exposto.
        """

        return {
            "integration": "IAM",
            "provider": (
                self._config.provider
            ),
            "base_url": (
                self._config.base_url
            ),
            "access_mode": "READ_ONLY",
            "http_methods": (
                "GET",
            ),
            "operations": (
                self._config
                .allowed_operations
            ),
        }