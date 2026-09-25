"""Create/update the DB user record on every update; block banned users."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repo import UserRepository
import structlog

log = structlog.get_logger()


class UserMiddleware(BaseMiddleware):
    """
    Upsert the Telegram user into the database on every message / callback.

    Side effects:
    - ``data["db_user"]``    — the ORM user object (always set when Telegram
                               provides a from_user).
    - ``data["is_new_user"]``— True when the record was just created.
    - Blocked users receive an alert and the handler chain is terminated early.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession | None = data.get("session")
        if not session:
            return await handler(event, data)

        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if not tg_user:
            return await handler(event, data)

        repo = UserRepository(session)
        db_user, is_new = await repo.create_or_update(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name or "User",
            username=tg_user.username,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
        )

        if db_user.is_blocked:
            log.info("blocked_user_attempt", user_id=tg_user.id)
            if isinstance(event, Message):
                await event.answer("\U0001f6ab Siz bloklangansiz.")
            elif isinstance(event, CallbackQuery):
                await event.answer("\U0001f6ab Siz bloklangansiz.", show_alert=True)
            return  # Short-circuit: do not call downstream handlers

        data["db_user"] = db_user
        data["is_new_user"] = is_new

        if is_new:
            log.info("new_user_registered", user_id=tg_user.id, username=tg_user.username)

        return await handler(event, data)
