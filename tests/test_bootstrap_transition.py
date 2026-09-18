"""
Testes de regressão da transição
AG-02 Alert Intake -> AG-03 Triage.

O bootstrap oficial precisa terminar
com o caso em TRIAGING e com AG-03
como próximo agente pendente.
"""

from app.bootstrap import (
    build_official_soc_orchestrator,
)


def create_raw_alert() -> dict:
    """
    Cria um alerta defensivo válido
    para o bootstrap oficial.
    """

    return {
        "alert_id": (
            "ALT-BOOTSTRAP-TRANSITION-0001"
        ),
        "source": {
            "system": "SIEM",
            "product": "Lab-SIEM",
            "rule_name": (
                "Bootstrap Transition Test"
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


def test_bootstrap_schedules_ag03_after_ag02(
) -> None:
    """
    Depois do AG-02, o workflow precisa
    encaminhar oficialmente para AG-03.
    """

    orchestrator = (
        build_official_soc_orchestrator()
    )

    case_state, result = (
        orchestrator.bootstrap_case(
            raw_alert=create_raw_alert(),
            case_id=(
                "CASE-BOOTSTRAP-TRANSITION-0001"
            ),
            correlation_id=(
                "CORR-BOOTSTRAP-TRANSITION-0001"
            ),
        )
    )

    assert result.success is True
    assert result.agent_id == "AG-02"

    assert case_state is not None

    assert (
        case_state
        .workflow
        .case_status
        .value
        == "TRIAGING"
    )

    assert (
        case_state
        .workflow
        .completed_agents
        == ["AG-02"]
    )

    assert (
        case_state
        .workflow
        .pending_agents
        == ["AG-03"]
    )

    assert (
        case_state
        .workflow
        .current_agent
        is None
    )