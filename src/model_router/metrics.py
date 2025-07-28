"""Model Router metrics helpers."""

from src.common.metrics import record_request


def record() -> None:
    """Record a Model Router request."""
    record_request("model-router")
