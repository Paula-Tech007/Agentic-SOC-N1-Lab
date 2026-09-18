"""
Testes da composição oficial das ferramentas
de enriquecimento da Fase 7.3.

Valida:

- criação isolada do ToolRuntime;
- registro funcional das ferramentas MISP;
- registro funcional das ferramentas IAM;
- registro funcional das ferramentas Asset / CMDB;
- ausência de acesso a rede real;
- comportamento fail-closed para configuração ausente;
- comportamento fail-closed para booleano inválido;
- comportamento fail-closed para timeout inválido.
"""

from __future__ import annotations

import httpx
import pytest

from app.enrichment_tool_bootstrap import (
    build_asset_config,
    build_enrichment_tool_runtime,
    build_identity_config,
    build_misp_config,
)

from tools.contracts import (
    ToolExecutionStatus,
    ToolRequest,
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
    Simula resposta MISP sem rede real.
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
    Simula resposta IAM sem rede real.
    """

    return httpx.Response(
        status_code=200,
        json={
            "username": "lab.user",
            "display_name": "Lab User",
            "enabled": True,
        },
        request=request,
    )


def _asset_transport(
    request: httpx.Request,
) -> httpx.Response:
    """
    Simula resposta Asset / CMDB
    sem rede real.
    """

    return httpx.Response(
        status_code=200,
        json={
            "asset_id": "ASSET-0001",
            "hostname": "lab-host",
            "criticality": "HIGH",
        },
        request=request,
    )


def _build_runtime():
    """
    Cria ToolRuntime completamente
    controlado para os testes.
    """

    return build_enrichment_tool_runtime(
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


def test_enrichment_runtime_executes_misp() -> None:
    """
    AG-04 precisa conseguir consultar
    MISP através do ToolRuntime.
    """

    runtime = _build_runtime()

    request = ToolRequest(
        request_id="REQ-TEST-MISP-0001",
        execution_id="EXEC-TEST-MISP-0001",
        agent_id="AG-04",
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        tool_id="misp.search_ioc",
        input_payload={
            "ioc": "203.0.113.10",
        },
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        is ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    assert (
        result.output_payload.get(
            "result"
        )
        is not None
    )

    assert (
        result.evidence_payload.get(
            "source"
        )
        == "MISP"
    )

    assert (
        result.evidence_payload.get(
            "read_only"
        )
        is True
    )


def test_enrichment_runtime_executes_iam() -> None:
    """
    AG-05 precisa conseguir consultar
    IAM através do ToolRuntime.
    """

    runtime = _build_runtime()

    request = ToolRequest(
        request_id="REQ-TEST-IAM-0001",
        execution_id="EXEC-TEST-IAM-0001",
        agent_id="AG-05",
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        tool_id="iam.get_user",
        input_payload={
            "username": "lab.user",
        },
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        is ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    assert (
        result.output_payload.get(
            "result"
        )
        is not None
    )

    assert (
        result.evidence_payload.get(
            "source"
        )
        == "IAM"
    )

    assert (
        result.evidence_payload.get(
            "provider"
        )
        == "LAB-IAM"
    )

    assert (
        result.evidence_payload.get(
            "read_only"
        )
        is True
    )


def test_enrichment_runtime_executes_asset() -> None:
    """
    AG-06 precisa conseguir consultar
    Asset / CMDB através do ToolRuntime.
    """

    runtime = _build_runtime()

    request = ToolRequest(
        request_id="REQ-TEST-ASSET-0001",
        execution_id="EXEC-TEST-ASSET-0001",
        agent_id="AG-06",
        case_id="CASE-TEST-0001",
        correlation_id="CORR-TEST-0001",
        tool_id="asset.get_asset",
        input_payload={
            "asset_id": "ASSET-0001",
        },
    )

    result = runtime.execute(
        request
    )

    assert (
        result.status
        is ToolExecutionStatus.COMPLETED
    )

    assert result.success is True

    assert (
        result.output_payload.get(
            "result"
        )
        is not None
    )

    assert (
        result.evidence_payload.get(
            "source"
        )
        == "ASSET"
    )

    assert (
        result.evidence_payload.get(
            "provider"
        )
        == "LAB-CMDB"
    )

    assert (
        result.evidence_payload.get(
            "read_only"
        )
        is True
    )


def test_missing_required_configuration_fails_closed() -> None:
    """
    Credencial obrigatória ausente
    precisa interromper a composição.
    """

    env = dict(
        TEST_ENV
    )

    env.pop(
        "MISP_API_KEY"
    )

    with pytest.raises(
        RuntimeError,
        match="MISP_API_KEY",
    ):
        build_misp_config(
            env=env
        )


def test_invalid_boolean_configuration_fails_closed() -> None:
    """
    Booleano inválido não pode ser
    interpretado silenciosamente.
    """

    env = dict(
        TEST_ENV
    )

    env[
        "IAM_VERIFY_SSL"
    ] = "talvez"

    with pytest.raises(
        RuntimeError,
        match="IAM_VERIFY_SSL",
    ):
        build_identity_config(
            env=env
        )


def test_invalid_timeout_configuration_fails_closed() -> None:
    """
    Timeout precisa ser inteiro positivo.
    """

    env = dict(
        TEST_ENV
    )

    env[
        "ASSET_TIMEOUT_SECONDS"
    ] = "0"

    with pytest.raises(
        RuntimeError,
        match="ASSET_TIMEOUT_SECONDS",
    ):
        build_asset_config(
            env=env
        )