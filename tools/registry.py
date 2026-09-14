"""
Registro oficial de ferramentas
do Agentic SOC N1 Lab.

Fase 4.0 — Catálogo e Governança das Ferramentas.

Este módulo mantém a relação entre:

- tool_id oficial;
- implementação Python correspondente.

Princípios:

- somente ferramentas existentes no catálogo oficial
  podem ser registradas;
- ferramenta desconhecida é recusada;
- registros duplicados são recusados;
- handlers precisam ser chamáveis;
- o registro não decide autorização por agente;
- autorização continua sendo responsabilidade
  da camada core.permissions;
- nenhuma integração externa é executada neste módulo.

Fluxo futuro:

ToolRequest
    ↓
Tool Authorization
    ↓
Tool Registry
    ↓
Tool Runtime
    ↓
Integração autorizada
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from core.permissions import get_tool_definition
from tools.contracts import (
    ToolRequest,
    ToolResult,
)


ToolHandler = Callable[
    [ToolRequest],
    ToolResult,
]


class ToolRegistry:
    """
    Registro em memória das implementações
    de ferramentas disponíveis.

    O ToolRegistry não concede permissão.

    Ele apenas responde:

    "Existe uma implementação registrada
    para esta ferramenta?"
    """

    def __init__(self) -> None:
        """
        Inicializa um registro vazio.
        """

        self._handlers: dict[
            str,
            ToolHandler,
        ] = {}

    def register(
        self,
        tool_id: str,
        handler: ToolHandler,
    ) -> None:
        """
        Registra uma implementação de ferramenta.

        Regras:

        - tool_id precisa ser string não vazia;
        - ferramenta precisa existir no catálogo oficial;
        - handler precisa ser callable;
        - registros duplicados são recusados.
        """

        if not isinstance(tool_id, str):
            raise TypeError(
                "tool_id precisa ser uma string."
            )

        normalized_tool_id = tool_id.strip()

        if not normalized_tool_id:
            raise ValueError(
                "tool_id não pode ser vazio."
            )

        definition = get_tool_definition(
            normalized_tool_id
        )

        if definition is None:
            raise ValueError(
                "Não é possível registrar ferramenta "
                "fora do catálogo oficial: "
                f"{normalized_tool_id!r}."
            )

        if not callable(handler):
            raise TypeError(
                "handler precisa ser chamável."
            )

        if normalized_tool_id in self._handlers:
            raise ValueError(
                "Ferramenta já registrada: "
                f"{normalized_tool_id!r}."
            )

        self._handlers[
            normalized_tool_id
        ] = handler

    def get(
        self,
        tool_id: str,
    ) -> ToolHandler | None:
        """
        Recupera um handler registrado.

        Retorna None quando não existe implementação.
        """

        if not isinstance(tool_id, str):
            return None

        normalized_tool_id = tool_id.strip()

        if not normalized_tool_id:
            return None

        return self._handlers.get(
            normalized_tool_id
        )

    def require(
        self,
        tool_id: str,
    ) -> ToolHandler:
        """
        Exige que uma implementação esteja registrada.

        Fail-closed:
        ferramenta sem implementação gera LookupError.
        """

        handler = self.get(tool_id)

        if handler is None:
            raise LookupError(
                "Ferramenta sem implementação "
                "registrada: "
                f"{tool_id!r}."
            )

        return handler

    def is_registered(
        self,
        tool_id: str,
    ) -> bool:
        """
        Informa se a ferramenta possui
        implementação registrada.
        """

        return self.get(tool_id) is not None

    def registered_tool_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Retorna os tool_ids registrados
        em ordem alfabética.
        """

        return tuple(
            sorted(
                self._handlers.keys()
            )
        )

    def snapshot(
        self,
    ) -> Mapping[str, ToolHandler]:
        """
        Retorna uma visão somente leitura
        do registro atual.

        Uma cópia é criada antes de gerar
        o MappingProxyType para impedir
        alterações externas no registro.
        """

        return MappingProxyType(
            dict(self._handlers)
        )

    def __contains__(
        self,
        tool_id: object,
    ) -> bool:
        """
        Permite:

        "misp.search_ioc" in registry
        """

        if not isinstance(tool_id, str):
            return False

        return self.is_registered(tool_id)

    def __len__(
        self,
    ) -> int:
        """
        Retorna a quantidade de ferramentas
        com implementação registrada.
        """

        return len(self._handlers)