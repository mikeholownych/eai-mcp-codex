"""Health check utilities."""

from typing import Dict


def health() -> Dict[str, str]:
    """Return the standard health payload."""
    return {"status": "ok"}
