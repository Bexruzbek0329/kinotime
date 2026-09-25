import time
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from redis.asyncio import Redis

from config import settings
import structlog

log = structlog.get_logger()


class RateLimitMiddleware(BaseMiddleware):
    """
    Enforce a sliding-window rate limit per Telegram user.

    Uses Redis if available, falling back to an in-memory sliding window
    if Redis is not configured or unavailable.
    """

    def __init__(self, redis: Optional[Redis] = None) -> None:
        self.redis = redis
        self.limit: int = settings.rate_limit_requests
        self.window: int = settings.rate_limit_window
        self._memory_cache: dict[int, list[float]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if not user_id:
            return await handler(event, data)

        exceeded = False
        if self.redis is not None:
            try:
                key = f"rate_limit:{user_id}"
                count: int = await self.redis.incr(key)
                if count == 1:
                    await self.redis.expire(key, self.window)
                if count > self.limit:
                    exceeded = True
            except Exception as e:
                log.warning("redis_rate_limit_error", error=str(e))
        else:
            now = time.time()
            timestamps = self._memory_cache.get(user_id, [])
            # Filter timestamps inside window
            timestamps = [t for t in timestamps if now - t < self.window]
            if len(timestamps) >= self.limit:
                exceeded = True
            else:
                timestamps.append(now)
                self._memory_cache[user_id] = timestamps

        if exceeded:
            log.info("rate_limit_exceeded", user_id=user_id)
            if isinstance(event, Message):
                await event.answer("\u23f3 Juda tez! Biroz kuting.")
            elif isinstance(event, CallbackQuery):
                await event.answer("\u23f3 Juda tez! Biroz kuting.", show_alert=True)
            return

        return await handler(event, data)

