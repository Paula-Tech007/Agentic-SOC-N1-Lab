"""
Testes do EnrichmentPayloadProvider
da Fase 7.3 do Agentic SOC N1 Lab.

Valida:

- AG-04 recebe payload comprovado por MISP;
- AG-05 recebe payload comprovado por IAM;
- AG-06 recebe payload comprovado por Asset / CMDB;
- schemas oficiais aceitam os payloads produzidos;
- ausência de IOC falha fechado;
- AG-08 permanece bloqueado até integração RAG;
- nenhum acesso à rede real é realizado.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.enrichment_payload_provider import (
    EnrichmentPayloadProvider,
)
from app.enrichment_tool_bootstrap import (
    build_enrichment_tool_runtime,
)

from core.schemas import (
    Alert,
    AlertEvent,
    AlertSource,
    AlertType,
    AssetContext,
    IdentityContext,
    Severity,
    ThreatIntelFinding,
)
from core.state import (
    CaseState,
)


TEST_ENV = {
    "MISP_URL": (
        "https://misp.example.invalid"
    ),
    "MISP_API_KEY": (
        "TEST-MISP-KEY"
    ),
    "MISP_VERIFY_SSL": "true",
    "MISP_TIMEOUT_SECONDS": "15",

    "IAM_URL": (
        "https://iam.example.invalid"
    ),
    "IAM_API_TOKEN": (
        "TEST-IAM-TOKEN"
    ),
    "IAM_PROVIDER": "LAB-IAM",
    "IAM_VERIFY_SSL": "true",
    "IAM_TIMEOUT_SECONDS": "15",

    "ASSET_URL": (
        "https://asset.example.invalid"
    ),
    "ASSET_API_TOKEN": (
        "TEST-ASSET-TOKEN"
    ),
    "ASSET_PROVIDER": "LAB-CMDB",
    "ASSET_VERIFY_SSL": "true",
    "ASSET_TIMEOUT_SECONDS": "15",
}


def _misp_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula consulta MISP.

    O IOC é consultado, porém a fonte
    não afirma reputação maliciosa
    nem benigna.
    """

    return httpx.Response(
        status_code=200,
        json={
            "response": {
                "Attribute": [],
            },
        },
        request=request,
    )


def _identity_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula as consultas IAM.

    O mesmo conjunto controlado de dados
    pode ser utilizado pelos quatro
    endpoints read-only.
    """

    return httpx.Response(
        status_code=200,
        json={
            "identity_id": (
                "IDENTITY-LAB-0001"
            ),
            "user_id": (
                "IDENTITY-LAB-0001"
            ),
            "username": "lab.user",
            "display_name": "Lab User",
            "email": (
                "lab.user@example.test"
            ),
            "exists": True,
            "enabled": True,
            "privileged": True,
            "mfa_enabled": True,
            "department": "Security",
            "role": "SOC Analyst",
            "failed_login_count": 7,
            "confidence": 90,
            "risk_factors": [
                "privileged_account",
                "multiple_failed_logins",
            ],
            "groups": [
                "SOC",
                "Security",
            ],
        },
        request=request,
    )


def _asset_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula consultas Asset / CMDB.

    A resposta contém dados suficientes
    para get_ip_context, criticality
    e EDR.
    """

    return httpx.Response(
        status_code=200,
        json={
            "asset_id": (
                "ASSET-LAB-0001"
            ),
            "hostname": (
                "lab-host"
            ),
            "asset_type": (
                "workstation"
            ),
            "operating_system": (
                "Windows"
            ),
            "criticality": "HIGH",
            "owner": "Lab User",
            "department": "Security",
            "environment": "laboratory",
            "internet_exposed": False,
            "managed": True,
            "edr_installed": True,
            "ip_address": (
                "203.0.113.10"
            ),
            "confidence": 92,
            "risk_factors": [
                "authentication_activity",
            ],
        },
        request=request,
    )


def _create_provider(
) -> EnrichmentPayloadProvider:
    """
    Cria provider com ToolRuntime
    completamente simulado.
    """

    runtime = (
        build_enrichment_tool_runtime(
            env=TEST_ENV,
            misp_transport=(
                httpx.MockTransport(
                    _misp_transport
                )
            ),
            identity_transport=(
                httpx.MockTransport(
                    _identity_transport
                )
            ),
            asset_transport=(
                httpx.MockTransport(
                    _asset_transport
                )
            ),
        )
    )

    return EnrichmentPayloadProvider(
        runtime
    )


