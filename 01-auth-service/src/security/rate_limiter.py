"""Rate limiting utilities for HyperScale Marketplace.

Implements IP-based, user-based, and endpoint-specific rate limiting
using a sliding-window algorithm backed by an in-memory store or Redis.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from fastapi import Request, HTTPException


# ------------------------------------------------------------------
# Protocol for pluggable storage back-ends
# ------------------------------------------------------------------

class RateLimitStore(Protocol):
    """Abstract store for rate-limit counters."""

    async def increment(self, key: str, window: int) -> int:
        """Increment the counter for *key* within *window* seconds.

        Returns the current count after incrementing.
        """

    async def get(self, key: str) -> Optional[int]:
        """Return the current counter value or ``None``."""

    async def delete(self, key: str) -> None:
        """Delete a counter."""


# ------------------------------------------------------------------
# In-memory store
# ------------------------------------------------------------------

@dataclass
class _InMemoryEntry:
    count: int = 0
    window_start: float = field(default_factory=time.time)


class InMemoryStore:
    """Sliding-window rate limiter backed by an in-process dict."""

    def __init__(self) -> None:
        self._data: dict[str, _InMemoryEntry] = {}
        self._lock: Any = None  # Not needed for single-threaded; keep for extension

    async def increment(self, key: str, window: int) -> int:
        now = time.time()
        entry = self._data.get(key)
        if entry is None or (now - entry.window_start) >= window:
            self._data[key] = _InMemoryEntry(count=1, window_start=now)
            return 1
        entry.count += 1
        return entry.count

    async def get(self, key: str) -> Optional[int]:
        entry = self._data.get(key)
        return entry.count if entry else None

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)


# ------------------------------------------------------------------
# Redis-backed store
# ------------------------------------------------------------------

class RedisStore:
    """Sliding-window rate limiter backed by Redis sorted sets."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    async def increment(self, key: str, window: int) -> int:
        now = time.time()
        window_key = f"rl:{key}:{int(now // window)}"
        pipe = self.redis.pipeline(transaction=True)
        pipe.zremrangebyscore(window_key, "-inf", now - window)
        pipe.zadd(window_key, {f"{now}:{uuid.uuid4().hex}": now})
        pipe.zcard(window_key)
        pipe.expire(window_key, window + 1)
        results = await pipe.execute()
        return results[2]

    async def get(self, key: str) -> Optional[int]:
        now = time.time()
        pipe = self.redis.pipeline(transaction=True)
        pipe.zcard(f"rl:{key}:{int(now // 60)}")
        results = await pipe.execute()
        return results[0]

    async def delete(self, key: str) -> None:
        await self.redis.delete(f"rl:{key}")


# ------------------------------------------------------------------
# Rate limiter
# ------------------------------------------------------------------

@dataclass
class RateLimitConfig:
    """Configuration for a single rate-limit rule."""
    key_prefix: str
    max_requests: int
    window_seconds: int


class RateLimiter:
    """Sliding-window rate limiter supporting IP, user, and endpoint rules.

    Example
    -------
    >>> limiter = RateLimiter(store=InMemoryStore())
    >>> limiter.add_rule("ip", "192.168.1.1", max_requests=10, window_seconds=60)
    >>> limiter.add_rule("user", "user-42", max_requests=100, window_seconds=60)
    >>> limiter.add_rule("endpoint", "POST:/api/login", max_requests=5, window_seconds=60)
    >>> await limiter.check(request)
    """

    def __init__(self, store: Optional[RateLimitStore] = None) -> None:
        self._store: RateLimitStore = store or InMemoryStore()
        self._rules: list[RateLimitConfig] = []

    def add_rule(
        self,
        key_prefix: str,
        key_value: str,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """Add a rate-limit rule."""
        self._rules.append(RateLimitConfig(
            key_prefix=key_prefix,
            key_value=key_value,
            max_requests=max_requests,
            window_seconds=window_seconds,
        ))

    async def check(self, request: Request) -> dict[str, int]:
        """Check all rules against *request*.

        Raises ``HTTPException(429)`` if **any** rule is exceeded.

        Returns a dict with ``limit``, ``remaining``, and ``reset`` headers.
        """
        now = time.time()
        headers: dict[str, int] = {}
        min_remaining: int = float("inf")
        max_reset: float = 0.0

        for rule in self._rules:
            full_key = f"{rule.key_prefix}:{rule.key_value}"
            count = await self._store.increment(full_key, rule.window_seconds)

            remaining = max(0, rule.max_requests - count)
            reset_at = int(now + rule.window_seconds)

            if count > rule.max_requests:
                headers["Retry-After"] = str(rule.window_seconds)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {rule.key_prefix}: {rule.key_value}",
                    headers=headers,
                )

            if remaining < min_remaining:
                min_remaining = remaining
            if reset_at > max_reset:
                max_reset = reset_at

        headers["X-RateLimit-Limit"] = rule.max_requests  # last rule wins for header
        headers["X-RateLimit-Remaining"] = min_remaining
        headers["X-RateLimit-Reset"] = int(max_reset)
        return headers

    async def reset(self, key_prefix: str, key_value: str) -> None:
        """Reset the counter for a specific rule."""
        full_key = f"{key_prefix}:{key_value}"
        await self._store.delete(full_key)


# ------------------------------------------------------------------
# Convenience: per-IP rate limiter
# ------------------------------------------------------------------

async def get_client_ip(request: Request) -> str:
    """Extract the real client IP from the request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"
