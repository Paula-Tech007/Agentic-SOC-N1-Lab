"""
Sistema central de logs do Agentic SOC N1 Lab.

Todos os componentes do projeto utilizarão este módulo
para registrar eventos importantes da execução.
"""

import logging
from pathlib import Path

from core.config import LOG_DIRECTORY, LOG_LEVEL


PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_PATH = PROJECT_ROOT / LOG_DIRECTORY

LOG_FILE = LOG_PATH / "agentic_soc.log"


def setup_logging() -> logging.Logger:
    """
    Configura o sistema central de logs.

    O log será enviado para:

    1. Terminal
    2. Arquivo logs/agentic_soc.log
    """

    LOG_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("agentic_soc")

    level = getattr(
        logging,
        LOG_LEVEL.upper(),
        logging.INFO,
    )

    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


logger = setup_logging()