def _create_case(
    *,
    raw_event: dict[
        str,
        Any,
    ]
    | None = None,
) -> CaseState:
    """
    Cria CaseState controlado
    semelhante ao alerta E2E real
    utilizado na Correção 3.
    """

    if raw_event is None:
        raw_event = {
            "username": "lab.user",
            "source_ip": (
                "203.0.113.10"
            ),
        }

    alert = Alert(
        alert_id=(
            "ALT-PAYLOAD-0001"
        ),
        correlation_id=(
            "CORR-PAYLOAD-0001"
        ),
        source=AlertSource(
            system="SIEM",
            product="Lab-SIEM",
            rule_name=(
                "Brute Force Payload Test"
            ),
        ),
        event=AlertEvent(
            event_type=(
                AlertType.AUTH_BRUTE_FORCE
            ),
            category=(
                "authentication"
            ),
            message=(
                "Multiplas falhas de "
                "autenticacao simuladas."
            ),
            raw_event=raw_event,
        ),
        initial_severity=(
            Severity.HIGH
        ),
    )

    return CaseState(
        case_id=(
            "CASE-PAYLOAD-0001"
        ),
        correlation_id=(
            "CORR-PAYLOAD-0001"
        ),
        alert=alert,
    )


def test_ag04_builds_valid_threat_intel_payload(
) -> None:
    """
    AG-04 deve receber finding válido
    construído a partir da consulta MISP.

    Ausência de reputação explícita
    permanece desconhecida.
    """

    provider = _create_provider()

    case_state = _create_case()

    payload = provider.build_payload(
        case_state=case_state,
        agent_id="AG-04",
    )

    assert "findings" in payload

    assert (
        len(
            payload["findings"]
        )
        == 1
    )

    finding = (
        ThreatIntelFinding
        .model_validate(
            payload[
                "findings"
            ][0]
        )
    )

    assert (
        finding.value
        == "203.0.113.10"
    )

    assert (
        finding.indicator_type.value
        == "IP"
    )

    assert (
        finding.provider
        == "MISP"
    )

    assert (
        finding.reputation
        is None
    )

    assert (
        finding.malicious_confirmed
        is None
    )

    assert (
        finding.confidence
        == 0
    )

    assert (
        payload[
            "queried_sources"
        ]
        == [
            "MISP",
        ]
    )


def test_ag05_builds_valid_identity_payload(
) -> None:
    """
    AG-05 deve receber IdentityContext
    válido construído exclusivamente
    com resultados do IAM.
    """

    provider = _create_provider()

    case_state = _create_case()

    payload = provider.build_payload(
        case_state=case_state,
        agent_id="AG-05",
    )

    assert "identities" in payload

    assert (
        len(
            payload["identities"]
        )
        == 1
    )

    identity = (
        IdentityContext
        .model_validate(
            payload[
                "identities"
            ][0]
        )
    )

    assert (
        identity.identity_id
        == "IDENTITY-LAB-0001"
    )

    assert (
        identity.username
        == "lab.user"
    )

    assert (
        identity.account_exists
        is True
    )

    assert (
        identity.account_enabled
        is True
    )

    assert (
        identity.privileged
        is True
    )

    assert (
        identity.mfa_enabled
        is True
    )

    assert (
        identity.confidence
        == 90
    )

    assert (
        identity.source
        == "LAB-IAM"
    )

    assert (
        "privileged_account"
        in identity.risk_factors
    )


def test_ag06_builds_valid_asset_payload(
) -> None:
    """
    AG-06 deve utilizar o source_ip
    do evento, consultar Asset / CMDB
    e produzir AssetContext válido.
    """

    provider = _create_provider()

    case_state = _create_case()

    payload = provider.build_payload(
        case_state=case_state,
        agent_id="AG-06",
    )

    assert "assets" in payload

    assert (
        len(
            payload["assets"]
        )
        == 1
    )

    asset = (
        AssetContext
        .model_validate(
            payload[
                "assets"
            ][0]
        )
    )

    assert (
        asset.asset_id
        == "ASSET-LAB-0001"
    )

    assert (
        asset.hostname
        == "lab-host"
    )

    assert (
        asset.criticality
        is Severity.HIGH
    )

    assert (
        asset.managed
        is True
    )

    assert (
        asset.edr_installed
        is True
    )

    assert (
        asset.source
        == "LAB-CMDB"
    )

    assert (
        asset.confidence
        == 92
    )

    assert (
        "203.0.113.10"
        in asset.ip_addresses
    )


def test_ag04_without_ioc_fails_closed(
) -> None:
    """
    AG-04 não pode inventar IOC
    quando o caso não possui indicador.
    """

    provider = _create_provider()

    case_state = _create_case(
        raw_event={
            "username": "lab.user",
        }
    )

    with pytest.raises(
        RuntimeError,
        match="sem IOC",
    ):
        provider.build_payload(
            case_state=case_state,
            agent_id="AG-04",
        )


def test_ag08_remains_fail_closed_until_rag(
) -> None:
    """
    AG-08 não pode receber payload
    artificial enquanto o RAG oficial
    ainda não estiver conectado.
    """

    provider = _create_provider()

    case_state = _create_case()

    with pytest.raises(
        RuntimeError,
        match="composição RAG",
    ):
        provider.build_payload(
            case_state=case_state,
            agent_id="AG-08",
        )


def test_unknown_agent_is_rejected(
) -> None:
    """
    Provider não pode preparar payload
    para agente fora do escopo.
    """

    provider = _create_provider()

    case_state = _create_case()

    with pytest.raises(
        ValueError,
        match="não suportado",
    ):
        provider.build_payload(
            case_state=case_state,
            agent_id="AG-99",
        )