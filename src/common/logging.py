"""Logging configuration utilities."""

import logging
import os


_def_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")


_def_handler = logging.StreamHandler()
_def_handler.setFormatter(_def_formatter)


_def_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, _def_level), handlers=[_def_handler])


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""
    return logging.getLogger(name)
