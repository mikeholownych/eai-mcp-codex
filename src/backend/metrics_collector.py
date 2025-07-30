"""Backend level metrics helpers.

This module wraps :class:`src.common.metrics.MetricsCollector` to ensure
collectors are reused per service to avoid duplicate metric registration.
"""

from __future__ import annotations

from typing import Dict

from src.common.metrics import MetricsCollector

_collectors: Dict[str, MetricsCollector] = {}


def get_backend_collector(service_name: str) -> MetricsCollector:
    """Return a shared MetricsCollector for the given service."""
    if service_name not in _collectors:
        _collectors[service_name] = MetricsCollector(service_name)
    return _collectors[service_name]
