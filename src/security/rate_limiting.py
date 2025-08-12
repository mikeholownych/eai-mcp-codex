"""
API Rate Limiting with Redis Backend

Provides configurable rate limiting for API endpoints using Redis as the storage backend.
Supports different rate limiting strategies including sliding window and token bucket.
"""

import time
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException, status
from functools import wraps
from enum import Enum

from ..common.redis_client import RedisClient
from ..common.settings import Settings


class RateLimitStrategy(str, Enum):
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"


class RateLimitExceededError(Exception):
    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class RateLimiter:
    def __init__(self, redis_client: RedisClient, settings: Settings):
        self.redis = redis_client
        self.settings = settings
        self.default_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000,
        }

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit

        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        current_time = int(time.time())

        if strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(
                identifier, limit, window_seconds, current_time
            )
        elif strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(
                identifier, limit, window_seconds, current_time
            )
        elif strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window_check(
                identifier, limit, window_seconds, current_time
            )
        else:
            raise ValueError(f"Unsupported rate limit strategy: {strategy}")

    async def _sliding_window_check(
        self, identifier: str, limit: int, window_seconds: int, current_time: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window rate limiting using Redis sorted sets"""
        key = f"rate_limit:sliding:{identifier}"
        window_start = current_time - window_seconds

        pipe = self.redis.client.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiry
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_count = results[1]

        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1)

        info = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": current_time + window_seconds,
            "window_seconds": window_seconds,
            "strategy": "sliding_window",
        }

        return allowed, info

    async def _token_bucket_check(
        self, identifier: str, limit: int, refill_seconds: int, current_time: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket rate limiting"""
        key = f"rate_limit:bucket:{identifier}"

        # Get current bucket state
        bucket_data = await self.redis.client.hgetall(key)

        if bucket_data:
            last_refill = float(bucket_data.get("last_refill", current_time))
            tokens = float(bucket_data.get("tokens", limit))
        else:
            last_refill = current_time
            tokens = limit

        # Calculate tokens to add based on time elapsed
        time_elapsed = current_time - last_refill
        tokens_to_add = (time_elapsed / refill_seconds) * limit
        tokens = min(limit, tokens + tokens_to_add)

        allowed = tokens >= 1

        if allowed:
            tokens -= 1

        # Update bucket state
        await self.redis.client.hset(
            key, mapping={"tokens": str(tokens), "last_refill": str(current_time)}
        )
        await self.redis.client.expire(key, refill_seconds * 2)

        info = {
            "limit": limit,
            "remaining": int(tokens),
            "reset_time": current_time + refill_seconds,
            "window_seconds": refill_seconds,
            "strategy": "token_bucket",
        }

        return allowed, info

    async def _fixed_window_check(
        self, identifier: str, limit: int, window_seconds: int, current_time: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fixed window rate limiting"""
        window_start = (current_time // window_seconds) * window_seconds
        key = f"rate_limit:fixed:{identifier}:{window_start}"

        current_count = await self.redis.client.incr(key)

        if current_count == 1:
            await self.redis.client.expire(key, window_seconds)

        allowed = current_count <= limit
        remaining = max(0, limit - current_count)

        info = {
            "limit": limit,
            "remaining": remaining,
            "reset_time": window_start + window_seconds,
            "window_seconds": window_seconds,
            "strategy": "fixed_window",
        }

        return allowed, info

    def get_client_identifier(self, request: Request) -> str:
        """Generate client identifier for rate limiting"""
        # Try to get authenticated user ID first
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    async def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for identifier"""
        info = {}

        # Check different time windows
        for window_name, seconds in [("minute", 60), ("hour", 3600), ("day", 86400)]:
            limit = self.default_limits.get(f"requests_per_{window_name}", 100)
            allowed, window_info = await self.check_rate_limit(
                identifier, limit, seconds, RateLimitStrategy.SLIDING_WINDOW
            )
            info[window_name] = window_info

        return info


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.endpoint_limits = {}

    def configure_endpoint(
        self,
        path: str,
        method: str,
        limit: int,
        window_seconds: int,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    ):
        """Configure rate limits for specific endpoint"""
        key = f"{method}:{path}"
        self.endpoint_limits[key] = {
            "limit": limit,
            "window_seconds": window_seconds,
            "strategy": strategy,
        }

    async def __call__(self, request: Request, call_next):
        """Process request through rate limiter"""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        identifier = self.rate_limiter.get_client_identifier(request)

        # Check endpoint-specific limits
        endpoint_key = f"{request.method}:{request.url.path}"
        if endpoint_key in self.endpoint_limits:
            config = self.endpoint_limits[endpoint_key]
            allowed, info = await self.rate_limiter.check_rate_limit(
                f"{identifier}:{endpoint_key}",
                config["limit"],
                config["window_seconds"],
                config["strategy"],
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(info["limit"]),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset_time"]),
                        "Retry-After": str(info["window_seconds"]),
                    },
                )

        # Check global limits
        for window_name, seconds in [("minute", 60), ("hour", 3600)]:
            limit_key = f"requests_per_{window_name}"
            if limit_key in self.rate_limiter.default_limits:
                limit = self.rate_limiter.default_limits[limit_key]
                allowed, info = await self.rate_limiter.check_rate_limit(
                    f"{identifier}:global:{window_name}", limit, seconds
                )

                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Global rate limit exceeded: {limit} requests per {window_name}",
                        headers={
                            "X-RateLimit-Limit": str(info["limit"]),
                            "X-RateLimit-Remaining": str(info["remaining"]),
                            "X-RateLimit-Reset": str(info["reset_time"]),
                            "Retry-After": str(info["window_seconds"]),
                        },
                    )

        response = await call_next(request)
        return response


