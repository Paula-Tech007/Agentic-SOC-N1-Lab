"""
Estruturas imutáveis utilizadas pelos schemas do
Agentic SOC N1 Lab.

O objetivo principal é impedir alterações silenciosas em
dados que precisam preservar integridade durante toda a
investigação.

O raw_event de um alerta é um exemplo desse tipo de dado.
"""

from collections.abc import Iterator, Mapping
from typing import Any


def freeze_value(value: Any) -> Any:
    """
    Converte estruturas mutáveis em equivalentes imutáveis.
    """

    if isinstance(value, FrozenDict):
        return value

    if isinstance(value, Mapping):
        return FrozenDict(value)

    if isinstance(value, list):
        return tuple(
            freeze_value(item)
            for item in value
        )

    if isinstance(value, tuple):
        return tuple(
            freeze_value(item)
            for item in value
        )

    if isinstance(value, set):
        return frozenset(
            freeze_value(item)
            for item in value
        )

    return value


def thaw_value(value: Any) -> Any:
    """
    Converte estruturas imutáveis novamente para estruturas
    compatíveis com JSON.
    """

    if isinstance(value, FrozenDict):
        return value.to_dict()

    if isinstance(value, tuple):
        return [
            thaw_value(item)
            for item in value
        ]

    if isinstance(value, frozenset):
        return [
            thaw_value(item)
            for item in value
        ]

    return value


class FrozenDict(Mapping[str, Any]):
    """
    Mapping imutável utilizado para preservar eventos brutos.
    """

    def __init__(
        self,
        data: Mapping[str, Any] | None = None,
    ) -> None:
        source = data or {}

        self._data = {
            str(key): freeze_value(value)
            for key, value in source.items()
        }

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"FrozenDict({self._data!r})"

    def to_dict(self) -> dict[str, Any]:
        """
        Retorna uma cópia compatível com serialização JSON.
        """

        return {
            key: thaw_value(value)
            for key, value in self._data.items()
        }