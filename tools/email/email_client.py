"""
Cliente HTTP defensivo da integração Email / Phishing.

Fase 4.5 — Email / Phishing Metadata Read-Only.

Operações oficiais:

- get_message_metadata;
- get_headers;
- get_authentication_results;
- get_attachment_metadata.

Princípios de segurança:

- somente método HTTP GET;
- somente rotas explicitamente autorizadas;
- nenhuma URL externa arbitrária;
- nenhuma query string;
- nenhum fragment;
- nenhuma abertura de URL presente no e-mail;
- nenhum download de anexo;
- nenhuma execução de anexo;
- nenhuma alteração de mensagem;
- nenhuma ação crítica.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from tools.email.email_config import (
    EmailConfig,
)


class EmailClientError(RuntimeError):
    """
    Erro base da integração Email / Phishing.
    """


class EmailConnectionError(
    EmailClientError
):
    """
    Falha de conexão com o provedor.
    """


class EmailTimeoutError(
    EmailClientError
):
    """
    Timeout durante consulta defensiva.
    """


class EmailHTTPError(
    EmailClientError
):
    """
    Resposta HTTP não bem-sucedida.
    """


class EmailResponseError(
    EmailClientError
):
    """
    Resposta inválida recebida do provedor.
    """


class EmailClient:
    """
    Cliente HTTP somente leitura para Email / Phishing.

    Este cliente não acessa links presentes nas mensagens
    e não recupera o conteúdo binário de anexos.
    """

    GET_MESSAGE_METADATA = (
        "get_message_metadata"
    )

    GET_HEADERS = (
        "get_headers"
    )

    GET_AUTHENTICATION_RESULTS = (
        "get_authentication_results"
    )

    GET_ATTACHMENT_METADATA = (
        "get_attachment_metadata"
    )

    def __init__(
        self,
        config: EmailConfig,
        *,
        transport: (
            httpx.BaseTransport
            | None
        ) = None,
    ) -> None:
        """
        Inicializa cliente HTTP controlado.
        """

        if not isinstance(
            config,
            EmailConfig,
        ):
            raise TypeError(
                "config precisa ser EmailConfig."
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
    ) -> EmailConfig:
        """
        Retorna configuração imutável do cliente.
        """

        return self._config

    def __enter__(
        self,
    ) -> "EmailClient":
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
        Fecha o cliente ao sair do context manager.
        """

        self.close()

    def close(
        self,
    ) -> None:
        """
        Fecha conexões HTTP.
        """

        self._client.close()

    def get_message_metadata(
        self,
        message_id: str,
    ) -> Mapping[str, Any]:
        """
        Consulta somente metadados da mensagem.

        Não retorna corpo executável e não segue links.
        """

        normalized_message_id = (
            self._normalize_message_id(
                message_id
            )
        )

        path = (
            "/messages/"
            f"{quote(normalized_message_id, safe='')}"
            "/metadata"
        )

        return self._request_json(
            operation=(
                self.GET_MESSAGE_METADATA
            ),
            path=path,
            expected_path=path,
        )

    def get_headers(
        self,
        message_id: str,
    ) -> Mapping[str, Any]:
        """
        Consulta cabeçalhos técnicos da mensagem.
        """

        normalized_message_id = (
            self._normalize_message_id(
                message_id
            )
        )

        path = (
            "/messages/"
            f"{quote(normalized_message_id, safe='')}"
            "/headers"
        )

        return self._request_json(
            operation=self.GET_HEADERS,
            path=path,
            expected_path=path,
        )

    def get_authentication_results(
        self,
        message_id: str,
    ) -> Mapping[str, Any]:
        """
        Consulta resultados SPF, DKIM e DMARC
        já disponíveis para a mensagem.
        """

        normalized_message_id = (
            self._normalize_message_id(
                message_id
            )
        )

        path = (
            "/messages/"
            f"{quote(normalized_message_id, safe='')}"
            "/authentication-results"
        )

        return self._request_json(
            operation=(
                self.GET_AUTHENTICATION_RESULTS
            ),
            path=path,
            expected_path=path,
        )

    def get_attachment_metadata(
        self,
        message_id: str,
    ) -> Mapping[str, Any]:
        """
        Consulta somente metadados dos anexos.

        O conteúdo binário dos anexos não é baixado.
        """

        normalized_message_id = (
            self._normalize_message_id(
                message_id
            )
        )

        path = (
            "/messages/"
            f"{quote(normalized_message_id, safe='')}"
            "/attachments/metadata"
        )

        return self._request_json(
            operation=(
                self.GET_ATTACHMENT_METADATA
            ),
            path=path,
            expected_path=path,
        )

    def _request_json(
        self,
        *,
        operation: str,
        path: str,
        expected_path: str,
    ) -> Mapping[str, Any]:
        """
        Executa uma requisição GET autorizada
        e exige resposta JSON em formato de objeto.
        """

        self._validate_request_shape(
            method="GET",
            operation=operation,
            path=path,
            expected_path=expected_path,
        )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        try:
            response = self._client.request(
                method="GET",
                url=normalized_path,
            )

        except httpx.TimeoutException as exc:
            raise EmailTimeoutError(
                "Timeout ao consultar Email / Phishing."
            ) from exc

        except httpx.RequestError as exc:
            raise EmailConnectionError(
                "Falha de conexão com Email / Phishing."
            ) from exc

        if (
            response.status_code < 200
            or response.status_code >= 300
        ):
            raise EmailHTTPError(
                "Email / Phishing retornou "
                f"status HTTP {response.status_code}."
            )

        try:
            payload = response.json()

        except ValueError as exc:
            raise EmailResponseError(
                "Email / Phishing retornou "
                "conteúdo que não é JSON válido."
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise EmailResponseError(
                "Email / Phishing precisa retornar "
                "um objeto JSON."
            )

        return payload

    def _validate_request_shape(
        self,
        *,
        method: str,
        operation: str,
        path: str,
        expected_path: str,
    ) -> None:
        """
        Aplica allowlist estrita de método,
        operação e rota.
        """

        if not isinstance(
            method,
            str,
        ):
            raise PermissionError(
                "Método HTTP inválido."
            )

        normalized_method = (
            method.strip().upper()
        )

        if normalized_method != "GET":
            raise PermissionError(
                "Integração Email / Phishing "
                "permite somente HTTP GET."
            )

        if operation not in (
            self._config.allowed_operations
        ):
            raise PermissionError(
                "Operação não autorizada "
                "para Email / Phishing."
            )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        normalized_expected_path = (
            self._normalize_path(
                expected_path
            )
        )

        if (
            normalized_path
            != normalized_expected_path
        ):
            raise PermissionError(
                "Rota não autorizada "
                "para Email / Phishing."
            )

    @staticmethod
    def _normalize_message_id(
        value: str,
    ) -> str:
        """
        Valida identificador de mensagem.
        """

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "message_id precisa ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "message_id não pode ser vazio."
            )

        if len(cleaned) > 512:
            raise ValueError(
                "message_id excede o tamanho permitido."
            )

        if any(
            ord(character) < 32
            or ord(character) == 127
            for character in cleaned
        ):
            raise ValueError(
                "message_id contém caractere "
                "de controle inválido."
            )

        return cleaned

    @staticmethod
    def _normalize_path(
        value: str,
    ) -> str:
        """
        Valida caminho HTTP interno.

        URLs absolutas, query strings e fragments
        são bloqueados.
        """

        if not isinstance(
            value,
            str,
        ):
            raise PermissionError(
                "Rota precisa ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise PermissionError(
                "Rota não pode ser vazia."
            )

        parsed = urlparse(
            cleaned
        )

        if (
            parsed.scheme
            or parsed.netloc
        ):
            raise PermissionError(
                "URL externa não é permitida."
            )

        if parsed.query:
            raise PermissionError(
                "Query string não é permitida."
            )

        if parsed.fragment:
            raise PermissionError(
                "Fragment não é permitido."
            )

        if not cleaned.startswith("/"):
            raise PermissionError(
                "Rota interna precisa iniciar com '/'."
            )

        return cleaned

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro do cliente.
        """

        return {
            "integration": "EMAIL",
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
                self._config.allowed_operations
            ),
            "downloads_attachments": False,
            "opens_urls": False,
            "executes_attachments": False,
        }