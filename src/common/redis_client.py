"""Redis client utilities."""

import os
from redis.asyncio import Redis
from typing import Optional

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


class RedisClient:
    """Thin wrapper around redis.asyncio.Redis to provide a stable interface.

    Many modules expect an object with a `.client` attribute that exposes the
    underlying Redis API. This wrapper standardizes that and offers simple
    helpers for construction and teardown.
    """

    def __init__(self, client: Redis):
        self.client: Redis = client

    @classmethod
    async def create(cls, url: Optional[str] = None) -> "RedisClient":
        client = await get_redis_connection(url)
        return cls(client)

    async def ping(self) -> bool:
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        # Gracefully close depending on redis version
        close = getattr(self.client, "aclose", None) or getattr(self.client, "close", None)
        if close:
            res = close()
            if hasattr(res, "__await__"):
                await res
