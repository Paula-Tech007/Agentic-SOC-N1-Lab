"""
Testes iniciais da Fundação Técnica do Agentic SOC N1 Lab.

Objetivo:
Validar configurações básicas e componentes principais
antes de avançar para os agentes.
"""

from pathlib import Path

from core.config import (
    APP_NAME,
    APP_VERSION,
    DENY_BY_DEFAULT,
    EMBEDDING_MODEL,
    FAIL_CLOSED,
    LLM_MODEL,
    N1_AUTO_CLOSE_MIN_CONFIDENCE,
)


def test_project_name() -> None:
    assert APP_NAME == "Agentic SOC N1 Lab"


def test_project_version_exists() -> None:
    assert APP_VERSION


def test_llm_model_configured() -> None:
    assert LLM_MODEL == "qwen3:4b-instruct"


def test_embedding_model_configured() -> None:
    assert EMBEDDING_MODEL == "embeddinggemma"


def test_security_deny_by_default_enabled() -> None:
    assert DENY_BY_DEFAULT is True


def test_fail_closed_enabled() -> None:
    assert FAIL_CLOSED is True


def test_n1_confidence_threshold() -> None:
    assert N1_AUTO_CLOSE_MIN_CONFIDENCE == 90


def test_required_directories_exist() -> None:
    project_root = Path(__file__).resolve().parent.parent

    required_directories = [
        "agents",
        "core",
        "docs",
        "knowledge",
        "logs",
        "mcp",
        "rag",
        "simulations",
        "storage",
        "tests",
        "tools",
    ]

    for directory in required_directories:
        assert (project_root / directory).is_dir()