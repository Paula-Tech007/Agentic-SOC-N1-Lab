"""
Cliente HTTP read-only da integração Asset / CMDB
do Agentic SOC N1 Lab.

Fase 4.4 — Asset / CMDB read-only.

Operações disponibilizadas:

- get_asset;
- get_ip_context;
- get_criticality;
- get_edr_status.

Princípios de segurança:

- somente HTTP GET;
- nenhuma operação de escrita;
- nenhuma alteração de inventário;
- nenhuma alteração de criticidade;
- nenhuma ação de contenção;
- nenhuma ação real sobre EDR;
- nenhuma credencial em logs ou resultados;
- redirects desabilitados;
- proxy de ambiente desabilitado;
- endpoints validados antes da chamada;
- fail-closed para rotas ou métodos não autorizados.

Princípio do projeto:

A ferramenta comprova.
O agente estrutura.
"""

from __future__ import annotations

from collections.abc import Mapping
from ipaddress import ip_address
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from tools.asset.asset_config import (
    AssetConfig,
)


class AssetClientError(RuntimeError):
    """
    Erro base da integração Asset / CMDB.
    """


class AssetConnectionError(
    AssetClientError
):
    """
    Falha de conexão com o serviço Asset / CMDB.
    """


class AssetTimeoutError(
    AssetClientError
):
    """
    Timeout durante consulta Asset / CMDB.
    """


class AssetHTTPError(
    AssetClientError
):
    """
    Resposta HTTP não bem-sucedida.
    """


class AssetResponseError(
    AssetClientError
):
    """
    Resposta Asset / CMDB inválida ou inesperada.
    """


