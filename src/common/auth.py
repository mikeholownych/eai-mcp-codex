"""Authentication utilities."""


def authenticate(token: str) -> bool:
    """Simple token authentication."""
    return bool(token)
