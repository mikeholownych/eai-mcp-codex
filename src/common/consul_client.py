"""Consul service discovery utilities."""

import requests


def register_service(
    name: str, url: str, consul_url: str = "http://localhost:8500"
) -> None:
    """Register the service with Consul."""
    payload = {
        "Name": name,
        "Address": url,
        "Check": {"HTTP": f"{url}/health", "Interval": "10s"},
    }
    response = requests.put(
        f"{consul_url}/v1/agent/service/register", json=payload, timeout=5
    )
    response.raise_for_status()
