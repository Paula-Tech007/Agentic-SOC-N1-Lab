"""
Configurações centrais do Agentic SOC N1 Lab.

Este arquivo concentra parâmetros globais utilizados pelos
agentes, pelo orquestrador, pelo LLM e pelos mecanismos
de governança do laboratório.
"""

# ============================================================
# PROJETO
# ============================================================

APP_NAME = "Agentic SOC N1 Lab"
APP_VERSION = "0.1.0"
ENVIRONMENT = "lab"


# ============================================================
# OLLAMA / IA
# ============================================================

OLLAMA_HOST = "http://localhost:11434"

LLM_MODEL = "qwen3:4b-instruct"

EMBEDDING_MODEL = "embeddinggemma"


# ============================================================
# AGENTES
# ============================================================

MAX_AGENT_STEPS = 20

MAX_REFLECTION_RETRIES = 2

AGENT_TIMEOUT_SECONDS = 30


# ============================================================
# SOC / DECISÃO
# ============================================================

N1_AUTO_CLOSE_MIN_CONFIDENCE = 90

SUPPORTED_SEVERITIES = (
    "INFORMATIONAL",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
)

FINAL_CLASSIFICATIONS = (
    "FALSE_POSITIVE",
    "BENIGN_POSITIVE",
    "SUSPICIOUS",
    "CONFIRMED_INCIDENT",
    "INCONCLUSIVE",
)

FINAL_DECISIONS = (
    "CLOSED_N1",
    "ESCALATED_N2",
    "WAITING_HUMAN",
)


# ============================================================
# SEGURANÇA / GOVERNANÇA
# ============================================================

DENY_BY_DEFAULT = True

ALLOW_CRITICAL_AUTONOMOUS_ACTIONS = False

FAIL_CLOSED = True


# ============================================================
# LOGS
# ============================================================

LOG_LEVEL = "INFO"

LOG_DIRECTORY = "logs"