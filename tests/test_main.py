"""
Testes do entry point oficial
do Agentic SOC N1 Lab.

Valida:

- carregamento seguro de JSON;
- rejeição de arquivo inválido;
- modo sem argumentos;
- modo --check;
- modo --alert;
- nenhuma dependência real de rede
  durante estes testes.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import main as main_module


class FakeComposition:
    """
    Composição controlada utilizada
    exclusivamente pelos testes.
    """

    def __init__(
        self,
    ) -> None:
        self.runner = FakeRunner()

    def safe_summary(
        self,
    ) -> dict[str, object]:
        return {
            "tool_runtime": (
                "ToolRuntime"
            ),
            "rag_items_loaded": 1,
            "payload_provider": (
                "FullEnrichmentPayloadProvider"
            ),
            "runner": (
                "Phase7E2ERunner"
            ),
            "rag_local_only": True,
        }


class FakeRunner:
    """
    Runner controlado sem agentes reais.
    """

    def bootstrap_and_run(
        self,
        raw_alert,
    ):
        assert isinstance(
            raw_alert,
            dict,
        )

        case_state = (
            SimpleNamespace(
                case_id=(
                    "CASE-MAIN-0001"
                ),
                correlation_id=(
                    "CORR-MAIN-0001"
                ),
            )
        )

        result = (
            SimpleNamespace(
                safe_summary=lambda: {
                    "case_id": (
                        "CASE-MAIN-0001"
                    ),
                    "correlation_id": (
                        "CORR-MAIN-0001"
                    ),
                    "final_case_status": (
                        "CLOSED_N1"
                    ),
                    "terminal": True,
                }
            )
        )

        return (
            case_state,
            result,
        )


def test_load_alert_file(
    tmp_path: Path,
) -> None:
    """
    JSON válido deve ser carregado.
    """

    path = (
        tmp_path
        / "alert.json"
    )

    payload = {
        "alert_id": (
            "ALT-MAIN-0001"
        )
    }

    path.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    result = (
        main_module
        ._load_alert_file(
            str(path)
        )
    )

    assert result == payload


def test_load_alert_rejects_missing_file(
    tmp_path: Path,
) -> None:
    """
    Arquivo inexistente falha fechado.
    """

    path = (
        tmp_path
        / "missing.json"
    )

    with pytest.raises(
        FileNotFoundError,
    ):
        main_module._load_alert_file(
            str(path)
        )


def test_load_alert_rejects_non_json_extension(
    tmp_path: Path,
) -> None:
    """
    Extensão diferente de JSON
    não deve ser aceita.
    """

    path = (
        tmp_path
        / "alert.txt"
    )

    path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=".json",
    ):
        main_module._load_alert_file(
            str(path)
        )


def test_load_alert_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    """
    JSON inválido falha fechado.
    """

    path = (
        tmp_path
        / "alert.json"
    )

    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON válido",
    ):
        main_module._load_alert_file(
            str(path)
        )


def test_main_without_operation_returns_zero(
    capsys,
) -> None:
    """
    Sem argumentos, apenas ajuda.
    """

    result = (
        main_module.main(
            []
        )
    )

    assert result == 0

    captured = (
        capsys.readouterr()
    )

    assert (
        "Agentic SOC N1 Lab"
        in captured.out
    )


def test_main_check_uses_operational_composition(
    monkeypatch,
    capsys,
) -> None:
    """
    --check deve construir
    composição oficial.
    """

    calls = []

    def fake_builder(
        *,
        max_cycles,
    ):
        calls.append(
            max_cycles
        )

        return FakeComposition()

    monkeypatch.setattr(
        main_module,
        (
            "build_operational_composition"
        ),
        fake_builder,
    )

    result = (
        main_module.main(
            [
                "--check",
                "--max-cycles",
                "20",
            ]
        )
    )

    assert result == 0

    assert calls == [
        20,
    ]

    captured = (
        capsys.readouterr()
    )

    assert (
        "COMPOSICAO OPERACIONAL OK"
        in captured.out
    )


def test_main_alert_uses_official_runner(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """
    --alert deve carregar JSON
    e delegar ao runner.
    """

    path = (
        tmp_path
        / "alert.json"
    )

    path.write_text(
        json.dumps(
            {
                "alert_id": (
                    "ALT-MAIN-0001"
                )
            }
        ),
        encoding="utf-8",
    )

    def fake_builder(
        *,
        max_cycles,
    ):
        assert max_cycles == 32

        return FakeComposition()

    monkeypatch.setattr(
        main_module,
        (
            "build_operational_composition"
        ),
        fake_builder,
    )

    result = (
        main_module.main(
            [
                "--alert",
                str(path),
            ]
        )
    )

    assert result == 0

    captured = (
        capsys.readouterr()
    )

    assert (
        "EXECUCAO FINALIZADA"
        in captured.out
    )

    assert (
        "CASE-MAIN-0001"
        in captured.out
    )