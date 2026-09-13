"""
Schema oficial da camada de conhecimento / RAG
do Agentic SOC N1 Lab.

Representa a saída estruturada produzida pelo
AG-08 Knowledge / RAG Agent.

O agente deverá recuperar informações de fontes
autorizadas, como:

- playbooks;
- runbooks;
- políticas;
- documentação;
- MITRE ATT&CK;
- conhecimento operacional.

Toda resposta deve preservar a origem do conteúdo
recuperado.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class KnowledgeChunk(BaseModel):
    """
    Trecho individual recuperado pela camada RAG.
    """

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único do trecho recuperado.",
    )

    document_name: str = Field(
        ...,
        min_length=1,
        description="Nome do documento de origem.",
    )

    document_type: str = Field(
        ...,
        min_length=1,
        description=(
            "Tipo do documento, por exemplo playbook, "
            "runbook, policy ou mitre."
        ),
    )

    section: str | None = Field(
        default=None,
        description="Seção ou capítulo de origem.",
    )

    content: str = Field(
        ...,
        min_length=1,
        description="Conteúdo textual recuperado.",
    )

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de similaridade entre 0 e 1.",
    )

    source_path: str | None = Field(
        default=None,
        description="Caminho ou referência da fonte.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados adicionais do trecho.",
    )

    @field_validator(
        "document_name",
        "document_type",
        "content",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Impede campos obrigatórios vazios.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Documento, tipo e conteúdo não podem estar vazios."
            )

        return cleaned_value


class KnowledgeResult(BaseModel):
    """
    Resultado consolidado produzido pelo
    AG-08 Knowledge / RAG Agent.
    """

    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(
        ...,
        min_length=1,
        description="Identificador da consulta de conhecimento.",
    )

    alert_id: str = Field(
        ...,
        min_length=1,
        description="Alerta relacionado à consulta.",
    )

    query: str = Field(
        ...,
        min_length=1,
        description="Consulta utilizada na recuperação.",
    )

    answer: str = Field(
        ...,
        min_length=1,
        description=(
            "Resposta consolidada exclusivamente a partir "
            "das fontes recuperadas."
        ),
    )

    retrieved_chunks: list[KnowledgeChunk] = Field(
        ...,
        min_length=1,
        description=(
            "Trechos que sustentam a resposta. "
            "Pelo menos uma fonte é obrigatória."
        ),
    )

    evidence_references: list[str] = Field(
        default_factory=list,
        description="Evidências relacionadas à consulta.",
    )

    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confiança da resposta consolidada.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator(
        "query",
        "answer",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        """
        Impede consulta ou resposta vazia.
        """

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Query e resposta não podem estar vazias."
            )

        return cleaned_value