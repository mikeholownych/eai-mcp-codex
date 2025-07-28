"""Database utilities."""


def get_connection(dsn: str) -> str:
    """Return a connection string (mock)."""
    return f"connected:{dsn}"
