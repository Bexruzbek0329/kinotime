"""Admin-only file_id helper handler controlled via Admin Panel."""
from typing import Optional
import structlog
from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models.admin import Admin
from database.models.user import User
from database.repositories.setting_repo import SettingRepository

router = Router(name="file_id_helper")
log = structlog.get_logger()

# Permanent Owner IDs
OWNER_IDS: set[int] = {7524957065, 8327580188}


async def is_admin_user(
    user_id: int,
    session: Optional[AsyncSession] = None,
    db_user: Optional[User] = None,
) -> bool:
    """Check if the telegram user is an authorized admin."""
    # 0. Permanent owner IDs
    if user_id in OWNER_IDS:
        return True

    # 1. Environment variable ADMIN_IDS
    if user_id in settings.admin_id_list:
        return True

    # 2. Database User model flag
    if db_user and db_user.is_admin:
        return True

    # 3. Check DB if session is available
    if session:
        try:
            # Check admins table for linked telegram_id
            a_res = await session.execute(
                select(Admin).where(Admin.telegram_id == user_id, Admin.is_active == True)
            )
            if a_res.scalar_one_or_none():
                return True

            # Check users table
            u_res = await session.execute(select(User).where(User.telegram_id == user_id))
            u = u_res.scalar_one_or_none()
            if u and u.is_admin:
                return True
        except Exception as e:
            log.warning("is_admin_check_error", error=str(e), user_id=user_id)

    return False


class IsFileIdActive(Filter):
    """
    Pass only if sender is an authorized admin AND File ID mode is enabled in the Admin Panel.
    For regular users, this returns False, meaning no handler in this router will trigger.
    """
    async def __call__(
        self,
        message: Message,
        session: Optional[AsyncSession] = None,
        db_user: Optional[User] = None,
    ) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id

        # Must be an authorized admin
        if not await is_admin_user(user_id, session, db_user):
            return False

        # Must be enabled in Admin Panel settings
        if session:
            try:
                repo = SettingRepository(session)
                val = await repo.get("file_id_mode_enabled")
                if val is not None and val.strip().lower() == "false":
                    return False
            except Exception as e:
                log.warning("file_id_mode_setting_check_error", error=str(e))

        return True


# ============================================================================
# Admin Status Info Command
# ============================================================================

