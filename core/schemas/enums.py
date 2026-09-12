"""
Enums oficiais do Agentic SOC N1 Lab.

Este módulo contém os valores padronizados utilizados em todo
o sistema.

O objetivo é impedir que diferentes agentes utilizem nomes
diferentes para representar o mesmo estado, decisão ou tipo
de informação.
"""

from enum import StrEnum


# ============================================================
# ESTADOS DO CASO
# ============================================================


class CaseStatus(StrEnum):
    """
    Estados possíveis de um caso dentro do workflow do SOC.
    """

    RECEIVED = "RECEIVED"
    NORMALIZING = "NORMALIZING"
    TRIAGING = "TRIAGING"
    ENRICHING = "ENRICHING"
    INVESTIGATING = "INVESTIGATING"
    CORRELATING = "CORRELATING"
    REVIEWING = "REVIEWING"
    DOCUMENTING = "DOCUMENTING"
    DECIDING = "DECIDING"

    WAITING_DATA = "WAITING_DATA"
    WAITING_HUMAN = "WAITING_HUMAN"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    CLOSED_N1 = "CLOSED_N1"
    ESCALATED_N2 = "ESCALATED_N2"


# ============================================================
# ESTADOS DOS AGENTES
# ============================================================


class AgentStatus(StrEnum):
    """
    Estado de execução de um agente.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ============================================================
# SEVERIDADE
# ============================================================


class Severity(StrEnum):
    """
    Níveis oficiais de severidade.
    """

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ============================================================
# CLASSIFICAÇÃO FINAL
# ============================================================


class FinalClassification(StrEnum):
    """
    Classificação final da investigação.
    """

    FALSE_POSITIVE = "FALSE_POSITIVE"
    BENIGN_POSITIVE = "BENIGN_POSITIVE"
    SUSPICIOUS = "SUSPICIOUS"
    CONFIRMED_INCIDENT = "CONFIRMED_INCIDENT"
    INCONCLUSIVE = "INCONCLUSIVE"


# ============================================================
# DECISÃO FINAL
# ============================================================


class FinalDecision(StrEnum):
    """
    Decisão operacional final do caso.
    """

    CLOSED_N1 = "CLOSED_N1"
    ESCALATED_N2 = "ESCALATED_N2"
    WAITING_HUMAN = "WAITING_HUMAN"


# ============================================================
# RESULTADO DO QA
# ============================================================


class QAStatus(StrEnum):
    """
    Estado da revisão realizada pelo Reflection / QA Agent.
    """

    NOT_REVIEWED = "NOT_REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ============================================================
# TIPOS DE ALERTA
# ============================================================


class AlertType(StrEnum):
    """
    Catálogo inicial de alertas suportados pelo SOC N1.
    """

    AUTH_BRUTE_FORCE = "AUTH_BRUTE_FORCE"
    SUSPICIOUS_LOGIN = "SUSPICIOUS_LOGIN"
    CREDENTIAL_EXPOSURE = "CREDENTIAL_EXPOSURE"
    PHISHING = "PHISHING"
    MALWARE_DETECTION = "MALWARE_DETECTION"
    SUSPICIOUS_POWERSHELL = "SUSPICIOUS_POWERSHELL"
    MALICIOUS_IOC = "MALICIOUS_IOC"
    PRIVILEGED_ACCOUNT_ACTIVITY = "PRIVILEGED_ACCOUNT_ACTIVITY"
    LATERAL_MOVEMENT_SUSPECTED = "LATERAL_MOVEMENT_SUSPECTED"
    DATA_EXFILTRATION_SUSPECTED = "DATA_EXFILTRATION_SUSPECTED"

    UNSUPPORTED = "UNSUPPORTED"


# ============================================================
# TIPOS DE INDICADOR
# ============================================================


class IndicatorType(StrEnum):
    """
    Tipos de IOC que poderão circular entre os agentes.
    """

    IP = "IP"
    DOMAIN = "DOMAIN"
    URL = "URL"
    HASH = "HASH"
    EMAIL = "EMAIL"


# ============================================================
# TIPOS DE EVIDÊNCIA
# ============================================================


class EvidenceType(StrEnum):
    """
    Categorias principais de evidências coletadas.
    """

    ALERT = "ALERT"
    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"
    IDENTITY = "IDENTITY"
    ASSET = "ASSET"
    EMAIL = "EMAIL"
    KNOWLEDGE = "KNOWLEDGE"
    LOG = "LOG"
    TOOL_RESULT = "TOOL_RESULT"
    ANALYSIS = "ANALYSIS"


# ============================================================
# PERMISSÕES
# ============================================================


class PermissionType(StrEnum):
    """
    Tipos de permissões utilizadas pela arquitetura.
    """

    READ = "READ"
    WRITE = "WRITE"
    TOOL = "TOOL"
    DECISION = "DECISION"


# ============================================================
# AÇÕES
# ============================================================


class ActionType(StrEnum):
    """
    Tipo de ação recomendada ou executada no laboratório.
    """

    NONE = "NONE"
    RECOMMENDED_ACTION = "RECOMMENDED_ACTION"
    SIMULATED_ACTION = "SIMULATED_ACTION"