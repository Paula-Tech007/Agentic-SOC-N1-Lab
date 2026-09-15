"""
Integração Email / Phishing do Agentic SOC N1 Lab.

Fase 4.5 — Email / Phishing Metadata Read-Only.

Exports públicos:

- EmailConfig;
- EmailClient;
- EmailToolHandlers;
- erros específicos do cliente;
- constantes de configuração.

A integração é estritamente defensiva e somente leitura.
"""

from tools.email.email_client import (
    EmailClient,
    EmailClientError,
    EmailConnectionError,
    EmailHTTPError,
    EmailResponseError,
    EmailTimeoutError,
)
from tools.email.email_config import (
    DEFAULT_EMAIL_PROVIDER,
    DEFAULT_EMAIL_TIMEOUT_SECONDS,
    MAX_EMAIL_TIMEOUT_SECONDS,
    MIN_EMAIL_TIMEOUT_SECONDS,
    OFFICIAL_EMAIL_OPERATIONS,
    EmailConfig,
)
from tools.email.email_handlers import (
    EmailToolHandlers,
)


__all__ = (
    "EmailClient",
    "EmailClientError",
    "EmailConfig",
    "EmailConnectionError",
    "EmailHTTPError",
    "EmailResponseError",
    "EmailTimeoutError",
    "EmailToolHandlers",
    "DEFAULT_EMAIL_PROVIDER",
    "DEFAULT_EMAIL_TIMEOUT_SECONDS",
    "MAX_EMAIL_TIMEOUT_SECONDS",
    "MIN_EMAIL_TIMEOUT_SECONDS",
    "OFFICIAL_EMAIL_OPERATIONS",
)