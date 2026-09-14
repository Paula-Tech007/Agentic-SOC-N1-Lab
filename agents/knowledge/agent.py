"""
AG-08 — Knowledge / RAG Agent.

Responsável por validar e consolidar conhecimento recuperado
de fontes internas autorizadas.

Nesta fase, o agente NÃO executa diretamente a busca vetorial.

A recuperação real será conectada posteriormente através das
camadas:

- rag/ingestion;
- rag/embeddings;
- rag/index;
- rag/retrieval;
- tools/knowledge;
- Permission Engine.

Fluxo atual:

Consulta do caso
        ↓
Resultado de recuperação autorizado
        ↓
KnowledgeChunk
        ↓
AG-08 Knowledge / RAG
        ↓
KnowledgeResult
        ↓
Orchestrator
        ↓
CaseState.knowledge

Princípio:

A ferramenta recupera.
A fonte comprova.
A LLM pode interpretar.
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
from core.schemas import (
    KnowledgeChunk,
    KnowledgeResult,
)


class KnowledgeRAGAgent(BaseAgent):
    """
    AG-08 — Knowledge / RAG Agent.
    """

    agent_id = "AG-08"

    agent_name = "Knowledge/RAG Agent"

    description = (
        "Recuperar, validar e consolidar conhecimento "
        "interno proveniente de playbooks, runbooks, "
        "políticas e documentação autorizada."
    )

    allowed_tools: tuple[str, ...] = (
        "retrieve_knowledge",
        "search_playbooks",
        "search_runbooks",
        "search_policies",
        "search_mitre",
    )

    def run(
        self,
        request: AgentExecutionRequest,
    ) -> AgentWorkResult:
        """
        Valida chunks recuperados e produz
        um KnowledgeResult oficial.

        O input_payload deve fornecer:

        - query;
        - answer;
        - retrieved_chunks;
        - confidence;
        - evidence_references opcional.

        Nenhum chunk é inventado pelo agente.
        """

        snapshot = request.case_snapshot.to_dict()

        alert_data = snapshot.get("alert")

        if not isinstance(
            alert_data,
            Mapping,
        ):
            raise ValueError(
                "O snapshot precisa possuir "
                "um objeto 'alert'."
            )

        alert_id = self._required_string(
            alert_data.get("alert_id"),
            "alert.alert_id",
        )

        payload = request.input_payload.to_dict()

        query = self._required_string(
            payload.get("query"),
            "input_payload.query",
        )

        answer = self._required_string(
            payload.get("answer"),
            "input_payload.answer",
        )

        confidence = self._confidence(
            payload.get("confidence")
        )

        chunks_data = payload.get(
            "retrieved_chunks"
        )

        if not isinstance(
            chunks_data,
            (list, tuple),
        ):
            raise ValueError(
                "input_payload.retrieved_chunks precisa "
                "ser uma lista."
            )

        if not chunks_data:
            raise ValueError(
                "AG-08 exige pelo menos um chunk "
                "recuperado de fonte autorizada."
            )

        chunks = self._build_chunks(
            chunks_data
        )

        evidence_references = self._string_list(
            payload.get("evidence_references")
        )

        knowledge_id = payload.get(
            "knowledge_id"
        )

        if knowledge_id is None:
            knowledge_id = (
                self._create_knowledge_id()
            )

        knowledge_id = self._required_string(
            knowledge_id,
            "knowledge_id",
        )

        knowledge = KnowledgeResult(
            knowledge_id=knowledge_id,
            alert_id=alert_id,
            query=query,
            answer=answer,
            retrieved_chunks=chunks,
            evidence_references=evidence_references,
            confidence=confidence,
        )

        return AgentWorkResult(
            output={
                "result_reference": (
                    knowledge.knowledge_id
                ),
                "knowledge_result": (
                    knowledge.model_dump(
                        mode="json"
                    )
                ),
            },
            evidence_references=tuple(
                evidence_references
            ),
            messages=(
                (
                    "Conhecimento interno consolidado "
                    "pelo AG-08."
                ),
                (
                    "Somente chunks recuperados de "
                    "fontes fornecidas foram utilizados."
                ),
            ),
        )

    def _build_chunks(
        self,
        chunks_data: list[Any] | tuple[Any, ...],
    ) -> list[KnowledgeChunk]:
        """
        Valida todos os chunks utilizando o schema oficial
        KnowledgeChunk.
        """

        chunks: list[
            KnowledgeChunk
        ] = []

        seen_chunk_ids: set[str] = set()

        for position, item in enumerate(
            chunks_data,
            start=1,
        ):
            if not isinstance(
                item,
                Mapping,
            ):
                raise ValueError(
                    "Chunk na posição "
                    f"{position} precisa ser um objeto."
                )

            try:
                chunk = (
                    KnowledgeChunk.model_validate(
                        dict(item)
                    )
                )

            except Exception as exc:
                raise ValueError(
                    "KnowledgeChunk inválido na posição "
                    f"{position}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if (
                chunk.chunk_id
                in seen_chunk_ids
            ):
                raise ValueError(
                    "chunk_id duplicado: "
                    f"{chunk.chunk_id}"
                )

            seen_chunk_ids.add(
                chunk.chunk_id
            )

            chunks.append(
                chunk
            )

        return chunks

    @staticmethod
    def _confidence(
        value: Any,
    ) -> int:
        """
        Valida confiança do resultado.

        O valor precisa estar entre 0 e 100.
        """

        if isinstance(value, bool):
            raise ValueError(
                "confidence precisa ser um número inteiro."
            )

        if not isinstance(value, int):
            raise ValueError(
                "confidence precisa ser um número inteiro."
            )

        if value < 0 or value > 100:
            raise ValueError(
                "confidence precisa estar entre 0 e 100."
            )

        return value

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
    def _create_knowledge_id() -> str:
        """
        Gera identificador único do resultado de conhecimento.
        """

        return (
            "KNOW-"
            + uuid4().hex.upper()
        )


knowledge_rag_agent = KnowledgeRAGAgent()