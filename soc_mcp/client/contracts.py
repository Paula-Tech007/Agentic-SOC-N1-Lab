"""
Contratos do cliente MCP local
do Agentic SOC N1 Lab.

Fase 6.1 — Cliente/uso controlado do MCP.

Este módulo define somente contratos
pertencentes à camada cliente.

Ele NÃO substitui os contratos internos
já existentes em:

    soc_mcp.contracts

Em especial, permanecem oficiais:

- MCPToolCallRequest;
- MCPToolCallResult;
- MCPToolDescriptor;
- MCPCallStatus.

Responsabilidades desta camada:

- representar uma tool apresentada
  pelo servidor ao cliente;
- representar os argumentos funcionais
  enviados pelo cliente para uma tool;
- manter estruturas imutáveis;
- impedir que o cliente escolha
  contexto de segurança.

O cliente NÃO possui campos para:

- agent_id;
- case_id;
- correlation_id.

Esses valores continuam vinculados
ao MCPServer pelo create_mcp_server().

Princípios:

- local-only;
- read-only;
- deny-by-default;
- fail-closed;
- payload imutável;
- nenhuma ação crítica autônoma;
- ToolRuntime permanece soberano.

Princípio central:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from types import (
    MappingProxyType,
)
from typing import (
    Any,
    Mapping,
)


def _required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Valida e normaliza
    uma string obrigatória.
    """

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(
            f"{field_name} não pode "
            "ser vazio."
        )

    return cleaned


def _optional_string(
    value: object,
    *,
    field_name: str,
) -> str | None:
    """
    Valida e normaliza
    uma string opcional.
    """

    if value is None:
        return None

    return _required_string(
        value,
        field_name=field_name,
    )


def _freeze_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, Any]:
    """
    Valida um mapping e retorna
    uma cópia imutável.

    A cópia evita que alterações
    posteriores no objeto original
    modifiquem o contrato.
    """

    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(
            f"{field_name} precisa "
            "ser um mapping."
        )

    copied: dict[str, Any] = {}

    for key, item in value.items():
        if not isinstance(
            key,
            str,
        ):
            raise ValueError(
                f"{field_name} precisa "
                "possuir somente chaves string."
            )

        cleaned_key = key.strip()

        if not cleaned_key:
            raise ValueError(
                f"{field_name} não pode "
                "possuir chave vazia."
            )

        copied[cleaned_key] = item

    return MappingProxyType(
        copied
    )


@dataclass(
    frozen=True,
    slots=True,
)
class MCPClientToolDescriptor:
    """
    Descrição de uma tool que foi
    apresentada pelo MCPServer
    ao cliente local.

    A existência deste objeto não concede
    autorização por conta própria.

    A autorização continua sendo definida
    pelo servidor, registry e ToolRuntime.
    """

    tool_id: str

    title: str | None = None

    description: str | None = None

    input_schema: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida e congela
        os dados da tool.
        """

        object.__setattr__(
            self,
            "tool_id",
            _required_string(
                self.tool_id,
                field_name="tool_id",
            ),
        )

        object.__setattr__(
            self,
            "title",
            _optional_string(
                self.title,
                field_name="title",
            ),
        )

        object.__setattr__(
            self,
            "description",
            _optional_string(
                self.description,
                field_name="description",
            ),
        )

        object.__setattr__(
            self,
            "input_schema",
            _freeze_mapping(
                self.input_schema,
                field_name=(
                    "input_schema"
                ),
            ),
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna apenas metadados
        seguros da tool.
        """

        return {
            "tool_id": self.tool_id,
            "title": self.title,
            "has_description": bool(
                self.description
            ),
            "input_schema_keys": tuple(
                self.input_schema.keys()
            ),
        }


@dataclass(
    frozen=True,
    slots=True,
)
class MCPClientToolCallRequest:
    """
    Solicitação funcional feita
    pelo cliente MCP local.

    Este contrato contém somente:

    - identificação da tool;
    - argumentos funcionais.

    Deliberadamente NÃO contém:

    - agent_id;
    - case_id;
    - correlation_id.

    O contexto de segurança continua
    vinculado ao servidor MCP.
    """

    tool_id: str

    arguments: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(
        self,
    ) -> None:
        """
        Valida e congela
        a solicitação do cliente.
        """

        object.__setattr__(
            self,
            "tool_id",
            _required_string(
                self.tool_id,
                field_name="tool_id",
            ),
        )

        object.__setattr__(
            self,
            "arguments",
            _freeze_mapping(
                self.arguments,
                field_name="arguments",
            ),
        )

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro
        sem expor valores dos argumentos.
        """

        return {
            "tool_id": self.tool_id,
            "argument_keys": tuple(
                self.arguments.keys()
            ),
        }


__all__ = [
    "MCPClientToolCallRequest",
    "MCPClientToolDescriptor",
]