"""Redis client utilities."""

import os
from redis.asyncio import Redis

from .logging import get_logger

logger = get_logger("redis")


def get_redis(url: str) -> Redis:
    """Create a Redis client from the given URL."""
    return Redis.from_url(url, decode_responses=True)


async def get_redis_connection(url: str = None) -> Redis:
    """Get Redis connection with default configuration."""
    if url is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")

    try:
        client = Redis.from_url(url, decode_responses=True)
        # Test connection
        await client.ping()
        logger.info(f"Connected to Redis at {url}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
