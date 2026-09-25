"""Inject an async SQLAlchemy session into every handler's data dict."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.engine import AsyncSessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """
    Open an :class:`~sqlalchemy.ext.asyncio.AsyncSession` per update,
    commit on success, and roll back on any unhandled exception.

    The session is stored in ``data["session"]`` so downstream middlewares
    and handlers can access it via dependency injection.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
