import logging
import sys


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("verifybot")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # evita duplicar handlers

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger
