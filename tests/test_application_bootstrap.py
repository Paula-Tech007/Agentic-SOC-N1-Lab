"""
Testes da composition root oficial
do Agentic SOC N1 Lab.
"""

from app.bootstrap import (
    OFFICIAL_AGENT_CLASSES,
    build_official_agent_registry,
    build_official_agent_runtime,
    build_official_soc_orchestrator,
    build_phase7_runner,
)
from core.orchestrator import (
    AgentRegistry,
    AgentRuntime,
    OFFICIAL_AGENT_IDS,
    SOCOrchestrator,
)
from core.orchestrator.phase7_runner import (
    Phase7E2ERunner,
)


def create_raw_alert() -> dict:
    """
    Cria alerta defensivo de laboratório
    válido para o bootstrap oficial.
    """

    return {
        "alert_id": (
            "ALT-APP-BOOTSTRAP-0001"
        ),
        "source": {
            "system": "SIEM",
            "product": "Lab-SIEM",
            "rule_name": (
                "Application Bootstrap Test"
            ),
        },
        "event": {
            "event_type": (
                "AUTH_BRUTE_FORCE"
            ),
            "category": (
                "authentication"
            ),
            "message": (
                "Falhas de autenticacao "
                "simuladas no laboratorio."
            ),
            "raw_event": {
                "username": "lab.user",
                "source_ip": (
                    "203.0.113.10"
                ),
            },
        },
        "initial_severity": "HIGH",
    }


def test_official_agent_classes_contains_12_agents(
) -> None:
    """
    A composition root precisa conhecer
    exatamente os 12 agentes oficiais.
    """

    assert len(
        OFFICIAL_AGENT_CLASSES
    ) == 12


def test_build_official_registry_registers_all_agents(
) -> None:
    """
    O Registry oficial precisa nascer
    com todos os agentes disponíveis.
    """

    registry = (
        build_official_agent_registry()
    )

    assert isinstance(
        registry,
        AgentRegistry,
    )

    assert (
        registry.registered_count()
        == 12
    )

    assert (
        set(
            registry.registered_ids()
        )
        == set(
            OFFICIAL_AGENT_IDS
        )
    )

    assert (
        registry.missing_official_agents()
        == ()
    )


def test_build_official_runtime_can_execute_all_agents(
) -> None:
    """
    O Runtime oficial precisa enxergar
    todos os agentes registrados.
    """

    runtime = (
        build_official_agent_runtime()
    )

    assert isinstance(
        runtime,
        AgentRuntime,
    )

    for agent_id in OFFICIAL_AGENT_IDS:
        assert runtime.can_execute(
            agent_id
        ) is True


def test_build_official_orchestrator_uses_complete_runtime(
) -> None:
    """
    O SOCOrchestrator oficial precisa
    utilizar um Runtime completo.
    """

    orchestrator = (
        build_official_soc_orchestrator()
    )

    assert isinstance(
        orchestrator,
        SOCOrchestrator,
    )

    for agent_id in OFFICIAL_AGENT_IDS:
        assert (
            orchestrator
            .runtime
            .can_execute(
                agent_id
            )
            is True
        )


def test_official_orchestrator_bootstraps_ag02(
) -> None:
    """
    A composição oficial precisa permitir
    que AG-02 execute sem registro manual.
    """

    orchestrator = (
        build_official_soc_orchestrator()
    )

    case_state, result = (
        orchestrator.bootstrap_case(
            raw_alert=create_raw_alert(),
            case_id=(
                "CASE-APP-BOOTSTRAP-0001"
            ),
            correlation_id=(
                "CORR-APP-BOOTSTRAP-0001"
            ),
        )
    )

    assert result.success is True

    assert (
        result.agent_id
        == "AG-02"
    )

    assert case_state is not None

    assert (
        "AG-02"
        in
        case_state
        .workflow
        .completed_agents
    )


def test_build_phase7_runner_returns_official_runner(
) -> None:
    """
    O builder E2E precisa produzir
    um Phase7E2ERunner válido.
    """

    runner = (
        build_phase7_runner()
    )

    assert isinstance(
        runner,
        Phase7E2ERunner,
    )


def test_build_phase7_runner_rejects_invalid_cycles(
) -> None:
    """
    Configuração inválida deve falhar fechado.
    """

    invalid_values = (
        0,
        -1,
        True,
    )

    for value in invalid_values:
        try:
            build_phase7_runner(
                max_cycles=value
            )

        except ValueError:
            pass

        else:
            raise AssertionError(
                "max_cycles inválido "
                "foi aceito."
            )