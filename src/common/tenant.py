"""Utilities for managing the current tenant context."""

from __future__ import annotations

import contextvars
from contextlib import contextmanager

_current_tenant: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_tenant", default="public"
)


def set_current_tenant(tenant_id: str) -> None:
    """Set the active tenant id for the current context."""

    _current_tenant.set(tenant_id)


def get_current_tenant() -> str:
    """Return the active tenant id for the current context."""

    return _current_tenant.get()


@contextmanager
def tenant_context(tenant_id: str):
    """Context manager to temporarily switch the active tenant."""

    token = _current_tenant.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant.reset(token)
