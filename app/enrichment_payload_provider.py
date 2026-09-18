"""
Provider oficial de payloads de enriquecimento
da Fase 7.3 do Agentic SOC N1 Lab.

Responsabilidades:

- obter evidência por ToolRuntime;
- transformar resultados de Tools em payloads
  compatíveis com os agentes especialistas;
- preservar a separação:

    ferramenta comprova;
    agente consolida/interpreta;

- não inventar reputação;
- não inventar estado de conta;
- não inventar características de ativo;
- falhar fechado quando não houver dados
  suficientes para construir o contrato.

Agentes suportados nesta etapa:

- AG-04 Threat Intelligence;
- AG-05 Identity Analyst;
- AG-06 Asset Context.

AG-08 permanece deliberadamente fail-closed
até a composição oficial do RAG ser conectada.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from typing import Any
from uuid import uuid4

from core.state import CaseState

from tools import (
    ToolRequest,
    ToolResult,
    ToolRuntime,
)


SUPPORTED_TOOL_AGENTS = (
    "AG-04",
    "AG-05",
    "AG-06",
)


class EnrichmentPayloadProvider:
    """
    Prepara input_payload para agentes
    de enriquecimento utilizando somente
    resultados obtidos pelo ToolRuntime.
    """

    def __init__(
        self,
        tool_runtime: ToolRuntime,
    ) -> None:
        if not isinstance(
            tool_runtime,
            ToolRuntime,
        ):
            raise TypeError(
                "tool_runtime precisa ser "
                "ToolRuntime."
            )

        self._tool_runtime = (
            tool_runtime
        )

    @property
    def tool_runtime(
        self,
    ) -> ToolRuntime:
        """
        Retorna o ToolRuntime utilizado.
        """

        return self._tool_runtime

    def build_payload(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Constrói o payload compatível
        com o especialista solicitado.

        Nenhuma chamada de agente ocorre aqui.
        """

        if not isinstance(
            case_state,
            CaseState,
        ):
            raise TypeError(
                "case_state precisa ser "
                "CaseState."
            )

        normalized_agent_id = (
            self._required_string(
                agent_id,
                "agent_id",
            )
        )

        if normalized_agent_id == "AG-04":
            return (
                self._build_threat_intel_payload(
                    case_state
                )
            )

        if normalized_agent_id == "AG-05":
            return (
                self._build_identity_payload(
                    case_state
                )
            )

        if normalized_agent_id == "AG-06":
            return (
                self._build_asset_payload(
                    case_state
                )
            )

        if normalized_agent_id == "AG-08":
            raise RuntimeError(
                "AG-08 exige composição RAG "
                "dedicada. Payload não pode "
                "ser inventado."
            )

        raise ValueError(
            "Agente não suportado pelo "
            "EnrichmentPayloadProvider: "
            f"{normalized_agent_id}."
        )

    # ============================================================
    # AG-04
    # ============================================================

    def _build_threat_intel_payload(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Consulta MISP para IOCs conhecidos
        e transforma cada consulta bem-sucedida
        em ThreatIntelFinding.

        Reputação e malícia permanecem
        desconhecidas quando a fonte não
        fornece esses valores explicitamente.
        """

        candidates = (
            self._ioc_candidates(
                case_state
            )
        )

        if not candidates:
            raise RuntimeError(
                "AG-04 solicitado sem IOC "
                "disponível no caso."
            )

        findings: list[
            dict[str, Any]
        ] = []

        errors: list[str] = []

        queried_sources: list[str] = []

        for candidate in candidates:
            try:
                tool_result = self._execute_tool(
                    case_state=case_state,
                    agent_id="AG-04",
                    tool_id="misp.search_ioc",
                    input_payload={
                        "ioc": candidate[
                            "value"
                        ],
                    },
                )

            except RuntimeError as exc:
                errors.append(
                    str(exc)
                )
                continue

            source = self._tool_source(
                tool_result,
                default="MISP",
            )

            if source not in queried_sources:
                queried_sources.append(
                    source
                )

            raw_result = (
                self._tool_output_result(
                    tool_result
                )
            )

            findings.append(
                {
                    "ioc_id": (
                        candidate["ioc_id"]
                    ),
                    "indicator_type": (
                        candidate[
                            "indicator_type"
                        ]
                    ),
                    "value": (
                        candidate["value"]
                    ),
                    "provider": source,
                    "reputation": (
                        self._explicit_string(
                            raw_result,
                            (
                                "reputation",
                                "verdict",
                            ),
                        )
                    ),
                    "malicious_confirmed": (
                        self._explicit_bool(
                            raw_result,
                            (
                                "malicious_confirmed",
                                "malicious",
                            ),
                        )
                    ),
                    "confidence": (
                        self._explicit_confidence(
                            raw_result
                        )
                    ),
                    "score": (
                        self._explicit_number(
                            raw_result,
                            (
                                "score",
                                "threat_score",
                            ),
                        )
                    ),
                    "tags": (
                        self._explicit_string_list(
                            raw_result,
                            (
                                "tags",
                            ),
                        )
                    ),
                    "details": {
                        "tool_id": (
                            tool_result.tool_id
                        ),
                        "result": raw_result,
                        "evidence": (
                            self._plain(
                                tool_result
                                .evidence_payload
                            )
                        ),
                    },
                }
            )

        if not findings:
            raise RuntimeError(
                "AG-04 não recebeu nenhum "
                "resultado comprovado do MISP."
            )

        return {
            "findings": findings,
            "queried_sources": (
                queried_sources
            ),
            "evidence_references": [],
            "errors": errors,
        }

    # ============================================================
    # AG-05
    # ============================================================

    def _build_identity_payload(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Consulta IAM para a identidade
        relacionada ao caso.

        Os quatro endpoints oficiais
        são utilizados quando disponíveis.
        """

        username = self._username_candidate(
            case_state
        )

        if username is None:
            raise RuntimeError(
                "AG-05 solicitado sem username "
                "disponível no caso."
            )

        tool_ids = (
            "iam.get_user",
            "iam.get_account_status",
            "iam.get_mfa_status",
            "iam.get_group_membership",
        )

        results: dict[
            str,
            dict[str, Any]
        ] = {}

        sources: list[str] = []

        errors: list[str] = []

        for tool_id in tool_ids:
            try:
                tool_result = self._execute_tool(
                    case_state=case_state,
                    agent_id="AG-05",
                    tool_id=tool_id,
                    input_payload={
                        "username": username,
                    },
                )

            except RuntimeError as exc:
                errors.append(
                    str(exc)
                )
                continue

            result_data = (
                self._tool_output_result(
                    tool_result
                )
            )

            if not isinstance(
                result_data,
                Mapping,
            ):
                errors.append(
                    f"{tool_id} retornou "
                    "resultado não estruturado."
                )
                continue

            results[
                tool_id
            ] = dict(
                result_data
            )

            source = self._tool_source(
                tool_result,
                default="IAM",
            )

            if source not in sources:
                sources.append(
                    source
                )

        if not results:
            raise RuntimeError(
                "AG-05 não recebeu nenhum "
                "resultado comprovado do IAM."
            )

        user_data = results.get(
            "iam.get_user",
            {},
        )

        account_data = results.get(
            "iam.get_account_status",
            {},
        )

        mfa_data = results.get(
            "iam.get_mfa_status",
            {},
        )

        group_data = results.get(
            "iam.get_group_membership",
            {},
        )

        identity_id = (
            self._first_string(
                (
                    user_data.get(
                        "identity_id"
                    ),
                    user_data.get(
                        "user_id"
                    ),
                    user_data.get(
                        "id"
                    ),
                )
            )
        )

        if identity_id is None:
            identity_id = self._stable_id(
                prefix="IDENTITY",
                value=username,
            )

        mfa_enabled = (
            self._first_bool(
                (
                    mfa_data.get(
                        "mfa_enabled"
                    ),
                    mfa_data.get(
                        "enabled"
                    ),
                )
            )
        )

        account_enabled = (
            self._first_bool(
                (
                    account_data.get(
                        "account_enabled"
                    ),
                    account_data.get(
                        "enabled"
                    ),
                    user_data.get(
                        "account_enabled"
                    ),
                    user_data.get(
                        "enabled"
                    ),
                )
            )
        )

        account_exists = (
            self._first_bool(
                (
                    account_data.get(
                        "account_exists"
                    ),
                    account_data.get(
                        "exists"
                    ),
                    user_data.get(
                        "account_exists"
                    ),
                    user_data.get(
                        "exists"
                    ),
                )
            )
        )

        privileged = (
            self._first_bool(
                (
                    account_data.get(
                        "privileged"
                    ),
                    user_data.get(
                        "privileged"
                    ),
                )
            )
        )

        confidence = max(
            self._explicit_confidence(
                data
            )
            for data in results.values()
        )

        risk_factors: list[str] = []

        for data in results.values():
            for item in (
                self._explicit_string_list(
                    data,
                    (
                        "risk_factors",
                    ),
                )
            ):
                if item not in risk_factors:
                    risk_factors.append(
                        item
                    )

        source_value = (
            sources[0]
            if sources
            else "IAM"
        )

        identity = {
            "identity_id": identity_id,
            "username": username,
            "email": (
                self._first_string(
                    (
                        user_data.get(
                            "email"
                        ),
                        user_data.get(
                            "mail"
                        ),
                    )
                )
            ),
            "display_name": (
                self._first_string(
                    (
                        user_data.get(
                            "display_name"
                        ),
                        user_data.get(
                            "name"
                        ),
                    )
                )
            ),
            "account_exists": (
                account_exists
            ),
            "account_enabled": (
                account_enabled
            ),
            "privileged": privileged,
            "mfa_enabled": (
                mfa_enabled
            ),
            "department": (
                self._first_string(
                    (
                        user_data.get(
                            "department"
                        ),
                    )
                )
            ),
            "role": (
                self._first_string(
                    (
                        user_data.get(
                            "role"
                        ),
                        user_data.get(
                            "job_title"
                        ),
                    )
                )
            ),
            "last_login": (
                self._first_string(
                    (
                        account_data.get(
                            "last_login"
                        ),
                        user_data.get(
                            "last_login"
                        ),
                    )
                )
            ),
            "failed_login_count": (
                self._first_non_negative_int(
                    (
                        account_data.get(
                            "failed_login_count"
                        ),
                        user_data.get(
                            "failed_login_count"
                        ),
                    )
                )
            ),
            "source": source_value,
            "confidence": confidence,
            "risk_factors": (
                risk_factors
            ),
            "metadata": {
                "tool_results": results,
                "group_membership": (
                    group_data
                ),
                "errors": errors,
            },
        }

        return {
            "identities": [
                identity
            ],
            "queried_sources": sources,
            "evidence_references": [],
        }

    # ============================================================
    # AG-06
    # ============================================================

    def _build_asset_payload(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Consulta Asset / CMDB.

        Preferência:

        1. asset_id;
        2. endereço IP.

        Nunca cria hostname ou asset_id
        sem origem observável.
        """

        raw_event = self._raw_event(
            case_state
        )

        asset_id = self._first_string(
            (
                raw_event.get(
                    "asset_id"
                ),
                raw_event.get(
                    "host_id"
                ),
                raw_event.get(
                    "device_id"
                ),
            )
        )

        hostname = self._first_string(
            (
                raw_event.get(
                    "hostname"
                ),
                raw_event.get(
                    "host"
                ),
                raw_event.get(
                    "computer_name"
                ),
            )
        )

        ip_candidate = self._first_string(
            (
                raw_event.get(
                    "destination_ip"
                ),
                raw_event.get(
                    "dest_ip"
                ),
                raw_event.get(
                    "source_ip"
                ),
                raw_event.get(
                    "ip"
                ),
            )
        )

        base_tool_id: str

        base_payload: dict[
            str,
            Any
        ]

        if asset_id is not None:
            base_tool_id = (
                "asset.get_asset"
            )

            base_payload = {
                "asset_id": asset_id,
            }

        elif ip_candidate is not None:
            base_tool_id = (
                "asset.get_ip_context"
            )

            base_payload = {
                "ip_address": (
                    ip_candidate
                ),
            }

        else:
            raise RuntimeError(
                "AG-06 solicitado sem asset_id "
                "ou endereço IP disponível."
            )

        base_result = self._execute_tool(
            case_state=case_state,
            agent_id="AG-06",
            tool_id=base_tool_id,
            input_payload=base_payload,
        )

        base_data = (
            self._tool_output_result(
                base_result
            )
        )

        if not isinstance(
            base_data,
            Mapping,
        ):
            raise RuntimeError(
                f"{base_tool_id} retornou "
                "resultado não estruturado."
            )

        base_data = dict(
            base_data
        )

        resolved_asset_id = (
            self._first_string(
                (
                    base_data.get(
                        "asset_id"
                    ),
                    base_data.get(
                        "id"
                    ),
                    asset_id,
                )
            )
        )

        resolved_hostname = (
            self._first_string(
                (
                    base_data.get(
                        "hostname"
                    ),
                    base_data.get(
                        "host_name"
                    ),
                    base_data.get(
                        "name"
                    ),
                    hostname,
                )
            )
        )

        if resolved_asset_id is None:
            raise RuntimeError(
                "Asset / CMDB não retornou "
                "asset_id comprovado."
            )

        if resolved_hostname is None:
            raise RuntimeError(
                "Asset / CMDB não retornou "
                "hostname comprovado."
            )

        supplemental_results: dict[
            str,
            dict[str, Any]
        ] = {}

        errors: list[str] = []

        for tool_id in (
            "asset.get_criticality",
            "asset.get_edr_status",
        ):
            try:
                result = self._execute_tool(
                    case_state=case_state,
                    agent_id="AG-06",
                    tool_id=tool_id,
                    input_payload={
                        "asset_id": (
                            resolved_asset_id
                        ),
                    },
                )

            except RuntimeError as exc:
                errors.append(
                    str(exc)
                )
                continue

            result_data = (
                self._tool_output_result(
                    result
                )
            )

            if isinstance(
                result_data,
                Mapping,
            ):
                supplemental_results[
                    tool_id
                ] = dict(
                    result_data
                )

        criticality_data = (
            supplemental_results.get(
                "asset.get_criticality",
                {},
            )
        )

        edr_data = (
            supplemental_results.get(
                "asset.get_edr_status",
                {},
            )
        )

        source = self._tool_source(
            base_result,
            default="ASSET",
        )

        ip_addresses: list[str] = []

        raw_ips = base_data.get(
            "ip_addresses"
        )

        if isinstance(
            raw_ips,
            (list, tuple),
        ):
            for value in raw_ips:
                normalized = (
                    self._optional_string(
                        value
                    )
                )

                if (
                    normalized is not None
                    and normalized
                    not in ip_addresses
                ):
                    ip_addresses.append(
                        normalized
                    )

        single_ip = self._first_string(
            (
                base_data.get(
                    "ip_address"
                ),
                ip_candidate,
            )
        )

        if (
            single_ip is not None
            and single_ip
            not in ip_addresses
        ):
            ip_addresses.append(
                single_ip
            )

        criticality = self._first_string(
            (
                criticality_data.get(
                    "criticality"
                ),
                base_data.get(
                    "criticality"
                ),
            )
        )

        if (
            criticality is not None
            and criticality.upper()
            in {
                "INFORMATIONAL",
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            }
        ):
            criticality = (
                criticality.upper()
            )

        else:
            criticality = None

        asset: dict[str, Any] = {
            "asset_id": (
                resolved_asset_id
            ),
            "hostname": (
                resolved_hostname
            ),
            "asset_type": (
                self._first_string(
                    (
                        base_data.get(
                            "asset_type"
                        ),
                        base_data.get(
                            "type"
                        ),
                    )
                )
            ),
            "operating_system": (
                self._first_string(
                    (
                        base_data.get(
                            "operating_system"
                        ),
                        base_data.get(
                            "os"
                        ),
                    )
                )
            ),
            "owner": (
                self._first_string(
                    (
                        base_data.get(
                            "owner"
                        ),
                    )
                )
            ),
            "department": (
                self._first_string(
                    (
                        base_data.get(
                            "department"
                        ),
                    )
                )
            ),
            "environment": (
                self._first_string(
                    (
                        base_data.get(
                            "environment"
                        ),
                    )
                )
            ),
            "internet_exposed": (
                self._first_bool(
                    (
                        base_data.get(
                            "internet_exposed"
                        ),
                    )
                )
            ),
            "managed": (
                self._first_bool(
                    (
                        base_data.get(
                            "managed"
                        ),
                    )
                )
            ),
            "edr_installed": (
                self._first_bool(
                    (
                        edr_data.get(
                            "edr_installed"
                        ),
                        edr_data.get(
                            "installed"
                        ),
                        edr_data.get(
                            "enabled"
                        ),
                        base_data.get(
                            "edr_installed"
                        ),
                    )
                )
            ),
            "ip_addresses": (
                ip_addresses
            ),
            "source": source,
            "confidence": max(
                self._explicit_confidence(
                    base_data
                ),
                self._explicit_confidence(
                    criticality_data
                ),
                self._explicit_confidence(
                    edr_data
                ),
            ),
            "risk_factors": (
                self._explicit_string_list(
                    base_data,
                    (
                        "risk_factors",
                    ),
                )
            ),
            "metadata": {
                "base_tool": (
                    base_tool_id
                ),
                "base_result": (
                    base_data
                ),
                "supplemental_results": (
                    supplemental_results
                ),
                "errors": errors,
            },
        }

        if criticality is not None:
            asset[
                "criticality"
            ] = criticality

        return {
            "assets": [
                asset
            ],
            "queried_sources": [
                source
            ],
            "evidence_references": [],
        }

    # ============================================================
    # CANDIDATOS
    # ============================================================

    def _ioc_candidates(
        self,
        case_state: CaseState,
    ) -> list[
        dict[str, str]
    ]:
        """
        Obtém IOCs existentes no CaseState
        ou, na ausência deles, indicadores
        explicitamente presentes no raw_event.
        """

        candidates: list[
            dict[str, str]
        ] = []

        seen_values: set[str] = set()

        for ioc in case_state.iocs:
            data = self._model_data(
                ioc
            )

            value = self._optional_string(
                data.get(
                    "value"
                )
            )

            if value is None:
                continue

            if value in seen_values:
                continue

            indicator_type = (
                self._enum_or_string(
                    data.get(
                        "indicator_type"
                    )
                )
            )

            if indicator_type is None:
                indicator_type = (
                    self._infer_indicator_type(
                        value
                    )
                )

            ioc_id = self._optional_string(
                data.get(
                    "ioc_id"
                )
            )

            if ioc_id is None:
                ioc_id = self._stable_id(
                    prefix="IOC",
                    value=value,
                )

            candidates.append(
                {
                    "ioc_id": ioc_id,
                    "indicator_type": (
                        indicator_type
                    ),
                    "value": value,
                }
            )

            seen_values.add(
                value
            )

        if candidates:
            return candidates

        raw_event = self._raw_event(
            case_state
        )

        key_types = (
            (
                "source_ip",
                "IP",
            ),
            (
                "destination_ip",
                "IP",
            ),
            (
                "dest_ip",
                "IP",
            ),
            (
                "ip",
                "IP",
            ),
            (
                "domain",
                "DOMAIN",
            ),
            (
                "url",
                "URL",
            ),
            (
                "hash",
                "HASH",
            ),
            (
                "file_hash",
                "HASH",
            ),
            (
                "sha256",
                "HASH",
            ),
            (
                "sha1",
                "HASH",
            ),
            (
                "md5",
                "HASH",
            ),
            (
                "email",
                "EMAIL",
            ),
        )

        for key, indicator_type in key_types:
            value = self._optional_string(
                raw_event.get(
                    key
                )
            )

            if (
                value is None
                or value in seen_values
            ):
                continue

            candidates.append(
                {
                    "ioc_id": (
                        self._stable_id(
                            prefix="IOC",
                            value=value,
                        )
                    ),
                    "indicator_type": (
                        indicator_type
                    ),
                    "value": value,
                }
            )

            seen_values.add(
                value
            )

        return candidates

    def _username_candidate(
        self,
        case_state: CaseState,
    ) -> str | None:
        """
        Obtém username já existente
        ou explicitamente presente
        no raw_event.
        """

        for identity in (
            case_state.identities
        ):
            data = self._model_data(
                identity
            )

            username = (
                self._optional_string(
                    data.get(
                        "username"
                    )
                )
            )

            if username is not None:
                return username

        raw_event = self._raw_event(
            case_state
        )

        return self._first_string(
            (
                raw_event.get(
                    "username"
                ),
                raw_event.get(
                    "user"
                ),
                raw_event.get(
                    "account"
                ),
                raw_event.get(
                    "principal"
                ),
            )
        )

    # ============================================================
    # TOOLRUNTIME
    # ============================================================

    def _execute_tool(
        self,
        *,
        case_state: CaseState,
        agent_id: str,
        tool_id: str,
        input_payload: Mapping[
            str,
            Any,
        ],
    ) -> ToolResult:
        """
        Executa uma ToolRequest vinculada
        ao agente/caso/correlation corretos.

        ToolRuntime continua responsável
        por autorização, retry e fail-closed.
        """

        token = (
            uuid4()
            .hex
            .upper()
        )

        request = ToolRequest(
            request_id=(
                f"REQ-{agent_id}-"
                f"{token[:16]}"
            ),
            execution_id=(
                f"EXEC-{agent_id}-"
                f"{token[16:]}"
            ),
            agent_id=agent_id,
            case_id=case_state.case_id,
            correlation_id=(
                case_state.correlation_id
            ),
            tool_id=tool_id,
            input_payload=dict(
                input_payload
            ),
        )

        result = (
            self._tool_runtime
            .execute(
                request
            )
        )

        if not result.success:
            detail = (
                result.error_message
                or result.error_code
                or "erro não informado"
            )

            raise RuntimeError(
                f"{tool_id} falhou: "
                f"{detail}"
            )

        return result

    # ============================================================
    # HELPERS
    # ============================================================

    def _raw_event(
        self,
        case_state: CaseState,
    ) -> dict[str, Any]:
        """
        Retorna cópia simples do raw_event.
        """

        return dict(
            self._plain(
                case_state
                .alert
                .event
                .raw_event
            )
        )

    def _tool_output_result(
        self,
        result: ToolResult,
    ) -> Any:
        """
        Extrai somente output_payload.result.
        """

        output = self._plain(
            result.output_payload
        )

        if not isinstance(
            output,
            Mapping,
        ):
            raise RuntimeError(
                f"{result.tool_id} retornou "
                "output_payload inválido."
            )

        if "result" not in output:
            raise RuntimeError(
                f"{result.tool_id} não retornou "
                "output_payload.result."
            )

        return output[
            "result"
        ]

    def _tool_source(
        self,
        result: ToolResult,
        *,
        default: str,
    ) -> str:
        """
        Obtém provider/source da evidência.
        """

        evidence = self._plain(
            result.evidence_payload
        )

        if isinstance(
            evidence,
            Mapping,
        ):
            provider = self._first_string(
                (
                    evidence.get(
                        "provider"
                    ),
                    evidence.get(
                        "source"
                    ),
                )
            )

            if provider is not None:
                return provider

        return default

    @classmethod
    def _plain(
        cls,
        value: Any,
    ) -> Any:
        """
        Converte FrozenDict/tuple/Mapping
        para estruturas Python simples.
        """

        if isinstance(
            value,
            Mapping,
        ):
            return {
                str(key): cls._plain(
                    item
                )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            tuple,
        ):
            return [
                cls._plain(
                    item
                )
                for item in value
            ]

        if isinstance(
            value,
            list,
        ):
            return [
                cls._plain(
                    item
                )
                for item in value
            ]

        return value

    @classmethod
    def _model_data(
        cls,
        value: Any,
    ) -> dict[str, Any]:
        """
        Converte schema Pydantic ou Mapping
        em dicionário simples.
        """

        if hasattr(
            value,
            "model_dump",
        ):
            return dict(
                cls._plain(
                    value.model_dump(
                        mode="python"
                    )
                )
            )

        if isinstance(
            value,
            Mapping,
        ):
            return dict(
                cls._plain(
                    value
                )
            )

        return {}

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        normalized = (
            EnrichmentPayloadProvider
            ._optional_string(
                value
            )
        )

        if normalized is None:
            raise ValueError(
                f"{field_name} precisa ser "
                "uma string não vazia."
            )

        return normalized

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if not isinstance(
            value,
            str,
        ):
            return None

        normalized = (
            value.strip()
        )

        if not normalized:
            return None

        return normalized

    @classmethod
    def _first_string(
        cls,
        values: tuple[
            Any,
            ...,
        ],
    ) -> str | None:
        for value in values:
            normalized = (
                cls._optional_string(
                    value
                )
            )

            if normalized is not None:
                return normalized

        return None

    @staticmethod
    def _first_bool(
        values: tuple[
            Any,
            ...,
        ],
    ) -> bool | None:
        for value in values:
            if isinstance(
                value,
                bool,
            ):
                return value

        return None

    @staticmethod
    def _first_non_negative_int(
        values: tuple[
            Any,
            ...,
        ],
    ) -> int | None:
        for value in values:
            if (
                isinstance(
                    value,
                    int,
                )
                and not isinstance(
                    value,
                    bool,
                )
                and value >= 0
            ):
                return value

        return None

    @classmethod
    def _explicit_string(
        cls,
        data: Any,
        keys: tuple[
            str,
            ...,
        ],
    ) -> str | None:
        if not isinstance(
            data,
            Mapping,
        ):
            return None

        return cls._first_string(
            tuple(
                data.get(
                    key
                )
                for key in keys
            )
        )

    @staticmethod
    def _explicit_bool(
        data: Any,
        keys: tuple[
            str,
            ...,
        ],
    ) -> bool | None:
        if not isinstance(
            data,
            Mapping,
        ):
            return None

        for key in keys:
            value = data.get(
                key
            )

            if isinstance(
                value,
                bool,
            ):
                return value

        return None

    @staticmethod
    def _explicit_number(
        data: Any,
        keys: tuple[
            str,
            ...,
        ],
    ) -> float | None:
        if not isinstance(
            data,
            Mapping,
        ):
            return None

        for key in keys:
            value = data.get(
                key
            )

            if (
                isinstance(
                    value,
                    (int, float),
                )
                and not isinstance(
                    value,
                    bool,
                )
            ):
                return float(
                    value
                )

        return None

    @staticmethod
    def _explicit_confidence(
        data: Any,
    ) -> int:
        if not isinstance(
            data,
            Mapping,
        ):
            return 0

        value = data.get(
            "confidence"
        )

        if (
            isinstance(
                value,
                int,
            )
            and not isinstance(
                value,
                bool,
            )
            and 0 <= value <= 100
        ):
            return value

        return 0

    @classmethod
    def _explicit_string_list(
        cls,
        data: Any,
        keys: tuple[
            str,
            ...,
        ],
    ) -> list[str]:
        if not isinstance(
            data,
            Mapping,
        ):
            return []

        for key in keys:
            value = data.get(
                key
            )

            if not isinstance(
                value,
                (list, tuple),
            ):
                continue

            output: list[str] = []

            for item in value:
                normalized = (
                    cls._optional_string(
                        item
                    )
                )

                if (
                    normalized is not None
                    and normalized
                    not in output
                ):
                    output.append(
                        normalized
                    )

            return output

        return []

    @staticmethod
    def _enum_or_string(
        value: Any,
    ) -> str | None:
        if isinstance(
            value,
            str,
        ):
            normalized = (
                value.strip()
            )

            return (
                normalized
                if normalized
                else None
            )

        enum_value = getattr(
            value,
            "value",
            None,
        )

        if isinstance(
            enum_value,
            str,
        ):
            normalized = (
                enum_value.strip()
            )

            return (
                normalized
                if normalized
                else None
            )

        return None

    @staticmethod
    def _infer_indicator_type(
        value: str,
    ) -> str:
        """
        Inferência estrutural conservadora
        usada apenas para classificar
        o formato do indicador.

        Não infere reputação ou malícia.
        """

        normalized = (
            value.strip()
        )

        if "://" in normalized:
            return "URL"

        if "@" in normalized:
            return "EMAIL"

        hex_chars = set(
            "0123456789abcdefABCDEF"
        )

        if (
            len(normalized)
            in {
                32,
                40,
                64,
                128,
            }
            and set(normalized)
            <= hex_chars
        ):
            return "HASH"

        parts = normalized.split(
            "."
        )

        if (
            len(parts) == 4
            and all(
                part.isdigit()
                for part in parts
            )
        ):
            return "IP"

        return "DOMAIN"

    @staticmethod
    def _stable_id(
        *,
        prefix: str,
        value: str,
    ) -> str:
        """
        Cria somente um identificador interno
        determinístico.

        Não representa evidência nem conclusão.
        """

        digest = (
            sha256(
                value.encode(
                    "utf-8"
                )
            )
            .hexdigest()
            .upper()
        )

        return (
            f"{prefix}-AUTO-"
            f"{digest[:12]}"
        )


__all__ = [
    "EnrichmentPayloadProvider",
    "SUPPORTED_TOOL_AGENTS",
]