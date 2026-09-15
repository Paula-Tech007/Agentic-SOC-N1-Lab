"""
Testes iniciais da Fundação Técnica
do Agentic SOC N1 Lab.

Objetivo:
Validar configurações básicas,
componentes principais e diretórios
estruturais do projeto antes de avançar
para as demais fases.

A camada Model Context Protocol utiliza:

    mcp

como SDK oficial instalado no ambiente Python.

A implementação própria do projeto utiliza:

    soc_mcp

evitando conflito de namespace com
o pacote oficial MCP.
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
    """
    Nome oficial do projeto.
    """

    assert (
        APP_NAME
        == "Agentic SOC N1 Lab"
    )


def test_project_version_exists() -> None:
    """
    O projeto precisa possuir
    versão configurada.
    """

    assert APP_VERSION


def test_llm_model_configured() -> None:
    """
    Modelo LLM local oficial.
    """

    assert (
        LLM_MODEL
        == "qwen3:4b-instruct"
    )


def test_embedding_model_configured() -> None:
    """
    Modelo local utilizado
    pela camada de embeddings/RAG.
    """

    assert (
        EMBEDDING_MODEL
        == "embeddinggemma"
    )


def test_security_deny_by_default_enabled() -> None:
    """
    Governança principal deve operar
    em deny-by-default.
    """

    assert (
        DENY_BY_DEFAULT
        is True
    )


def test_fail_closed_enabled() -> None:
    """
    Falhas de segurança devem resultar
    em bloqueio conservador.
    """

    assert (
        FAIL_CLOSED
        is True
    )


def test_n1_confidence_threshold() -> None:
    """
    Fechamento automático N1 exige
    confiança mínima definida.
    """

    assert (
        N1_AUTO_CLOSE_MIN_CONFIDENCE
        == 90
    )


def test_required_directories_exist() -> None:
    """
    Valida os diretórios estruturais
    obrigatórios do projeto.

    O diretório soc_mcp contém a
    implementação MCP própria.

    Não utilizamos um diretório local
    chamado mcp porque esse namespace
    pertence ao SDK oficial instalado
    no ambiente Python.
    """

    project_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    required_directories = [
        "agents",
        "core",
        "docs",
        "knowledge",
        "logs",
        "rag",
        "simulations",
        "soc_mcp",
        "storage",
        "tests",
        "tools",
    ]

    for directory in required_directories:
        directory_path = (
            project_root
            / directory
        )

        assert (
            directory_path.is_dir()
        ), (
            "Diretório obrigatório "
            "não encontrado: "
            f"{directory}"
        )