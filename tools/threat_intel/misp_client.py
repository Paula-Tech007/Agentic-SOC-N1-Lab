"""
Cliente HTTP read-only do MISP
para o Agentic SOC N1 Lab.

Fase 4.1 — Threat Intelligence / MISP.

Responsabilidades:

- pesquisar IOC no MISP;
- consultar evento existente;
- consultar atributo existente;
- utilizar somente endpoints autorizados;
- aplicar timeout;
- respeitar validação SSL;
- nunca registrar ou expor a API key;
- operar de forma fail-closed.

IMPORTANTE:

O endpoint attributes/restSearch utiliza POST,
mas é tratado aqui exclusivamente como operação
de consulta read-only.

Este cliente não implementa:

- criação de eventos;
- alteração de eventos;
- exclusão de eventos;
- criação de atributos;
- alteração de atributos;
- exclusão de atributos;
- publicação;
- tagging;
- qualquer ação de escrita.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from tools.threat_intel.misp_config import (
    MISPConfig,
)


class MISPClientError(RuntimeError):
    """
    Erro base seguro da integração MISP.
    """


class MISPConnectionError(MISPClientError):
    """
    Falha de conexão com o MISP.
    """


class MISPTimeoutError(MISPClientError):
    """
    Timeout durante uma consulta ao MISP.
    """


class MISPHTTPError(MISPClientError):
    """
    Resposta HTTP inválida recebida do MISP.
    """


class MISPResponseError(MISPClientError):
    """
    Resposta do MISP não possui formato esperado.
    """


JSONResponse = (
    dict[str, Any]
    | list[Any]
)


class MISPClient:
    """
    Cliente defensivo e read-only da API MISP.

    Somente três operações são permitidas:

    - search_ioc;
    - get_event;
    - get_attribute.

    Nenhum método de escrita é disponibilizado.
    """

    _ALLOWED_GET_PATH_PREFIXES = (
        "/events/",
        "/attributes/",
    )

    _ALLOWED_POST_PATHS = frozenset(
        {
            "/attributes/restSearch",
        }
    )

    def __init__(
        self,
        config: MISPConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """
        Inicializa o cliente.

        transport é opcional e será utilizado
        posteriormente pelos testes automatizados
        para simular respostas sem acessar
        um MISP real.
        """

        if not isinstance(
            config,
            MISPConfig,
        ):
            raise TypeError(
                "config precisa ser uma "
                "instância de MISPConfig."
            )

        if (
            transport is not None
            and not isinstance(
                transport,
                httpx.BaseTransport,
            )
        ):
            raise TypeError(
                "transport precisa ser "
                "httpx.BaseTransport ou None."
            )

        self._config = config

        self._transport = transport

    @property
    def config(
        self,
    ) -> MISPConfig:
        """
        Retorna a configuração atual.
        """

        return self._config

    def search_ioc(
        self,
        value: str,
        *,
        limit: int = 50,
    ) -> JSONResponse:
        """
        Pesquisa um IOC no MISP.

        Utiliza:

        POST /attributes/restSearch

        O uso de POST neste endpoint é somente
        para pesquisa e não modifica o MISP.
        """

        normalized_value = (
            self._normalize_search_value(
                value
            )
        )

        if not isinstance(
            limit,
            int,
        ):
            raise TypeError(
                "limit precisa ser inteiro."
            )

        if not 1 <= limit <= 1000:
            raise ValueError(
                "limit precisa estar "
                "entre 1 e 1000."
            )

        payload = {
            "returnFormat": "json",
            "value": normalized_value,
            "limit": limit,
            "includeEventUuid": True,
        }

        return self._request_json(
            method="POST",
            path="/attributes/restSearch",
            payload=payload,
        )

    def get_event(
        self,
        event_identifier: str,
    ) -> JSONResponse:
        """
        Consulta um evento existente.

        event_identifier pode representar
        um ID ou UUID previamente conhecido.
        """

        identifier = (
            self._normalize_identifier(
                event_identifier,
                field_name="event_identifier",
            )
        )

        encoded_identifier = quote(
            identifier,
            safe="",
        )

        return self._request_json(
            method="GET",
            path=(
                f"/events/"
                f"{encoded_identifier}"
            ),
        )

    def get_attribute(
        self,
        attribute_identifier: str,
    ) -> JSONResponse:
        """
        Consulta um atributo existente.

        attribute_identifier pode representar
        um ID ou UUID previamente conhecido.
        """

        identifier = (
            self._normalize_identifier(
                attribute_identifier,
                field_name=(
                    "attribute_identifier"
                ),
            )
        )

        encoded_identifier = quote(
            identifier,
            safe="",
        )

        return self._request_json(
            method="GET",
            path=(
                f"/attributes/"
                f"{encoded_identifier}"
            ),
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """
        Executa uma requisição permitida
        e devolve JSON.

        Antes da execução:

        - valida método;
        - valida endpoint;
        - aplica configuração segura.

        Qualquer endpoint fora da allowlist
        é bloqueado antes da chamada HTTP.
        """

        normalized_method = (
            method.strip().upper()
        )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        self._validate_endpoint(
            method=normalized_method,
            path=normalized_path,
        )

        client = self._build_client()

        try:
            if normalized_method == "GET":
                response = client.get(
                    normalized_path
                )

            elif normalized_method == "POST":
                response = client.post(
                    normalized_path,
                    json=payload or {},
                )

            else:
                raise MISPClientError(
                    "Método HTTP não autorizado."
                )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise MISPTimeoutError(
                "Timeout durante consulta "
                "read-only ao MISP."
            ) from error

        except httpx.HTTPStatusError as error:
            raise MISPHTTPError(
                "MISP retornou status HTTP "
                f"{error.response.status_code}."
            ) from error

        except httpx.RequestError as error:
            raise MISPConnectionError(
                "Falha de comunicação com o MISP."
            ) from error

        finally:
            client.close()

        try:
            result = response.json()

        except ValueError as error:
            raise MISPResponseError(
                "MISP retornou conteúdo "
                "que não é JSON válido."
            ) from error

        if not isinstance(
            result,
            (
                dict,
                list,
            ),
        ):
            raise MISPResponseError(
                "MISP retornou estrutura JSON "
                "não suportada."
            )

        return result

    def _build_client(
        self,
    ) -> httpx.Client:
        """
        Cria um httpx.Client seguro.

        follow_redirects=False reduz o risco
        de encaminhar Authorization para
        destino inesperado.

        trust_env=False evita uso silencioso
        de proxies definidos no ambiente.
        """

        return httpx.Client(
            base_url=self._config.base_url,
            headers=(
                self._config
                .authorization_headers
            ),
            timeout=httpx.Timeout(
                self._config.timeout_seconds
            ),
            verify=self._config.verify_ssl,
            follow_redirects=False,
            trust_env=False,
            transport=self._transport,
        )

    @classmethod
    def _validate_endpoint(
        cls,
        *,
        method: str,
        path: str,
    ) -> None:
        """
        Aplica allowlist de método + endpoint.

        Fail-closed:
        qualquer rota não autorizada é recusada.
        """

        if method == "POST":
            if path not in cls._ALLOWED_POST_PATHS:
                raise PermissionError(
                    "Endpoint POST não autorizado "
                    "para integração MISP: "
                    f"{path!r}."
                )

            return

        if method == "GET":
            if not any(
                path.startswith(prefix)
                for prefix
                in cls._ALLOWED_GET_PATH_PREFIXES
            ):
                raise PermissionError(
                    "Endpoint GET não autorizado "
                    "para integração MISP: "
                    f"{path!r}."
                )

            if path in {
                "/events/",
                "/attributes/",
            }:
                raise PermissionError(
                    "Consulta MISP sem identificador "
                    "não é autorizada."
                )

            return

        raise PermissionError(
            "Método HTTP não autorizado "
            "para integração MISP: "
            f"{method!r}."
        )

    @staticmethod
    def _normalize_path(
        path: str,
    ) -> str:
        """
        Normaliza um caminho interno da API.
        """

        if not isinstance(
            path,
            str,
        ):
            raise TypeError(
                "path precisa ser string."
            )

        normalized = path.strip()

        if not normalized:
            raise ValueError(
                "path não pode ser vazio."
            )

        if not normalized.startswith("/"):
            normalized = (
                "/"
                + normalized
            )

        if "://" in normalized:
            raise PermissionError(
                "URL absoluta não é permitida "
                "em chamadas internas do MISP."
            )

        return normalized

    @staticmethod
    def _normalize_search_value(
        value: str,
    ) -> str:
        """
        Normaliza o valor usado na pesquisa
        de IOC.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "IOC precisa ser uma string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "IOC não pode ser vazio."
            )

        if len(normalized) > 4096:
            raise ValueError(
                "IOC excede o tamanho máximo "
                "permitido."
            )

        return normalized

    @staticmethod
    def _normalize_identifier(
        value: str,
        *,
        field_name: str,
    ) -> str:
        """
        Normaliza identificadores usados
        em rotas GET.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} precisa "
                "ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} não pode "
                "ser vazio."
            )

        if len(normalized) > 200:
            raise ValueError(
                f"{field_name} excede "
                "o tamanho máximo permitido."
            )

        return normalized

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Informações seguras sobre o cliente.

        Nenhuma API key é retornada.
        """

        return {
            "integration": "MISP",
            "mode": "READ_ONLY",
            "base_url": (
                self._config.base_url
            ),
            "verify_ssl": (
                self._config.verify_ssl
            ),
            "timeout_seconds": (
                self._config.timeout_seconds
            ),
            "allowed_operations": (
                "search_ioc",
                "get_event",
                "get_attribute",
            ),
        }