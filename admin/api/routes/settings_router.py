"""App settings routes (texts, stickers, etc)."""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from database.repositories.setting_repo import SettingRepository
from admin.api.middlewares.auth import get_current_admin
from aiogram import Bot
from config import settings
import structlog

log = structlog.get_logger()
router = APIRouter()


async def sync_telegram_descriptions(bot_desc: Optional[str] = None, bot_short: Optional[str] = None) -> dict:
    """Helper to update Telegram Bot API description and short description."""
    if not settings.bot_token:
        return {"ok": False, "error": "Bot token not configured"}

    bot = Bot(token=settings.bot_token)
    results = {}
    try:
        if bot_desc is not None:
            # Telegram description limit is 512 characters
            clean_desc = bot_desc.strip()[:512]
            await bot.set_my_description(description=clean_desc)
            results["bot_description"] = "synced"
        if bot_short is not None:
            # Telegram short description limit is 120 characters
            clean_short = bot_short.strip()[:120]
            await bot.set_my_short_description(short_description=clean_short)
            results["bot_short_description"] = "synced"
        return {"ok": True, "details": results}
    except Exception as e:
        log.warning("telegram_description_sync_failed", error=str(e))
        return {"ok": False, "error": str(e)}
    finally:
        await bot.session.close()


@router.get("")
async def get_all_settings(
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = SettingRepository(session)
    settings_list = await repo.get_all()
    return {s.key: s.value for s in settings_list}


@router.put("")
async def update_settings(
    body: dict,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = SettingRepository(session)
    for key, value in body.items():
        await repo.set(key, str(value))
    await session.commit()

    # Automatically sync to Telegram if description keys were modified
    sync_desc = body.get("bot_description")
    sync_short = body.get("bot_short_description")
    telegram_sync = None
    if sync_desc is not None or sync_short is not None:
        telegram_sync = await sync_telegram_descriptions(sync_desc, sync_short)

    return {"ok": True, "telegram_sync": telegram_sync}


@router.post("/sync-telegram")
async def sync_telegram_endpoint(
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Manually force sync descriptions to Telegram Bot API."""
    repo = SettingRepository(session)
    desc = await repo.get("bot_description")
    short_desc = await repo.get("bot_short_description")
    res = await sync_telegram_descriptions(desc, short_desc)
    return res


@router.put("/{key}")
async def update_setting(
    key: str,
    body: dict,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = SettingRepository(session)
    val = str(body.get("value", ""))
    await repo.set(key, val)
    await session.commit()

    if key == "bot_description":
        await sync_telegram_descriptions(bot_desc=val)
    elif key == "bot_short_description":
        await sync_telegram_descriptions(bot_short=val)

    return {"ok": True}
