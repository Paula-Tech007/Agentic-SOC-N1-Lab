"""
AG-05 — Identity Analyst Agent.

Responsável por validar e consolidar contexto de identidade
obtido por ferramentas autorizadas.

Nesta fase, o agente NÃO consulta diretamente:

- Active Directory;
- Microsoft Entra ID;
- LDAP;
- IAM corporativo;
- bancos de identidade.

As integrações reais serão implementadas posteriormente
na camada de Tools / Permission Engine.

Fluxo atual:

Resultado de ferramenta ou simulação controlada
        ↓
AG-05 Identity Analyst
        ↓
Validação
        ↓
IdentityContext
        ↓
Orchestrator
        ↓
CaseState.identities

Princípio:

A ferramenta comprova.
O agente estrutura.
O Orchestrator aplica no CaseState.
"""

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from core.orchestrator import (
    AgentExecutionRequest,
    AgentWorkResult,
    BaseAgent,
)
from core.schemas import IdentityContext


class IdentityAnalystAgent(BaseAgent):
    """
    AG-05 — Identity Analyst Agent.
    """

    agent_id = "AG-05"

    agent_name = "Identity Analyst Agent"

    description = (
        "Validar e consolidar contexto de identidade, "
        "conta, privilégios, MFA e autenticações."
    )

    allowed_tools: tuple[str, ...] = (
        "lookup_identity",
        "lookup_account_status",
        "lookup_mfa_status",
        "lookup_identity_privileges",
        "lookup_authentication_history",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Consolida informações de identidade recebidas
        de ferramenta autorizada ou simulação controlada.
        """

        snapshot = request.case_snapshot.to_dict()

        alert_data = snapshot.get("alert")

        if not isinstance(alert_data, Mapping):
            raise ValueError(
                "O snapshot precisa possuir "
                "um objeto 'alert'."
            )

        alert_id = self._required_string(
            alert_data.get("alert_id"),
            "alert.alert_id",
        )

        payload = request.input_payload.to_dict()

        identities_data = payload.get(
            "identities"
        )

        if not isinstance(
            identities_data,
            (list, tuple),
        ):
            raise ValueError(
                "input_payload.identities precisa "
                "ser uma lista."
            )

        if not identities_data:
            raise ValueError(
                "AG-05 exige pelo menos um contexto "
                "de identidade comprovado."
            )

        identities = self._build_identities(
            identities_data
        )

        evidence_references = self._string_list(
            payload.get("evidence_references")
        )

        queried_sources = self._build_sources(
            payload=payload,
            identities=identities,
        )

        analysis_id = payload.get(
            "identity_analysis_id"
        )

        if analysis_id is None:
            analysis_id = (
                self._create_analysis_id()
            )

        analysis_id = self._required_string(
            analysis_id,
            "identity_analysis_id",
        )

        summary = self._build_summary(
            alert_id=alert_id,
            identities=identities,
        )

        return AgentWorkResult(
            output={
                "result_reference": analysis_id,
                "alert_id": alert_id,
                "identities": [
                    identity.model_dump(
                        mode="json"
                    )
                    for identity in identities
                ],
                "queried_sources": queried_sources,
                "summary": summary,
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Contexto de identidade consolidado "
                    "pelo AG-05."
                ),
                (
                    "Nenhuma informação de conta foi "
                    "inventada; somente dados fornecidos "
                    "foram utilizados."
                ),
            ),
        )

    def _build_identities(
        self,
        identities_data: list[Any] | tuple[Any, ...],
    ) -> list[IdentityContext]:
        """
        Valida cada identidade utilizando o schema oficial
        IdentityContext.
        """

        identities: list[
            IdentityContext
        ] = []

        seen_identity_ids: set[str] = set()

        for position, item in enumerate(
            identities_data,
            start=1,
        ):
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Identidade na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                identity = (
                    IdentityContext.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "IdentityContext inválido na posição "
                    f"{position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if (
                identity.identity_id
                in seen_identity_ids
            ):
                raise ValueError(
                    "identity_id duplicado: "
                    f"{identity.identity_id}"
                )

            seen_identity_ids.add(
                identity.identity_id
            )

            identities.append(
                identity
            )

        return identities

    def _build_sources(
        self,
        payload: dict[str, Any],
        identities: list[IdentityContext],
    ) -> list[str]:
        """
        Consolida fontes consultadas sem duplicidade.
        """

        sources = self._string_list(
            payload.get("queried_sources")
        )

        for identity in identities:
            if identity.source is None:
                continue

            source = identity.source.strip()

            if source and source not in sources:
                sources.append(source)

        return sources

    def _build_summary(
        self,
        alert_id: str,
        identities: list[IdentityContext],
    ) -> str:
        """
        Produz resumo objetivo baseado somente nos
        IdentityContext recebidos.
        """

        existing_accounts = sum(
            1
            for identity in identities
            if identity.account_exists is True
        )

        enabled_accounts = sum(
            1
            for identity in identities
            if identity.account_enabled is True
        )

        privileged_accounts = sum(
            1
            for identity in identities
            if identity.privileged is True
        )

        mfa_disabled = sum(
            1
            for identity in identities
            if identity.mfa_enabled is False
        )

        return (
            f"Análise de identidade do alerta {alert_id}: "
            f"{len(identities)} identidade(s) processada(s). "
            f"Contas existentes confirmadas: "
            f"{existing_accounts}. "
            f"Contas habilitadas: {enabled_accounts}. "
            f"Contas privilegiadas: "
            f"{privileged_accounts}. "
            f"Contas com MFA explicitamente desabilitado: "
            f"{mfa_disabled}."
        )

    @staticmethod
    def _string_list(
        value: Any,
    ) -> list[str]:
        """
        Normaliza listas de strings.
        """

        if value is None:
            return []

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise ValueError(
                "Era esperada uma lista de strings."
            )

        result: list[str] = []

        for item in value:
            if not isinstance(item, str):
                raise ValueError(
                    "A lista contém valor "
                    "que não é string."
                )

            cleaned = item.strip()

            if cleaned and cleaned not in result:
                result.append(cleaned)

        return result

    @staticmethod
    def _required_string(
        value: Any,
        field_name: str,
    ) -> str:
        """
        Valida campo textual obrigatório.
        """

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} precisa ser uma string."
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} não pode ser vazio."
            )

        return cleaned

    @staticmethod
    def _create_analysis_id() -> str:
        """
        Gera identificador único da análise de identidade.
        """

        return (
            "IDENTITY-ANALYSIS-"
            + uuid4().hex.upper()
        )


identity_analyst_agent = (
    IdentityAnalystAgent()
)