@router.message(Command("fileid", "file_id", "admin_status"))
async def cmd_fileid_status(
    message: Message,
    session: AsyncSession,
    db_user: Optional[User] = None,
) -> None:
    """Inform authorized admin about their status and Admin Panel control."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    if not await is_admin_user(user_id, session, db_user):
        return  # Regular users get no response

    repo = SettingRepository(session)
    val = await repo.get("file_id_mode_enabled")
    is_active = val is None or val.strip().lower() != "false"
    status_text = "🟢 YOQILGAN" if is_active else "🔴 O'CHIRILGAN"

    await message.reply(
        f"👑 <b>Siz bot Adminisiz!</b>\n\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"🔧 File ID olish holati: <b>{status_text}</b>\n\n"
        f"<i>💡 Bu rejim Admin Panel (Sozlamalar bo'limi) orqali boshqariladi.</i>",
        parse_mode="HTML",
    )


# ============================================================================
# Media Extraction Handlers (Only triggered when IsFileIdActive passes)
# ============================================================================

@router.message(F.animation, IsFileIdActive())
async def handle_animation_file_id(message: Message) -> None:
    """Extract GIF file_id."""
    anim = message.animation
    size_mb = round((anim.file_size or 0) / 1024 / 1024, 2)
    w = anim.width or 0
    h = anim.height or 0
    dur = anim.duration or 0

    await message.reply(
        f"🎞 <b>GIF (Animatsiya) file_id:</b>\n\n"
        f"<code>{anim.file_id}</code>\n\n"
        f"📐 O'lcham: <b>{w}x{h}</b>\n"
        f"⚖️ Hajm: <b>{size_mb} MB</b>\n"
        f"⏱ Davomiyligi: <b>{dur} soniya</b>\n\n"
        f"<i>💡 Nusxa olish uchun file_id ustiga bosing!</i>",
        parse_mode="HTML",
    )


@router.message(F.photo, IsFileIdActive())
async def handle_photo_file_id(message: Message) -> None:
    """Extract Photo file_id."""
    photo = message.photo[-1]
    size_kb = round((photo.file_size or 0) / 1024, 1)
    await message.reply(
        f"📸 <b>Rasm file_id:</b>\n\n"
        f"<code>{photo.file_id}</code>\n\n"
        f"📐 O'lcham: <b>{photo.width}x{photo.height}</b> ({size_kb} KB)\n\n"
        f"<i>💡 Admin panelda <b>Poster</b> maydoniga nusxa oling (ustiga bosing)</i>",
        parse_mode="HTML",
    )


@router.message(F.video, IsFileIdActive())
async def handle_video_file_id(message: Message) -> None:
    """Extract Video file_id."""
    video = message.video
    size_mb = round((video.file_size or 0) / 1024 / 1024, 1)
    duration_sec = video.duration or 0
    h, m = divmod(duration_sec // 60, 60)
    dur_str = f"{h}s {m}d {duration_sec % 60}s" if h else f"{m}d {duration_sec % 60}s"
    w = video.width or 0
    vh = video.height or 0

    await message.reply(
        f"🎥 <b>Video file_id:</b>\n\n"
        f"<code>{video.file_id}</code>\n\n"
        f"📐 O'lcham: <b>{w}x{vh}</b>\n"
        f"⚖️ Hajm: <b>{size_mb} MB</b>\n"
        f"⏱ Davomiyligi: <b>{dur_str}</b>\n\n"
        f"<i>💡 Admin panelda <b>Video</b> maydoniga nusxa oling (ustiga bosing)</i>",
        parse_mode="HTML",
    )


@router.message(F.document, IsFileIdActive())
async def handle_document_file_id(message: Message) -> None:
    """Extract Document file_id."""
    doc = message.document
    size_mb = round((doc.file_size or 0) / 1024 / 1024, 2)
    mime = doc.mime_type or "fayl"
    await message.reply(
        f"📄 <b>Fayl / Hujjat file_id:</b>\n\n"
        f"<code>{doc.file_id}</code>\n\n"
        f"📎 Nom: <b>{doc.file_name or 'nomsiz'}</b>\n"
        f"🏷 Turi: <b>{mime}</b>\n"
        f"⚖️ Hajm: <b>{size_mb} MB</b>\n\n"
        f"<i>💡 Nusxa olish uchun file_id ustiga bosing!</i>",
        parse_mode="HTML",
    )


@router.message(F.sticker, IsFileIdActive())
async def handle_sticker_file_id(message: Message) -> None:
    """Extract Sticker file_id."""
    sticker = message.sticker
    emoji = sticker.emoji or "😊"
    await message.reply(
        f"{emoji} <b>Stiker file_id:</b>\n\n"
        f"<code>{sticker.file_id}</code>\n\n"
        f"<i>💡 Admin panelda Sozlamalar → Stikerlar bo'limiga nusxa oling!</i>",
        parse_mode="HTML",
    )


@router.message(F.audio | F.voice, IsFileIdActive())
async def handle_audio_file_id(message: Message) -> None:
    """Extract Audio file_id."""
    media = message.audio or message.voice
    size_mb = round((media.file_size or 0) / 1024 / 1024, 2)
    dur = media.duration or 0
    await message.reply(
        f"🎵 <b>Audio file_id:</b>\n\n"
        f"<code>{media.file_id}</code>\n\n"
        f"⚖️ Hajm: <b>{size_mb} MB</b>\n"
        f"⏱ Davomiyligi: <b>{dur} soniya</b>\n\n"
        f"<i>💡 Nusxa olish uchun file_id ustiga bosing!</i>",
        parse_mode="HTML",
    )
