"""
Cliente HTTP read-only do Elastic / Elasticsearch
para o Agentic SOC N1 Lab.

Fase 4.2 — Elastic / Elasticsearch.

Responsabilidades:

- pesquisar alertas;
- pesquisar eventos;
- consultar documento específico;
- limitar consultas aos índices autorizados;
- aplicar timeout;
- respeitar validação SSL;
- nunca expor a API key;
- operar de forma fail-closed.

IMPORTANTE:

POST /_search é utilizado exclusivamente
como operação de leitura.

Este cliente não implementa:

- indexação de documentos;
- atualização;
- exclusão;
- bulk;
- criação ou exclusão de índices;
- alteração de mappings;
- alteração de configurações;
- operações administrativas.
"""

from __future__ import annotations

from collections.abc import Mapping
from fnmatch import fnmatchcase
from typing import Any
from urllib.parse import quote

import httpx

from tools.elastic.elastic_config import (
    ElasticConfig,
)


class ElasticClientError(RuntimeError):
    """
    Erro base seguro da integração Elastic.
    """


class ElasticConnectionError(
    ElasticClientError
):
    """
    Falha de comunicação com o Elastic.
    """


class ElasticTimeoutError(
    ElasticClientError
):
    """
    Timeout durante consulta ao Elastic.
    """


class ElasticHTTPError(
    ElasticClientError
):
    """
    Elastic respondeu com status HTTP inválido.
    """


class ElasticResponseError(
    ElasticClientError
):
    """
    Resposta do Elastic possui formato inválido.
    """


JSONResponse = (
    dict[str, Any]
    | list[Any]
)


