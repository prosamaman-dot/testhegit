from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from src.config.settings import settings


def create_logger(name: str = "scalpbot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if settings.log_to_file:
        file_handler = RotatingFileHandler(settings.log_file_path, maxBytes=50_000_000, backupCount=1)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


