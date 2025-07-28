"""Redis client utilities."""


def get_redis(url: str) -> str:
    """Return redis connection info (mock)."""
    return f"redis:{url}"
