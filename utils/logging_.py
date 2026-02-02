import logging

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("verifybot")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Evita duplicar logs se o módulo for recarregado.
    logger.propagate = False
    return logger
