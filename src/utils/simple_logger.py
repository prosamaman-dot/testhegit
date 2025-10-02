"""
Simple logger without rotation to avoid permission errors
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime

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

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Simple file handler without rotation
    if settings.log_to_file:
        try:
            file_handler = logging.FileHandler(settings.log_file_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, just use console
            logger.warning("File logging disabled: %s", e)

    logger.propagate = False
    return logger
