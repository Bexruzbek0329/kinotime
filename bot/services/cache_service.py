"""Redis caching layer with JSON serialisation."""
import json
from typing import Any, Optional

from redis.asyncio import Redis
import structlog

log = structlog.get_logger()


class CacheService:
    """
    Thin wrapper around :class:`redis.asyncio.Redis` that JSON-serialises
    values and swallows connection errors so cache failures never break
    the main request flow.
    """

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    # ------------------------------------------------------------------
    # Core primitives
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Optional[Any]:
        """Return the cached value for *key*, or *None* on miss / error."""
        try:
            raw = await self.redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as exc:
            log.warning("cache_get_error", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store *value* under *key* with an expiry of *ttl* seconds."""
        try:
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as exc:
            log.warning("cache_set_error", key=key, error=str(exc))

    async def delete(self, key: str) -> None:
        """Remove *key* from the cache."""
        try:
            await self.redis.delete(key)
        except Exception as exc:
            log.warning("cache_delete_error", key=key, error=str(exc))

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    async def invalidate_movie(self, movie_id: int) -> None:
        """
        Invalidate all cache entries related to *movie_id*.

        Removes:
        - The specific movie card key.
        - All paginated latest-movies keys (pattern ``movies:latest:*``).
        - All paginated top-movies keys (pattern ``movies:top:*``).
        """
        exact_keys = [f"movie:card:{movie_id}"]
        pattern_keys = ["movies:latest:*", "movies:top:*"]

        for key in exact_keys:
            await self.delete(key)

        for pattern in pattern_keys:
            try:
                async for k in self.redis.scan_iter(pattern):
                    await self.redis.delete(k)
            except Exception as exc:
                log.warning("cache_pattern_delete_error", pattern=pattern, error=str(exc))
