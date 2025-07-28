"""Consul service discovery utilities."""


def register_service(name: str, url: str) -> str:
    """Return registration result (mock)."""
    return f"registered:{name}@{url}"
