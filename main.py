"""
Entry point oficial
do Agentic SOC N1 Lab.

Este módulo substitui o teste inicial
isolado de comunicação com Ollama.

Agora o ponto de entrada utiliza a
composição operacional oficial:

Tools
    ↓
RAG
    ↓
FullEnrichmentPayloadProvider
    ↓
Phase7E2ERunner

Modos disponíveis:

--check
    Valida a composição operacional
    e exibe somente informações seguras.

--alert caminho.json
    Carrega um alerta defensivo de um
    arquivo JSON local e executa o
    pipeline oficial.

Sem argumentos:

    apenas exibe ajuda.

Princípios:

- nenhum segredo é impresso;
- nenhuma execução ocorre por import;
- nenhuma rede é acessada sem comando
  explícito do operador;
- arquivos inválidos falham fechado;
- execução continua subordinada aos
  guardrails do projeto.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.operational_bootstrap import (
    build_operational_composition,
)


def _build_parser(
) -> argparse.ArgumentParser:
    """
    Cria o parser oficial da CLI.
    """

    parser = argparse.ArgumentParser(
        prog="agentic-soc-n1",
        description=(
            "Agentic SOC N1 Lab - "
            "pipeline defensivo multiagente."
        ),
    )

    operation = (
        parser.add_mutually_exclusive_group()
    )

    operation.add_argument(
        "--check",
        action="store_true",
        help=(
            "Valida a composição operacional "
            "sem executar um alerta."
        ),
    )

    operation.add_argument(
        "--alert",
        type=str,
        metavar="ARQUIVO_JSON",
        help=(
            "Executa o pipeline utilizando "
            "um alerta JSON local."
        ),
    )

    parser.add_argument(
        "--max-cycles",
        type=int,
        default=32,
        help=(
            "Limite defensivo de ciclos "
            "do runner. Padrão: 32."
        ),
    )

    return parser


def _load_alert_file(
    file_path: str,
) -> dict[str, Any]:
    """
    Carrega alerta JSON local.

    Falha fechado para:

    - caminho inexistente;
    - diretório;
    - arquivo fora de JSON válido;
    - raiz que não seja objeto.
    """

    if not isinstance(
        file_path,
        str,
    ):
        raise TypeError(
            "file_path precisa ser string."
        )

    cleaned = file_path.strip()

    if not cleaned:
        raise ValueError(
            "file_path não pode ser vazio."
        )

    path = (
        Path(cleaned)
        .expanduser()
        .resolve()
    )

    if not path.exists():
        raise FileNotFoundError(
            "Arquivo de alerta "
            "não encontrado."
        )

    if not path.is_file():
        raise ValueError(
            "Caminho do alerta "
            "não é um arquivo."
        )

    if path.suffix.lower() != ".json":
        raise ValueError(
            "Arquivo de alerta precisa "
            "utilizar extensão .json."
        )

    try:
        raw_data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Arquivo de alerta não "
            "contém JSON válido."
        ) from exc

    if not isinstance(
        raw_data,
        dict,
    ):
        raise ValueError(
            "Alerta precisa ser um "
            "objeto JSON."
        )

    return raw_data


def _print_safe_summary(
    summary: dict[str, Any],
) -> None:
    """
    Exibe somente resumo seguro
    em JSON formatado.
    """

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def _run_check(
    *,
    max_cycles: int,
) -> int:
    """
    Valida a composição operacional.

    Nenhum alerta é executado.
    """

    composition = (
        build_operational_composition(
            max_cycles=max_cycles,
        )
    )

    print(
        "=" * 72
    )

    print(
        "AGENTIC SOC N1 LAB"
    )

    print(
        "COMPOSICAO OPERACIONAL OK"
    )

    print(
        "=" * 72
    )

    _print_safe_summary(
        composition.safe_summary()
    )

    return 0


def _run_alert(
    *,
    alert_file: str,
    max_cycles: int,
) -> int:
    """
    Executa alerta local através
    do runner operacional oficial.
    """

    raw_alert = (
        _load_alert_file(
            alert_file
        )
    )

    composition = (
        build_operational_composition(
            max_cycles=max_cycles,
        )
    )

    case_state, result = (
        composition
        .runner
        .bootstrap_and_run(
            raw_alert
        )
    )

    print(
        "=" * 72
    )

    print(
        "AGENTIC SOC N1 LAB"
    )

    print(
        "EXECUCAO FINALIZADA"
    )

    print(
        "=" * 72
    )

    safe_result = (
        result.safe_summary()
    )

    safe_result[
        "case_id"
    ] = case_state.case_id

    safe_result[
        "correlation_id"
    ] = (
        case_state.correlation_id
    )

    _print_safe_summary(
        safe_result
    )

    return 0


def main(
    argv: list[str]
    | None = None,
) -> int:
    """
    Entry point da aplicação.

    Sem operação explícita,
    apenas mostra ajuda.
    """

    parser = _build_parser()

    args = parser.parse_args(
        argv
    )

    if args.check:
        return _run_check(
            max_cycles=(
                args.max_cycles
            ),
        )

    if args.alert is not None:
        return _run_alert(
            alert_file=args.alert,
            max_cycles=(
                args.max_cycles
            ),
        )

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )