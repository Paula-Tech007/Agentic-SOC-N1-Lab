"""
Camada Identity / IAM
do Agentic SOC N1 Lab.

Fase 4.3 — Identity / IAM read-only.

Este pacote fornece:

- configuração segura da integração IAM;
- cliente HTTP estritamente read-only;
- handlers oficiais para ToolRuntime.

Ferramentas implementadas:

- iam.get_user;
- iam.get_account_status;
- iam.get_mfa_status;
- iam.get_group_membership.

Nenhuma operação de alteração de identidade,
senha, conta ou grupo é disponibilizada.
"""

from tools.identity.identity_client import (
    IdentityClient,
    IdentityClientError,
    IdentityConnectionError,
    IdentityHTTPError,
    IdentityResponseError,
    IdentityTimeoutError,
)
from tools.identity.identity_config import (
    DEFAULT_IAM_PROVIDER,
    DEFAULT_IAM_TIMEOUT_SECONDS,
    MAX_IAM_TIMEOUT_SECONDS,
    MIN_IAM_TIMEOUT_SECONDS,
    IdentityConfig,
)
from tools.identity.identity_handlers import (
    IdentityToolHandlers,
)


__all__ = [
    "DEFAULT_IAM_PROVIDER",
    "DEFAULT_IAM_TIMEOUT_SECONDS",
    "IdentityClient",
    "IdentityClientError",
    "IdentityConfig",
    "IdentityConnectionError",
    "IdentityHTTPError",
    "IdentityResponseError",
    "IdentityTimeoutError",
    "IdentityToolHandlers",
    "MAX_IAM_TIMEOUT_SECONDS",
    "MIN_IAM_TIMEOUT_SECONDS",
]