"""
Política central de ferramentas do Agentic SOC N1 Lab.

Fase 4.0 — Catálogo e Governança das Ferramentas.

Princípios:

- deny-by-default;
- least privilege;
- somente operações defensivas;
- ferramentas comprovam, LLM interpreta;
- chamadas externas precisam ser auditáveis;
- nenhuma ação crítica real é autorizada;
- integrações iniciais são somente leitura;
- agente só utiliza ferramenta explicitamente permitida.

Ações críticas como:

- reset de senha;
- desabilitação de conta;
- bloqueio de IP;
- isolamento de endpoint;
- modificação de firewall;
- abertura de URL;
- execução de anexo;

não fazem parte do catálogo autorizado.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class ToolAccessMode(str, Enum):
    """
    Modos de acesso possíveis para ferramentas.

    Na Fase 4 somente READ_ONLY é permitido
    no catálogo operacional.
    """

    READ_ONLY = "READ_ONLY"
    RECOMMENDED_ACTION = "RECOMMENDED_ACTION"
    SIMULATED_ACTION = "SIMULATED_ACTION"


class ToolRiskLevel(str, Enum):
    """
    Classificação de risco da ferramenta.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """
    Definição imutável de uma ferramenta autorizada.
    """

    tool_id: str
    integration: str
    operation: str
    description: str
    access_mode: ToolAccessMode
    risk_level: ToolRiskLevel
    allowed_agents: tuple[str, ...]
    timeout_seconds: int = 15
    max_retries: int = 1
    evidence_required: bool = True


OFFICIAL_AGENT_IDS = frozenset(
    {
        "AG-01",
        "AG-02",
        "AG-03",
        "AG-04",
        "AG-05",
        "AG-06",
        "AG-07",
        "AG-08",
        "AG-09",
        "AG-10",
        "AG-11",
        "AG-12",
    }
)


FORBIDDEN_TOOL_IDS = frozenset(
    {
        "iam.reset_password",
        "iam.disable_user",
        "iam.delete_user",
        "network.block_ip",
        "network.unblock_ip",
        "firewall.add_rule",
        "firewall.delete_rule",
        "firewall.modify_rule",
        "endpoint.isolate_host",
        "endpoint.kill_process",
        "endpoint.delete_file",
        "email.open_url",
        "email.execute_attachment",
        "email.download_attachment",
    }
)


