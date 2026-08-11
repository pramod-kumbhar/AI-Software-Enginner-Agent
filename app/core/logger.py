from app.core.logging import logger, setup_logger

def get_logger(name: str = "swe_security"):
    return setup_logger(name)

__all__ = ["logger", "get_logger", "setup_logger"]
