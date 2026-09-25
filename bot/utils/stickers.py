"""Sticker-send helper backed by DB settings."""
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from database.repositories.setting_repo import SettingRepository
import structlog

log = structlog.get_logger()

# Maps a logical sticker type to its settings key
STICKER_KEY_MAP: dict[str, str] = {
    "start": "start_sticker_file_id",
    "not_found": "not_found_sticker_file_id",
    "error": "error_sticker_file_id",
    "movie": "movie_sticker_file_id",
}


async def send_sticker(
    bot: Bot,
    chat_id: int,
    sticker_type: str,
    session: AsyncSession,
) -> None:
    """
    Send a sticker to *chat_id* if stickers are enabled and a file ID is set.

    The function is intentionally silent on failure — a missing sticker should
    never interrupt the main handler flow.

    Args:
        bot:          The :class:`~aiogram.Bot` instance.
        chat_id:      Telegram chat ID to send to.
        sticker_type: Logical type key, one of ``"start"``, ``"not_found"``,
                      ``"error"``, ``"movie"``.
        session:      Active async SQLAlchemy session.
    """
    try:
        setting_key = STICKER_KEY_MAP.get(sticker_type, "")
        if not setting_key:
            return

        repo = SettingRepository(session)
        settings_dict = await repo.bulk_get(["stickers_enabled", setting_key])

        enabled = settings_dict.get("stickers_enabled", "true")
        if enabled.lower() != "true":
            return

        file_id: str = settings_dict.get(setting_key, "")
        if file_id:
            await bot.send_sticker(chat_id=chat_id, sticker=file_id)
    except Exception as exc:
        log.warning(
            "sticker_send_failed",
            error=str(exc),
            sticker_type=sticker_type,
            chat_id=chat_id,
        )