_TOOL_CATALOG: dict[str, ToolDefinition] = {
    # =========================================================
    # MISP / Threat Intelligence
    # =========================================================
    "misp.search_ioc": ToolDefinition(
        tool_id="misp.search_ioc",
        integration="MISP",
        operation="search_ioc",
        description=(
            "Pesquisa IOC conhecido no MISP utilizando "
            "indicador previamente coletado."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-04",
            "AG-07",
            "AG-09",
        ),
    ),
    "misp.get_event": ToolDefinition(
        tool_id="misp.get_event",
        integration="MISP",
        operation="get_event",
        description=(
            "Consulta detalhes de um evento existente no MISP."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-04",
            "AG-09",
        ),
    ),
    "misp.get_attribute": ToolDefinition(
        tool_id="misp.get_attribute",
        integration="MISP",
        operation="get_attribute",
        description=(
            "Consulta atributo específico existente no MISP."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-04",
            "AG-09",
        ),
    ),

    # =========================================================
    # Elastic / SIEM
    # =========================================================
    "elastic.search_alerts": ToolDefinition(
        tool_id="elastic.search_alerts",
        integration="ELASTIC",
        operation="search_alerts",
        description=(
            "Pesquisa alertas relacionados ao caso no Elastic/SIEM."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-03",
            "AG-05",
            "AG-06",
            "AG-09",
        ),
        timeout_seconds=20,
    ),
    "elastic.search_events": ToolDefinition(
        tool_id="elastic.search_events",
        integration="ELASTIC",
        operation="search_events",
        description=(
            "Pesquisa eventos relacionados ao caso no Elastic/SIEM."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-03",
            "AG-05",
            "AG-06",
            "AG-09",
        ),
        timeout_seconds=20,
    ),
    "elastic.get_document": ToolDefinition(
        tool_id="elastic.get_document",
        integration="ELASTIC",
        operation="get_document",
        description=(
            "Consulta documento específico já identificado "
            "no Elastic."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-03",
            "AG-09",
        ),
        timeout_seconds=15,
    ),

    # =========================================================
    # IAM / Identidade
    # =========================================================
    "iam.get_user": ToolDefinition(
        tool_id="iam.get_user",
        integration="IAM",
        operation="get_user",
        description=(
            "Consulta informações defensivas de uma identidade."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-05",
            "AG-09",
        ),
    ),
    "iam.get_account_status": ToolDefinition(
        tool_id="iam.get_account_status",
        integration="IAM",
        operation="get_account_status",
        description=(
            "Verifica se uma conta está habilitada, "
            "desabilitada ou bloqueada."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-03",
            "AG-05",
            "AG-09",
        ),
    ),
    "iam.get_mfa_status": ToolDefinition(
        tool_id="iam.get_mfa_status",
        integration="IAM",
        operation="get_mfa_status",
        description=(
            "Consulta o estado de MFA da identidade."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-05",
            "AG-09",
        ),
    ),
    "iam.get_group_membership": ToolDefinition(
        tool_id="iam.get_group_membership",
        integration="IAM",
        operation="get_group_membership",
        description=(
            "Consulta grupos e privilégios associados "
            "à identidade."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.MEDIUM,
        allowed_agents=(
            "AG-05",
            "AG-09",
        ),
    ),

    # =========================================================
    # Asset / CMDB
    # =========================================================
    "asset.get_asset": ToolDefinition(
        tool_id="asset.get_asset",
        integration="ASSET",
        operation="get_asset",
        description=(
            "Consulta informações de ativo previamente identificado."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-06",
            "AG-09",
        ),
    ),
    "asset.get_ip_context": ToolDefinition(
        tool_id="asset.get_ip_context",
        integration="ASSET",
        operation="get_ip_context",
        description=(
            "Consulta contexto de ativo associado a um IP interno."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-06",
            "AG-09",
        ),
    ),
    "asset.get_criticality": ToolDefinition(
        tool_id="asset.get_criticality",
        integration="ASSET",
        operation="get_criticality",
        description=(
            "Consulta a criticidade cadastrada para o ativo."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-03",
            "AG-06",
            "AG-09",
        ),
    ),
    "asset.get_edr_status": ToolDefinition(
        tool_id="asset.get_edr_status",
        integration="ASSET",
        operation="get_edr_status",
        description=(
            "Consulta se o ativo possui proteção EDR registrada."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-06",
            "AG-09",
        ),
    ),

    # =========================================================
    # Email / Phishing
    # =========================================================
    "email.get_message_metadata": ToolDefinition(
        tool_id="email.get_message_metadata",
        integration="EMAIL",
        operation="get_message_metadata",
        description=(
            "Consulta metadados defensivos de uma mensagem."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-07",
            "AG-09",
        ),
    ),
    "email.get_headers": ToolDefinition(
        tool_id="email.get_headers",
        integration="EMAIL",
        operation="get_headers",
        description=(
            "Consulta cabeçalhos técnicos de uma mensagem."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-07",
            "AG-09",
        ),
    ),
    "email.get_authentication_results": ToolDefinition(
        tool_id="email.get_authentication_results",
        integration="EMAIL",
        operation="get_authentication_results",
        description=(
            "Consulta resultados SPF, DKIM e DMARC "
            "já disponíveis na mensagem."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-07",
            "AG-09",
        ),
    ),
    "email.get_attachment_metadata": ToolDefinition(
        tool_id="email.get_attachment_metadata",
        integration="EMAIL",
        operation="get_attachment_metadata",
        description=(
            "Consulta somente metadados de anexos, "
            "sem executar ou abrir o arquivo."
        ),
        access_mode=ToolAccessMode.READ_ONLY,
        risk_level=ToolRiskLevel.LOW,
        allowed_agents=(
            "AG-07",
            "AG-09",
        ),
    ),
}


TOOL_CATALOG: Mapping[str, ToolDefinition] = (
    MappingProxyType(_TOOL_CATALOG)
)


def get_tool_definition(
    tool_id: str,
) -> ToolDefinition | None:
    """
    Recupera uma ferramenta conhecida.

    Retorna None quando ela não pertence ao catálogo.
    """

    if not isinstance(tool_id, str):
        return None

    normalized_tool_id = tool_id.strip()

    if not normalized_tool_id:
        return None

    return TOOL_CATALOG.get(normalized_tool_id)


def allowed_tools_for_agent(
    agent_id: str,
) -> tuple[str, ...]:
    """
    Retorna somente ferramentas explicitamente
    autorizadas para o agente informado.
    """

    if not isinstance(agent_id, str):
        return ()

    normalized_agent_id = agent_id.strip()

    if normalized_agent_id not in OFFICIAL_AGENT_IDS:
        return ()

    return tuple(
        sorted(
            tool_id
            for tool_id, definition
            in TOOL_CATALOG.items()
            if normalized_agent_id
            in definition.allowed_agents
        )
    )


def is_tool_allowed(
    agent_id: str,
    tool_id: str,
) -> bool:
    """
    Verifica autorização usando deny-by-default.

    Qualquer agente ou ferramenta desconhecida
    recebe False.
    """

    if not isinstance(agent_id, str):
        return False

    normalized_agent_id = agent_id.strip()

    if normalized_agent_id not in OFFICIAL_AGENT_IDS:
        return False

    definition = get_tool_definition(tool_id)

    if definition is None:
        return False

    if definition.tool_id in FORBIDDEN_TOOL_IDS:
        return False

    return (
        normalized_agent_id
        in definition.allowed_agents
    )


def validate_tool_access(
    agent_id: str,
    tool_id: str,
) -> ToolDefinition:
    """
    Valida acesso à ferramenta.

    Fail-closed:
    acesso não autorizado gera PermissionError.
    """

    definition = get_tool_definition(tool_id)

    if definition is None:
        raise PermissionError(
            "Ferramenta não registrada no catálogo: "
            f"{tool_id!r}."
        )

    if not is_tool_allowed(
        agent_id=agent_id,
        tool_id=tool_id,
    ):
        raise PermissionError(
            "Acesso à ferramenta negado: "
            f"agent_id={agent_id!r}, "
            f"tool_id={tool_id!r}."
        )

    return definition


def validate_tool_catalog() -> None:
    """
    Valida a integridade do catálogo oficial.

    A aplicação deve falhar de forma fechada caso
    uma ferramenta insegura ou uma configuração
    inválida seja adicionada.
    """

    for tool_id, definition in TOOL_CATALOG.items():
        if tool_id != definition.tool_id:
            raise RuntimeError(
                "tool_id do catálogo não corresponde "
                "ao ToolDefinition: "
                f"{tool_id!r} != "
                f"{definition.tool_id!r}."
            )

        expected_tool_id = (
            f"{definition.integration.lower()}."
            f"{definition.operation}"
        )

        if tool_id != expected_tool_id:
            raise RuntimeError(
                "Formato de tool_id inválido: "
                f"{tool_id!r}. "
                "Esperado: "
                f"{expected_tool_id!r}."
            )

        if (
            definition.access_mode
            != ToolAccessMode.READ_ONLY
        ):
            raise RuntimeError(
                "A Fase 4 somente permite ferramentas "
                "operacionais READ_ONLY: "
                f"{tool_id!r}."
            )

        if (
            definition.risk_level
            == ToolRiskLevel.CRITICAL
        ):
            raise RuntimeError(
                "Ferramentas CRITICAL não podem fazer "
                "parte do catálogo operacional: "
                f"{tool_id!r}."
            )

        if definition.timeout_seconds < 1:
            raise RuntimeError(
                "timeout_seconds inválido em "
                f"{tool_id!r}."
            )

        if definition.max_retries < 0:
            raise RuntimeError(
                "max_retries inválido em "
                f"{tool_id!r}."
            )

        if not definition.allowed_agents:
            raise RuntimeError(
                "Ferramenta sem agente autorizado: "
                f"{tool_id!r}."
            )

        for agent_id in definition.allowed_agents:
            if agent_id not in OFFICIAL_AGENT_IDS:
                raise RuntimeError(
                    "Ferramenta referencia agente "
                    "não oficial: "
                    f"{tool_id!r} -> "
                    f"{agent_id!r}."
                )

        if tool_id in FORBIDDEN_TOOL_IDS:
            raise RuntimeError(
                "Ferramenta proibida encontrada "
                "no catálogo: "
                f"{tool_id!r}."
            )


validate_tool_catalog()