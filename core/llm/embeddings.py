"""
Cliente de embeddings do Agentic SOC N1 Lab.

Responsável por transformar textos em vetores numéricos
utilizando o modelo local configurado no Ollama.

Esses vetores serão utilizados posteriormente pelo RAG
para busca semântica em playbooks, runbooks e políticas.
"""

from ollama import Client, ResponseError

from core.config import EMBEDDING_MODEL, OLLAMA_HOST


class OllamaEmbeddingClient:
    """
    Cliente central para geração de embeddings.
    """

    def __init__(self) -> None:
        self.model = EMBEDDING_MODEL

        self.client = Client(
            host=OLLAMA_HOST,
        )

    def embed(self, text: str) -> list[float]:
        """
        Transforma um texto em um vetor numérico.

        Args:
            text: texto que será convertido em embedding.

        Returns:
            Vetor de números do embedding.
        """

        if not text.strip():
            raise ValueError(
                "O texto para geração de embedding não pode estar vazio."
            )

        try:
            response = self.client.embed(
                model=self.model,
                input=text,
            )

            if not response.embeddings:
                raise RuntimeError(
                    "O modelo não retornou nenhum embedding."
                )

            return list(response.embeddings[0])

        except ResponseError as exc:
            raise RuntimeError(
                f"Erro retornado pelo Ollama ao gerar embedding: {exc.error}"
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"Falha ao gerar embedding: {exc}"
            ) from exc


embedding_client = OllamaEmbeddingClient()


def create_embedding(text: str) -> list[float]:
    """
    Interface simples para geração de embedding.
    """

    return embedding_client.embed(text)