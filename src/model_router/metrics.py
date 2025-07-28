"""Model Router metrics."""

from ..common.metrics import record


def record_request() -> str:
    return record("model_router_request", 1.0)
