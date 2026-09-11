"""
Primeiro teste oficial do Agentic SOC N1 Lab.

Objetivo:
Validar a comunicação entre:

Python
    ↓
core.llm
    ↓
Ollama
    ↓
qwen3:4b-instruct
"""

from core.config import APP_NAME, LLM_MODEL
from core.llm import ask_llm


def main() -> None:
    print("=" * 60)
    print(APP_NAME)
    print(f"Modelo: {LLM_MODEL}")
    print("=" * 60)

    system_prompt = """
Você é um analista defensivo de SOC N1.

Sua função é analisar eventos de segurança de forma objetiva.

Não invente fatos, indicadores ou evidências.

Quando uma informação não estiver disponível,
informe claramente que ela não foi fornecida.

Responda em português do Brasil.
"""

    user_prompt = """
Explique em uma única frase qual é a principal função
de um analista SOC N1.
"""

    response = ask_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    print()
    print("Resposta do modelo:")
    print()
    print(response)


if __name__ == "__main__":
    main()