class ElasticClient:
    """
    Cliente defensivo e read-only do Elastic.

    Operações públicas permitidas:

    - search_alerts;
    - search_events;
    - get_document.
    """

    def __init__(
        self,
        config: ElasticConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """
        Inicializa o cliente.

        transport é opcional e será usado
        nos testes com httpx.MockTransport,
        sem conexão externa.
        """

        if not isinstance(
            config,
            ElasticConfig,
        ):
            raise TypeError(
                "config precisa ser uma "
                "instância de ElasticConfig."
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
    ) -> ElasticConfig:
        """
        Retorna a configuração atual.
        """

        return self._config

    def search_alerts(
        self,
        query: Mapping[str, Any],
        *,
        size: int = 50,
    ) -> JSONResponse:
        """
        Pesquisa alertas no índice autorizado.

        Utiliza somente:

        POST /<alerts-index>/_search
        """

        body = self._build_search_body(
            query=query,
            size=size,
        )

        path = self._search_path(
            self._config.alerts_index
        )

        return self._request_json(
            method="POST",
            path=path,
            payload=body,
            allowed_index=(
                self._config.alerts_index
            ),
            operation="search",
        )

    def search_events(
        self,
        query: Mapping[str, Any],
        *,
        size: int = 100,
    ) -> JSONResponse:
        """
        Pesquisa eventos no índice autorizado.

        Utiliza somente:

        POST /<events-index>/_search
        """

        body = self._build_search_body(
            query=query,
            size=size,
        )

        path = self._search_path(
            self._config.events_index
        )

        return self._request_json(
            method="POST",
            path=path,
            payload=body,
            allowed_index=(
                self._config.events_index
            ),
            operation="search",
        )

    def get_document(
        self,
        *,
        index: str,
        document_id: str,
    ) -> JSONResponse:
        """
        Consulta um documento específico.

        O índice concreto informado precisa
        corresponder a um dos padrões de índice
        autorizados na configuração.

        Exemplo:

        padrão autorizado:
            alerts-*

        índice concreto permitido:
            alerts-2026.09.15
        """

        normalized_index = (
            self._normalize_concrete_index(
                index
            )
        )

        self._validate_concrete_index_allowed(
            normalized_index
        )

        normalized_document_id = (
            self._normalize_document_id(
                document_id
            )
        )

        encoded_index = quote(
            normalized_index,
            safe="-_.",
        )

        encoded_document_id = quote(
            normalized_document_id,
            safe="",
        )

        path = (
            f"/{encoded_index}"
            f"/_doc/"
            f"{encoded_document_id}"
        )

        return self._request_json(
            method="GET",
            path=path,
            allowed_index=(
                normalized_index
            ),
            operation="get_document",
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        allowed_index: str,
        operation: str,
        payload: dict[str, Any] | None = None,
    ) -> JSONResponse:
        """
        Executa somente uma requisição
        previamente autorizada pelo cliente.

        Qualquer método ou endpoint fora
        dos contratos read-only é recusado.
        """

        normalized_method = (
            method.strip().upper()
        )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        self._validate_request_shape(
            method=normalized_method,
            path=normalized_path,
            allowed_index=allowed_index,
            operation=operation,
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
                raise PermissionError(
                    "Método HTTP não autorizado "
                    "para integração Elastic."
                )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise ElasticTimeoutError(
                "Timeout durante consulta "
                "read-only ao Elastic."
            ) from error

        except httpx.HTTPStatusError as error:
            raise ElasticHTTPError(
                "Elastic retornou status HTTP "
                f"{error.response.status_code}."
            ) from error

        except httpx.RequestError as error:
            raise ElasticConnectionError(
                "Falha de comunicação "
                "com o Elastic."
            ) from error

        finally:
            client.close()

        try:
            result = response.json()

        except ValueError as error:
            raise ElasticResponseError(
                "Elastic retornou conteúdo "
                "que não é JSON válido."
            ) from error

        if not isinstance(
            result,
            (
                dict,
                list,
            ),
        ):
            raise ElasticResponseError(
                "Elastic retornou estrutura JSON "
                "não suportada."
            )

        return result

    def _build_client(
        self,
    ) -> httpx.Client:
        """
        Cria cliente HTTP seguro.

        follow_redirects=False:
        evita envio automático de Authorization
        para destino diferente.

        trust_env=False:
        evita uso silencioso de proxies
        configurados no ambiente.
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

    @staticmethod
    def _build_search_body(
        *,
        query: Mapping[str, Any],
        size: int,
    ) -> dict[str, Any]:
        """
        Monta corpo de consulta _search.

        O chamador fornece apenas a cláusula
        query. O cliente controla size.
        """

        if not isinstance(
            query,
            Mapping,
        ):
            raise TypeError(
                "query precisa ser mapping."
            )

        if not query:
            raise ValueError(
                "query não pode ser vazia."
            )

        if not isinstance(
            size,
            int,
        ):
            raise TypeError(
                "size precisa ser inteiro."
            )

        if not 1 <= size <= 1000:
            raise ValueError(
                "size precisa estar "
                "entre 1 e 1000."
            )

        return {
            "size": size,
            "query": dict(query),
        }

    @staticmethod
    def _search_path(
        index_pattern: str,
    ) -> str:
        """
        Monta caminho seguro do endpoint _search.

        O caractere * é preservado porque
        padrões de índice são permitidos
        somente para pesquisa read-only.
        """

        encoded_index = quote(
            index_pattern,
            safe="-_.*,"
        )

        return (
            f"/{encoded_index}/_search"
        )

    def _validate_concrete_index_allowed(
        self,
        index: str,
    ) -> None:
        """
        Verifica se um índice concreto pertence
        a um dos padrões autorizados.
        """

        if any(
            fnmatchcase(
                index,
                pattern,
            )
            for pattern
            in self._config.allowed_indices
        ):
            return

        raise PermissionError(
            "Índice não autorizado "
            "para consulta: "
            f"{index!r}."
        )

    @staticmethod
    def _normalize_concrete_index(
        value: str,
    ) -> str:
        """
        Normaliza índice concreto usado
        no get_document.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "index precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "index não pode ser vazio."
            )

        if "*" in normalized:
            raise ValueError(
                "get_document exige "
                "um índice concreto, "
                "sem wildcard."
            )

        if len(normalized) > 255:
            raise ValueError(
                "index excede o tamanho "
                "máximo permitido."
            )

        forbidden_fragments = (
            "/",
            "\\",
            "..",
            "?",
            "#",
        )

        if any(
            fragment in normalized
            for fragment
            in forbidden_fragments
        ):
            raise ValueError(
                "index contém caracteres "
                "não permitidos."
            )

        return normalized

    @staticmethod
    def _normalize_document_id(
        value: str,
    ) -> str:
        """
        Normaliza ID de documento.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "document_id precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "document_id não pode ser vazio."
            )

        if len(normalized) > 512:
            raise ValueError(
                "document_id excede "
                "o tamanho máximo permitido."
            )

        return normalized

    @staticmethod
    def _normalize_path(
        path: str,
    ) -> str:
        """
        Normaliza caminho interno.
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
                "em chamadas internas do Elastic."
            )

        return normalized

    def _validate_request_shape(
        self,
        *,
        method: str,
        path: str,
        allowed_index: str,
        operation: str,
    ) -> None:
        """
        Allowlist final de método + endpoint.

        Fail-closed:
        tudo que não corresponder exatamente
        aos contratos read-only é bloqueado.
        """

        if operation == "search":
            if method != "POST":
                raise PermissionError(
                    "Pesquisa Elastic aceita "
                    "somente POST read-only."
                )

            expected_path = (
                self._search_path(
                    allowed_index
                )
            )

            if path != expected_path:
                raise PermissionError(
                    "Endpoint de pesquisa Elastic "
                    "não autorizado."
                )

            return

        if operation == "get_document":
            if method != "GET":
                raise PermissionError(
                    "Consulta de documento aceita "
                    "somente GET."
                )

            normalized_index = (
                self._normalize_concrete_index(
                    allowed_index
                )
            )

            self._validate_concrete_index_allowed(
                normalized_index
            )

            encoded_index = quote(
                normalized_index,
                safe="-_.",
            )

            expected_prefix = (
                f"/{encoded_index}/_doc/"
            )

            if not path.startswith(
                expected_prefix
            ):
                raise PermissionError(
                    "Endpoint de documento Elastic "
                    "não autorizado."
                )

            document_part = path[
                len(expected_prefix):
            ]

            if not document_part:
                raise PermissionError(
                    "Consulta de documento sem ID "
                    "não é autorizada."
                )

            return

        raise PermissionError(
            "Operação Elastic não autorizada: "
            f"{operation!r}."
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna informações seguras
        sobre o cliente.

        Nunca inclui a API key.
        """

        return {
            "integration": "ELASTIC",
            "mode": "READ_ONLY",
            "base_url": (
                self._config.base_url
            ),
            "alerts_index": (
                self._config.alerts_index
            ),
            "events_index": (
                self._config.events_index
            ),
            "verify_ssl": (
                self._config.verify_ssl
            ),
            "timeout_seconds": (
                self._config.timeout_seconds
            ),
            "allowed_operations": (
                "search_alerts",
                "search_events",
                "get_document",
            ),
        }