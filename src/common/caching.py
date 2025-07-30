"""Caching utilities with multiple backend support."""

import json
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass
from functools import wraps
from abc import ABC, abstractmethod

from .logging import get_logger
from .metrics import get_metrics_collector

logger = get_logger("caching")


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """Get all cache keys."""
        pass

    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from memory cache."""
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                self._misses += 1
                return None

            # Check expiration
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Update access stats
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self._hits += 1

            return entry

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in memory cache."""
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None

            # Calculate approximate size
            size_bytes = len(str(value).encode("utf-8"))

            entry = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes,
            )

            self._cache[key] = entry
            return True

    def delete(self, key: str) -> bool:
        """Delete a value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            return True

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            return list(self._cache.keys())

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            total_size = sum(entry.size_bytes for entry in self._cache.values())

            return {
                "backend": "memory",
                "entries": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "total_size_bytes": total_size,
                "default_ttl": self.default_ttl,
            }

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at,
        )

        del self._cache[lru_key]
        self._evictions += 1


class RedisCache(CacheBackend):
    """Redis cache backend (requires redis-py)."""

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "mcp:"):
        self.prefix = prefix
        try:
            import redis

            self.redis = redis.from_url(redis_url)
            self.redis.ping()  # Test connection
            logger.info(f"Connected to Redis at {redis_url}")
        except ImportError:
            raise ImportError("redis package required for RedisCache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get a value from Redis cache."""
        try:
            redis_key = self._make_key(key)
            data = self.redis.get(redis_key)
            if not data:
                return None

            entry_data = json.loads(data)

            # Reconstruct CacheEntry
            entry = CacheEntry(
                value=entry_data["value"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                expires_at=(
                    datetime.fromisoformat(entry_data["expires_at"])
                    if entry_data["expires_at"]
                    else None
                ),
                access_count=entry_data.get("access_count", 0),
                last_accessed=(
                    datetime.fromisoformat(entry_data["last_accessed"])
                    if entry_data.get("last_accessed")
                    else None
                ),
                size_bytes=entry_data.get("size_bytes", 0),
            )

            # Update access stats
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()

            # Write back updated stats
            self._store_entry(redis_key, entry)

            return entry

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis cache."""
        try:
            redis_key = self._make_key(key)

            entry = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl) if ttl else None,
                size_bytes=len(str(value).encode("utf-8")),
            )

            self._store_entry(redis_key, entry, ttl)
            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def _store_entry(
        self, redis_key: str, entry: CacheEntry, ttl: Optional[int] = None
    ):
        """Store entry in Redis."""
        entry_data = {
            "value": entry.value,
            "created_at": entry.created_at.isoformat(),
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
            "access_count": entry.access_count,
            "last_accessed": (
                entry.last_accessed.isoformat() if entry.last_accessed else None
            ),
            "size_bytes": entry.size_bytes,
        }

        data = json.dumps(entry_data)
        if ttl:
            self.redis.setex(redis_key, ttl, data)
        else:
            self.redis.set(redis_key, data)

    def delete(self, key: str) -> bool:
        """Delete a value from Redis cache."""
        try:
            redis_key = self._make_key(key)
            return bool(self.redis.delete(redis_key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries with prefix."""
        try:
            keys = self.redis.keys(f"{self.prefix}*")
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def keys(self) -> List[str]:
        """Get all cache keys."""
        try:
            redis_keys = self.redis.keys(f"{self.prefix}*")
            return [key.decode().replace(self.prefix, "", 1) for key in redis_keys]
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.redis.info()
            keys_count = len(self.keys())

            return {
                "backend": "redis",
                "entries": keys_count,
                "redis_memory": info.get("used_memory_human", "unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"backend": "redis", "error": str(e)}


class CacheManager:
    """High-level cache manager with multiple backends and metrics."""

    def __init__(self, backend: CacheBackend, service_name: str = "default"):
        self.backend = backend
        self.service_name = service_name
        self.metrics = get_metrics_collector(service_name)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from cache."""
        try:
            entry = self.backend.get(key)
            if entry:
                self.metrics.record_cache_operation("get", "hit")
                return entry.value
            else:
                self.metrics.record_cache_operation("get", "miss")
                return default
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.metrics.record_cache_operation("get", "error")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache."""
        try:
            success = self.backend.set(key, value, ttl)
            self.metrics.record_cache_operation(
                "set", "success" if success else "failure"
            )
            return success
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.metrics.record_cache_operation("set", "error")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            success = self.backend.delete(key)
            self.metrics.record_cache_operation(
                "delete", "success" if success else "failure"
            )
            return success
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self.metrics.record_cache_operation("delete", "error")
            return False

    def get_or_set(
        self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or compute and store it."""
        value = self.get(key)
        if value is not None:
            return value

        # Compute value
        try:
            computed_value = factory()
            self.set(key, computed_value, ttl)
            return computed_value
        except Exception as e:
            logger.error(f"Factory function failed: {e}")
            raise

    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            success = self.backend.clear()
            self.metrics.record_cache_operation(
                "clear", "success" if success else "failure"
            )
            return success
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.metrics.record_cache_operation("clear", "error")
            return False

    def stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        backend_stats = self.backend.stats()

        return {
            **backend_stats,
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        import fnmatch

        deleted_count = 0
        try:
            keys = self.backend.keys()
            matching_keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]

            for key in matching_keys:
                if self.delete(key):
                    deleted_count += 1

            logger.info(f"Invalidated {deleted_count} keys matching pattern: {pattern}")

        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")

        return deleted_count


# Global cache managers
_cache_managers: Dict[str, CacheManager] = {}


def get_cache_manager(
    service_name: str, backend_type: str = "memory", **kwargs
) -> CacheManager:
    """Get or create a cache manager for a service."""
    cache_key = f"{service_name}_{backend_type}"

    if cache_key not in _cache_managers:
        if backend_type == "memory":
            backend = MemoryCache(**kwargs)
        elif backend_type == "redis":
            backend = RedisCache(**kwargs)
        else:
            raise ValueError(f"Unsupported cache backend: {backend_type}")

        _cache_managers[cache_key] = CacheManager(backend, service_name)

    return _cache_managers[cache_key]


def cached(ttl: int = 3600, key_prefix: str = "", service_name: str = "default"):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        cache_manager = get_cache_manager(service_name)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]

            # Add args to key (simplified)
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(tuple(sorted(kwargs.items())))))

            cache_key = ":".join(filter(None, key_parts))

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        # Add cache management methods to decorated function
        wrapper.cache_clear = lambda: cache_manager.clear()
        wrapper.cache_stats = lambda: cache_manager.stats()

        return wrapper

    return decorator


class DistributedLock:
    """Distributed lock using cache backend."""

    def __init__(self, cache_manager: CacheManager, key: str, timeout: int = 30):
        self.cache_manager = cache_manager
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.acquired = False

    def acquire(self) -> bool:
        """Acquire the lock."""
        lock_data = {
            "acquired_at": datetime.utcnow().isoformat(),
            "timeout": self.timeout,
        }

        # Try to set lock (atomic operation in most backends)
        existing = self.cache_manager.get(self.key)
        if existing is None:
            success = self.cache_manager.set(self.key, lock_data, self.timeout)
            if success:
                self.acquired = True
                return True

        return False

    def release(self) -> bool:
        """Release the lock."""
        if self.acquired:
            success = self.cache_manager.delete(self.key)
            self.acquired = False
            return success
        return False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Utility functions
def with_cache(service_name: str, ttl: int = 3600):
    """Context manager for cache operations."""
    cache_manager = get_cache_manager(service_name)

    class CacheContext:
        def __init__(self, manager):
            self.manager = manager

        def get(self, key, default=None):
            return self.manager.get(key, default)

        def set(self, key, value, ttl=ttl):
            return self.manager.set(key, value, ttl)

        def delete(self, key):
            return self.manager.delete(key)

    return CacheContext(cache_manager)


def cache_warming_decorator(cache_keys: List[str], ttl: int = 3600):
    """Decorator to warm cache with multiple keys."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Warm cache with result for all specified keys
            cache_manager = get_cache_manager("default")
            for key in cache_keys:
                cache_manager.set(key, result, ttl)

            return result

        return wrapper

    return decorator