def rate_limit(
    limit: int,
    window_seconds: int,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    key_func: Optional[callable] = None,
):
    """Decorator for rate limiting specific endpoints

    Attempts to locate a RateLimiter instance from the FastAPI app state. If none is
    available, the wrapped function executes without rate limiting (safe fallback).
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Try to obtain a RateLimiter instance from the app state
            rate_limiter = None
            try:
                app_state = getattr(request, "app", None)
                state = getattr(app_state, "state", None) if app_state else None
                if state is not None:
                    if hasattr(state, "rate_limiter") and state.rate_limiter is not None:
                        rate_limiter = state.rate_limiter
                    elif hasattr(state, "security_stack") and getattr(
                        state.security_stack, "rate_limiter", None
                    ) is not None:
                        rate_limiter = state.security_stack.rate_limiter
            except Exception:
                rate_limiter = None

            # If no rate limiter, proceed without enforcement
            if rate_limiter is None:
                return await func(request, *args, **kwargs)

            # Build client identifier
            identifier = (
                key_func(request)
                if key_func is not None
                else rate_limiter.get_client_identifier(request)
            )

            # Include endpoint-specific suffix for better isolation
            endpoint_key = f"{request.method}:{request.url.path}:{func.__name__}"

            allowed, info = await rate_limiter.check_rate_limit(
                f"{identifier}:{endpoint_key}", limit, window_seconds, strategy
            )

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(info.get("limit", limit)),
                        "X-RateLimit-Remaining": str(info.get("remaining", 0)),
                        "X-RateLimit-Reset": str(info.get("reset_time", 0)),
                        "Retry-After": str(info.get("window_seconds", window_seconds)),
                    },
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


async def setup_rate_limiter(
    redis_client: RedisClient, settings: Settings
) -> RateLimiter:
    """Factory function to create and configure rate limiter"""
    rate_limiter = RateLimiter(redis_client, settings)

    # Configure default limits from settings
    if hasattr(settings, "RATE_LIMITS"):
        rate_limiter.default_limits.update(settings.RATE_LIMITS)

    return rate_limiter
