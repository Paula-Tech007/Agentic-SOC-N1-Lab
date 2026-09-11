"""
Cliente central de LLM do Agentic SOC N1 Lab.

Este módulo é responsável pela comunicação entre o sistema
Python e o modelo local executado pelo Ollama.
"""

from ollama import Client, ResponseError

from core.config import (
    LLM_MODEL,
    OLLAMA_HOST,
)


class OllamaLLMClient:
    """
    Cliente central utilizado pelos agentes do SOC para conversar
    com o modelo local configurado no Ollama.
    """

    def __init__(self) -> None:
        self.model = LLM_MODEL

        self.client = Client(
            host=OLLAMA_HOST,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Envia uma mensagem ao modelo local.

        Args:
            system_prompt: instruções fixas do agente.
            user_prompt: conteúdo da tarefa atual.

        Returns:
            Texto retornado pelo modelo.
        """

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
            )

            content = response.message.content

            if not content:
                raise RuntimeError(
                    "O modelo respondeu sem conteúdo."
                )

            return content.strip()

        except ResponseError as exc:
            raise RuntimeError(
                f"Erro retornado pelo Ollama: {exc.error}"
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"Falha na comunicação com o Ollama: {exc}"
            ) from exc


llm_client = OllamaLLMClient()


def ask_llm(
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Função simples para os agentes enviarem solicitações ao LLM.
    """

    return llm_client.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )