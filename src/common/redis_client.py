"""Redis client utilities."""

from redis import Redis


def get_redis(url: str) -> Redis:
    """Create a Redis client from the given URL."""
    return Redis.from_url(url, decode_responses=True)