class AssetClient:
    """
    Cliente HTTP defensivo e estritamente
    read-only para consultas de ativos.
    """

    GET_ASSET_OPERATION = (
        "get_asset"
    )

    GET_IP_CONTEXT_OPERATION = (
        "get_ip_context"
    )

    GET_CRITICALITY_OPERATION = (
        "get_criticality"
    )

    GET_EDR_STATUS_OPERATION = (
        "get_edr_status"
    )

    def __init__(
        self,
        config: AssetConfig,
        *,
        transport: (
            httpx.BaseTransport
            | None
        ) = None,
    ) -> None:
        """
        Inicializa o cliente Asset / CMDB.

        transport é opcional e permite
        httpx.MockTransport nos testes.
        """

        if not isinstance(
            config,
            AssetConfig,
        ):
            raise TypeError(
                "config precisa ser uma "
                "instância de AssetConfig."
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
    ) -> AssetConfig:
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
    ) -> "AssetClient":
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

    def get_asset(
        self,
        asset_id: str,
    ) -> dict[str, Any]:
        """
        Consulta informações gerais de um ativo.

        Endpoint lógico:

        GET /assets/{asset_id}
        """

        normalized_asset_id = (
            self._normalize_asset_id(
                asset_id
            )
        )

        encoded_asset_id = quote(
            normalized_asset_id,
            safe="",
        )

        path = (
            f"/assets/{encoded_asset_id}"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_ASSET_OPERATION
            ),
            identifier=normalized_asset_id,
        )

    def get_ip_context(
        self,
        ip_value: str,
    ) -> dict[str, Any]:
        """
        Consulta o contexto de ativo associado
        a um endereço IP interno.

        Endpoint lógico:

        GET /assets/by-ip/{ip}
        """

        normalized_ip = (
            self._normalize_ip(
                ip_value
            )
        )

        encoded_ip = quote(
            normalized_ip,
            safe="",
        )

        path = (
            f"/assets/by-ip/{encoded_ip}"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_IP_CONTEXT_OPERATION
            ),
            identifier=normalized_ip,
        )

    def get_criticality(
        self,
        asset_id: str,
    ) -> dict[str, Any]:
        """
        Consulta a criticidade registrada
        para um ativo.

        Endpoint lógico:

        GET /assets/{asset_id}/criticality
        """

        normalized_asset_id = (
            self._normalize_asset_id(
                asset_id
            )
        )

        encoded_asset_id = quote(
            normalized_asset_id,
            safe="",
        )

        path = (
            f"/assets/{encoded_asset_id}"
            "/criticality"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_CRITICALITY_OPERATION
            ),
            identifier=normalized_asset_id,
        )

    def get_edr_status(
        self,
        asset_id: str,
    ) -> dict[str, Any]:
        """
        Consulta somente o estado registrado
        do EDR associado ao ativo.

        Nenhuma ação é executada sobre o EDR.

        Endpoint lógico:

        GET /assets/{asset_id}/edr
        """

        normalized_asset_id = (
            self._normalize_asset_id(
                asset_id
            )
        )

        encoded_asset_id = quote(
            normalized_asset_id,
            safe="",
        )

        path = (
            f"/assets/{encoded_asset_id}"
            "/edr"
        )

        return self._request_json(
            method="GET",
            path=path,
            operation=(
                self.GET_EDR_STATUS_OPERATION
            ),
            identifier=normalized_asset_id,
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        operation: str,
        identifier: str,
    ) -> dict[str, Any]:
        """
        Executa uma chamada Asset / CMDB após
        validar método, rota e operação.
        """

        self._validate_request_shape(
            method=method,
            path=path,
            operation=operation,
            identifier=identifier,
        )

        try:
            response = self._client.request(
                method=method,
                url=path,
            )

        except httpx.TimeoutException as exc:
            raise AssetTimeoutError(
                "Timeout durante consulta Asset / CMDB."
            ) from exc

        except httpx.RequestError as exc:
            raise AssetConnectionError(
                "Falha de conexão durante "
                "consulta Asset / CMDB."
            ) from exc

        if not (
            200
            <= response.status_code
            < 300
        ):
            raise AssetHTTPError(
                "Asset / CMDB retornou status HTTP "
                f"{response.status_code}."
            )

        try:
            payload = response.json()

        except ValueError as exc:
            raise AssetResponseError(
                "Asset / CMDB retornou conteúdo "
                "que não é JSON válido."
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise AssetResponseError(
                "Asset / CMDB precisa retornar "
                "um objeto JSON."
            )

        return dict(payload)

    def _validate_request_shape(
        self,
        *,
        method: str,
        path: str,
        operation: str,
        identifier: str,
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
                "AssetClient permite somente "
                "operações HTTP GET."
            )

        if operation not in (
            self._config.allowed_operations
        ):
            raise PermissionError(
                "Operação Asset / CMDB "
                "não autorizada: "
                f"{operation!r}."
            )

        if operation == (
            self.GET_IP_CONTEXT_OPERATION
        ):
            normalized_identifier = (
                self._normalize_ip(
                    identifier
                )
            )

            encoded_identifier = quote(
                normalized_identifier,
                safe="",
            )

            expected_paths = {
                self.GET_IP_CONTEXT_OPERATION: (
                    f"/assets/by-ip/"
                    f"{encoded_identifier}"
                ),
            }

        else:
            normalized_identifier = (
                self._normalize_asset_id(
                    identifier
                )
            )

            encoded_identifier = quote(
                normalized_identifier,
                safe="",
            )

            expected_paths = {
                self.GET_ASSET_OPERATION: (
                    f"/assets/{encoded_identifier}"
                ),
                self.GET_CRITICALITY_OPERATION: (
                    f"/assets/{encoded_identifier}"
                    "/criticality"
                ),
                self.GET_EDR_STATUS_OPERATION: (
                    f"/assets/{encoded_identifier}"
                    "/edr"
                ),
            }

        expected_path = (
            expected_paths.get(
                operation
            )
        )

        if expected_path is None:
            raise PermissionError(
                "Operação Asset / CMDB sem rota "
                "read-only autorizada."
            )

        normalized_path = (
            self._normalize_path(
                path
            )
        )

        if normalized_path != expected_path:
            raise PermissionError(
                "Rota Asset / CMDB não autorizada "
                f"para a operação {operation!r}."
            )

    @staticmethod
    def _normalize_asset_id(
        value: str,
    ) -> str:
        """
        Normaliza identificador de ativo.

        O asset_id é tratado como um único
        segmento de URL e será percent-encoded.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "asset_id precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "asset_id não pode ser vazio."
            )

        if len(normalized) > 256:
            raise ValueError(
                "asset_id não pode possuir "
                "mais de 256 caracteres."
            )

        if any(
            ord(character) < 32
            or ord(character) == 127
            for character in normalized
        ):
            raise ValueError(
                "asset_id contém caractere "
                "de controle inválido."
            )

        return normalized

    @staticmethod
    def _normalize_ip(
        value: str,
    ) -> str:
        """
        Valida e normaliza endereço IPv4 ou IPv6.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "ip_value precisa ser string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "ip_value não pode ser vazio."
            )

        try:
            parsed_ip = ip_address(
                normalized
            )

        except ValueError as exc:
            raise ValueError(
                "ip_value precisa ser um endereço "
                "IPv4 ou IPv6 válido."
            ) from exc

        return str(
            parsed_ip
        )

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
                "AssetClient não aceita "
                "URLs absolutas internas."
            )

        if parsed.query:
            raise PermissionError(
                "Rotas Asset / CMDB não podem conter "
                "query string nesta fase."
            )

        if parsed.fragment:
            raise PermissionError(
                "Rotas Asset / CMDB não podem conter "
                "fragmento."
            )

        if not normalized.startswith("/"):
            raise PermissionError(
                "Rota Asset / CMDB precisa ser relativa "
                "à URL base configurada."
            )

        return normalized

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna descrição segura
        do cliente Asset / CMDB.

        Nenhum token é exposto.
        """

        return {
            "integration": "ASSET",
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