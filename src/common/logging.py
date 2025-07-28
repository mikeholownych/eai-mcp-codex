"""Logging helpers."""

import logging


logging.basicConfig(level=logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger."""
    return logging.getLogger(name)
