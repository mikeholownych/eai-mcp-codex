"""Prometheus metrics utilities."""

from prometheus_client import Counter

REQUEST_COUNTER = Counter(
    "mcp_requests_total",
    "Total service requests",
    ["service"],
)


def record_request(service: str) -> None:
    """Increment the request counter for the given service."""
    REQUEST_COUNTER.labels(service=service).inc()
