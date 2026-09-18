"""
Camada de composição da aplicação
do Agentic SOC N1 Lab.

Esta camada é responsável por montar
os componentes oficiais da aplicação
sem adicionar efeitos colaterais ao
Registry, Runtime ou Orchestrator.
"""

from .bootstrap import (
    OFFICIAL_AGENT_CLASSES,
    build_official_agent_registry,
    build_official_agent_runtime,
    build_official_soc_orchestrator,
    build_phase7_runner,
)


__all__ = [
    "OFFICIAL_AGENT_CLASSES",
    "build_official_agent_registry",
    "build_official_agent_runtime",
    "build_official_soc_orchestrator",
    "build_phase7_runner",
]