"""
AG-06 — Asset Context Agent.

Responsável por validar e consolidar contexto de ativos
obtido por ferramentas autorizadas.

Nesta fase, o agente NÃO consulta diretamente:

- CMDB;
- EDR;
- inventário corporativo;
- Active Directory;
- scanners;
- plataformas externas.

As integrações reais serão implementadas posteriormente
na camada de Tools / Permission Engine.

Fluxo atual:

Resultado de ferramenta ou simulação controlada
        ↓
AG-06 Asset Context
        ↓
Validação
        ↓
AssetContext
        ↓
Orchestrator
        ↓
CaseState.assets

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
from core.schemas import AssetContext


class AssetContextAgent(BaseAgent):
    """
    AG-06 — Asset Context Agent.
    """

    agent_id = "AG-06"

    agent_name = "Asset Context Agent"

    description = (
        "Validar e consolidar contexto de ativos, "
        "criticidade, exposição, gerenciamento e EDR."
    )

    allowed_tools: tuple[str, ...] = (
        "lookup_asset",
        "lookup_asset_criticality",
        "lookup_asset_exposure",
        "lookup_edr_status",
        "lookup_asset_inventory",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Consolida informações de ativos recebidas
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

        assets_data = payload.get(
            "assets"
        )

        if not isinstance(
            assets_data,
            (list, tuple),
        ):
            raise ValueError(
                "input_payload.assets precisa "
                "ser uma lista."
            )

        if not assets_data:
            raise ValueError(
                "AG-06 exige pelo menos um contexto "
                "de ativo comprovado."
            )

        assets = self._build_assets(
            assets_data
        )

        evidence_references = self._string_list(
            payload.get("evidence_references")
        )

        queried_sources = self._build_sources(
            payload=payload,
            assets=assets,
        )

        analysis_id = payload.get(
            "asset_analysis_id"
        )

        if analysis_id is None:
            analysis_id = (
                self._create_analysis_id()
            )

        analysis_id = self._required_string(
            analysis_id,
            "asset_analysis_id",
        )

        summary = self._build_summary(
            alert_id=alert_id,
            assets=assets,
        )

        return AgentWorkResult(
            output={
                "result_reference": analysis_id,
                "alert_id": alert_id,
                "assets": [
                    asset.model_dump(
                        mode="json"
                    )
                    for asset in assets
                ],
                "queried_sources": queried_sources,
                "summary": summary,
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Contexto de ativos consolidado "
                    "pelo AG-06."
                ),
                (
                    "Nenhuma característica do ativo "
                    "foi inventada; somente dados "
                    "fornecidos foram utilizados."
                ),
            ),
        )

    def _build_assets(
        self,
        assets_data: list[Any] | tuple[Any, ...],
    ) -> list[AssetContext]:
        """
        Valida cada ativo utilizando o schema oficial
        AssetContext.
        """

        assets: list[
            AssetContext
        ] = []

        seen_asset_ids: set[str] = set()

        for position, item in enumerate(
            assets_data,
            start=1,
        ):
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Ativo na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                asset = (
                    AssetContext.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "AssetContext inválido na posição "
                    f"{position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if (
                asset.asset_id
                in seen_asset_ids
            ):
                raise ValueError(
                    "asset_id duplicado: "
                    f"{asset.asset_id}"
                )

            seen_asset_ids.add(
                asset.asset_id
            )

            assets.append(
                asset
            )

        return assets

    def _build_sources(
        self,
        payload: dict[str, Any],
        assets: list[AssetContext],
    ) -> list[str]:
        """
        Consolida fontes consultadas sem duplicidade.
        """

        sources = self._string_list(
            payload.get("queried_sources")
        )

        for asset in assets:
            if asset.source is None:
                continue

            source = asset.source.strip()

            if source and source not in sources:
                sources.append(source)

        return sources

    def _build_summary(
        self,
        alert_id: str,
        assets: list[AssetContext],
    ) -> str:
        """
        Produz resumo objetivo baseado somente nos
        AssetContext recebidos.
        """

        critical_assets = sum(
            1
            for asset in assets
            if asset.criticality.value == "CRITICAL"
        )

        internet_exposed = sum(
            1
            for asset in assets
            if asset.internet_exposed is True
        )

        unmanaged_assets = sum(
            1
            for asset in assets
            if asset.managed is False
        )

        without_edr = sum(
            1
            for asset in assets
            if asset.edr_installed is False
        )

        return (
            f"Análise de ativos do alerta {alert_id}: "
            f"{len(assets)} ativo(s) processado(s). "
            f"Ativos críticos: {critical_assets}. "
            f"Expostos à Internet: {internet_exposed}. "
            f"Não gerenciados: {unmanaged_assets}. "
            f"Sem EDR confirmado: {without_edr}."
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
        Gera identificador único da análise de ativo.
        """

        return (
            "ASSET-ANALYSIS-"
            + uuid4().hex.upper()
        )


asset_context_agent = AssetContextAgent()