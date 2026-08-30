"""Rate limiter middleware using Redis or in-memory store.

Implements a simple sliding window rate limiter per client IP address.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Store abstraction
# ------------------------------------------------------------------


class RateLimitStore(ABC):
    """Abstract interface for rate limiter storage backends."""

    @abstractmethod
    async def add_request(self, key: str, now: float, window: int) -> int:
        """Record a request and return the current count in the window."""
        ...

    @abstractmethod
    async def get_count(self, key: str, now: float, window: int) -> int:
        """Return the number of requests in the current window."""
        ...


class RedisStore(RateLimitStore):
    """Redis-backed rate limiter store."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client

    async def add_request(self, key: str, now: float, window: int) -> int:
        window_start = now - window
        pipe = self.redis.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window + 1)
        results = await pipe.execute()
        return results[2]

    async def get_count(self, key: str, now: float, window: int) -> int:
        window_start = now - window
        pipe = self.redis.pipeline(transaction=True)
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        return results[1]


class InMemoryStore(RateLimitStore):
    """In-memory rate limiter store (fallback when Redis is unavailable)."""

    def __init__(self) -> None:
        self._data: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def add_request(self, key: str, now: float, window: int) -> int:
        async with self._lock:
            if key not in self._data:
                self._data[key] = []
            # Clean old entries
            window_start = now - window
            self._data[key] = [t for t in self._data[key] if t > window_start]
            self._data[key].append(now)
            return len(self._data[key])

    async def get_count(self, key: str, now: float, window: int) -> int:
        async with self._lock:
            if key not in self._data:
                return 0
            window_start = now - window
            count = sum(1 for t in self._data[key] if t > window_start)
            return count


# ------------------------------------------------------------------
# Rate limiter
# ------------------------------------------------------------------


class RateLimiter:
    """Rate limiter with pluggable storage backend."""

    def __init__(
        self,
        store: RateLimitStore | None = None,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """
        Args:
            store: Storage backend (Redis or InMemory). Falls back to InMemory if None.
            max_requests: Maximum requests allowed per window.
            window_seconds: Window duration in seconds.
        """
        self._store: RateLimitStore = store or InMemoryStore()
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(self, request: Request) -> None:
        """Check rate limit for the request.

        Raises:
            HTTPException: 429 if rate limit exceeded.
        """
        client_ip = self._get_client_ip(request)
        if client_ip == "unknown":
            return

        key = f"rate_limit:{client_ip}"
        now = time.time()

        try:
            current_count = await self._store.add_request(key, now, self.window_seconds)

            if current_count > self.max_requests:
                logger.warning("Rate limit exceeded for IP %s", client_ip)
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(self.window_seconds)},
                )

            request.state.rate_limit_remaining = max(0, self.max_requests - current_count)
            request.state.rate_limit_limit = self.max_requests
            request.state.rate_limit_window = self.window_seconds

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Rate limiter error: %s", exc)
            return

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request headers."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
