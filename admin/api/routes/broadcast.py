"""Broadcast messages to all users with rich buttons, media and targeting."""
import asyncio
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, update
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from database.engine import get_db, engine
from database.models.admin import Admin
from database.models.user import User
from database.repositories.user_repo import UserRepository
from admin.api.middlewares.auth import get_current_admin
from config import settings
import structlog

router = APIRouter()
log = structlog.get_logger()

# In-memory store for broadcast progress (keyed by broadcast_id)
broadcast_status: dict[str, dict] = {}


class BroadcastButton(BaseModel):
    text: str
    url: str


class BroadcastRequest(BaseModel):
    text: str
    parse_mode: str = "Markdown"  # "Markdown" or "HTML"
    photo_file_id: Optional[str] = None
    video_file_id: Optional[str] = None
    buttons: Optional[List[BroadcastButton]] = None
    pin_message: bool = False
    disable_notification: bool = False
    target_audience: str = "all"  # "all" | "active" | "test_admin"


async def do_broadcast(
    broadcast_id: str,
    request: BroadcastRequest,
    sender_admin_id: Optional[int] = None,
    sender_admin_tg_id: Optional[int] = None,
) -> None:
    """Background task: send rich messages according to target_audience."""
    pm = ParseMode.HTML if request.parse_mode.upper() == "HTML" else ParseMode.MARKDOWN
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=pm),
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    sent = 0
    failed = 0
    blocked = 0
    start_time = time.time()

    # Build inline keyboard if buttons provided
    kb: Optional[InlineKeyboardMarkup] = None
    if request.buttons and len(request.buttons) > 0:
        builder = InlineKeyboardBuilder()
        for b in request.buttons:
            if b.text.strip() and b.url.strip():
                builder.row(InlineKeyboardButton(text=b.text.strip(), url=b.url.strip()))
        kb = builder.as_markup()

    try:
        async with SessionLocal() as session:
            user_repo = UserRepository(session)

            if request.target_audience == "test_admin":
                # Send test to admin's Telegram ID
                tg_id = sender_admin_tg_id
                if not tg_id and settings.admin_id_list:
                    tg_id = settings.admin_id_list[0]
                user_ids = [tg_id] if tg_id else []
            elif request.target_audience == "active":
                # Active in last 30 days
                user_ids = await user_repo.get_broadcast_user_ids(active_days=30)
            else:
                # All non-blocked users
                user_ids = await user_repo.get_broadcast_user_ids(active_days=None)

        broadcast_status[broadcast_id] = {
            "total": len(user_ids),
            "sent": 0,
            "failed": 0,
            "blocked": 0,
            "done": False,
            "target_audience": request.target_audience,
            "duration_seconds": 0,
        }

        blocked_ids_to_update = []

        for uid in user_ids:
            try:
                msg = None
                if request.photo_file_id and request.photo_file_id.strip():
                    msg = await bot.send_photo(
                        chat_id=uid,
                        photo=request.photo_file_id.strip(),
                        caption=request.text,
                        reply_markup=kb,
                        disable_notification=request.disable_notification,
                    )
                elif request.video_file_id and request.video_file_id.strip():
                    msg = await bot.send_video(
                        chat_id=uid,
                        video=request.video_file_id.strip(),
                        caption=request.text,
                        reply_markup=kb,
                        disable_notification=request.disable_notification,
                    )
                else:
                    msg = await bot.send_message(
                        chat_id=uid,
                        text=request.text,
                        reply_markup=kb,
                        disable_notification=request.disable_notification,
                    )

                if request.pin_message and msg:
                    try:
                        await bot.pin_chat_message(
                            chat_id=uid,
                            message_id=msg.message_id,
                            disable_notification=True,
                        )
                    except Exception:
                        pass

                sent += 1
            except TelegramForbiddenError:
                blocked += 1
                blocked_ids_to_update.append(uid)
            except Exception as e:
                err_str = str(e).lower()
                if "blocked" in err_str or "deactivated" in err_str:
                    blocked += 1
                    blocked_ids_to_update.append(uid)
                else:
                    failed += 1
                log.warning("broadcast_item_failed", user_id=uid, error=str(e))

            broadcast_status[broadcast_id].update(
                {
                    "sent": sent,
                    "failed": failed,
                    "blocked": blocked,
                    "duration_seconds": round(time.time() - start_time, 1),
                }
            )
            await asyncio.sleep(0.04)  # ~25 msg/s — safe Telegram limit

        # Bulk update blocked users in database
        if blocked_ids_to_update:
            try:
                async with SessionLocal() as session:
                    await session.execute(
                        update(User)
                        .where(User.telegram_id.in_(blocked_ids_to_update))
                        .values(is_blocked=True)
                    )
                    await session.commit()
            except Exception as e:
                log.warning("broadcast_blocked_update_failed", error=str(e))

    finally:
        await bot.session.close()
        broadcast_status[broadcast_id]["done"] = True
        broadcast_status[broadcast_id]["duration_seconds"] = round(time.time() - start_time, 1)
        log.info(
            "broadcast_done",
            broadcast_id=broadcast_id,
            sent=sent,
            failed=failed,
            blocked=blocked,
        )


@router.post("")
async def send_broadcast(
    body: BroadcastRequest,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin),
):
    if body.target_audience == "test_admin" and not admin.telegram_id and not settings.admin_id_list:
        raise HTTPException(
            status_code=400,
            detail="Admin Telegram ID topilmadi. Avval admin profilingizga yoki .env ga ADMIN_IDS ni kiriting.",
        )

    bid = str(uuid.uuid4())[:8]
    background_tasks.add_task(
        do_broadcast,
        bid,
        body,
        sender_admin_id=admin.id,
        sender_admin_tg_id=admin.telegram_id,
    )
    return {
        "broadcast_id": bid,
        "message": "Reklama yuborish boshlandi",
        "target_audience": body.target_audience,
    }


@router.get("/status/{broadcast_id}")
async def get_broadcast_status(
    broadcast_id: str,
    admin: Admin = Depends(get_current_admin),
):
    status = broadcast_status.get(broadcast_id)
    if not status:
        raise HTTPException(status_code=404, detail="Broadcast topilmadi")
    return status
