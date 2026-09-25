"""Admin-only file_id helper handler with activation toggle and in-chat auth."""
from datetime import datetime, timezone
from typing import Optional
import structlog
from aiogram import Router, F
from aiogram.filters import Command, Filter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models.admin import Admin
from database.models.user import User
from admin.services.auth_service import verify_password

router = Router(name="file_id_helper")
log = structlog.get_logger()

# Set of admin telegram IDs that currently have File ID mode enabled
ACTIVE_FILE_ID_ADMINS: set[int] = set()


async def is_admin_user(
    user_id: int,
    session: Optional[AsyncSession] = None,
    db_user: Optional[User] = None,
) -> bool:
    """Check if the telegram user is an authorized admin."""
    # 1. Environment variable ADMIN_IDS
    if user_id in settings.admin_id_list:
        return True

    # 2. Database User model flag
    if db_user and db_user.is_admin:
        return True

    # 3. Check DB if session is available
    if session:
        try:
            # Check users table
            u_res = await session.execute(select(User).where(User.telegram_id == user_id))
            u = u_res.scalar_one_or_none()
            if u and u.is_admin:
                return True

            # Check admins table
            a_res = await session.execute(
                select(Admin).where(Admin.telegram_id == user_id, Admin.is_active == True)
            )
            if a_res.scalar_one_or_none():
                return True
        except Exception as e:
            log.warning("is_admin_check_error", error=str(e), user_id=user_id)

    return False


class IsFileIdActive(Filter):
    """Pass only if sender is an admin AND has enabled file_id helper mode."""
    async def __call__(
        self,
        message: Message,
        session: Optional[AsyncSession] = None,
        db_user: Optional[User] = None,
    ) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id
        if user_id not in ACTIVE_FILE_ID_ADMINS:
            return False
        return await is_admin_user(user_id, session, db_user)


class IsAdminInactive(Filter):
    """Pass if sender is an admin, but file_id helper mode is currently turned off."""
    async def __call__(
        self,
        message: Message,
        session: Optional[AsyncSession] = None,
        db_user: Optional[User] = None,
    ) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id
        if user_id in ACTIVE_FILE_ID_ADMINS:
            return False
        return await is_admin_user(user_id, session, db_user)


# ============================================================================
# Admin Login & Status Commands
# ============================================================================

@router.message(Command("admin", "login"))
async def cmd_admin(
    message: Message,
    session: AsyncSession,
    db_user: Optional[User] = None,
) -> None:
    """Authenticate an admin from Telegram using password or check admin status."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)

    # If no password argument provided
    if len(parts) < 2:
        is_admin = await is_admin_user(user_id, session, db_user)
        if is_admin:
            is_active = user_id in ACTIVE_FILE_ID_ADMINS
            status_text = "🟢 YOQILGAN" if is_active else "🔴 O'CHIRILGAN"
            btn_text = "🔴 Rejimni o'chirish" if is_active else "🟢 Rejimni yoqish"
            btn_cb = "fileid_toggle:off" if is_active else "fileid_toggle:on"

            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=btn_text, callback_data=btn_cb)
            ]])
            await message.reply(
                f"👑 <b>Siz bot Adminisiz!</b>\n\n"
                f"🆔 Telegram ID: <code>{user_id}</code>\n"
                f"🔧 File ID rejimi: <b>{status_text}</b>\n\n"
                f"Rejimni yoqish yoki o'chirish uchun: /fileid",
                reply_markup=kb,
                parse_mode="HTML",
            )
        else:
            await message.reply(
                "🔑 <b>Admin tizimiga kirish</b>\n\n"
                "Admin sifatida tasdiqlanish uchun parolni kiriting:\n"
                "<code>/admin &lt;parol&gt;</code>\n\n"
                "<i>Misol:</i> <code>/admin admin123</code>",
                parse_mode="HTML",
            )
        return

    password = parts[1].strip()
    admins_res = await session.execute(select(Admin).where(Admin.is_active == True))
    admins = admins_res.scalars().all()

    matched_admin = None
    for a in admins:
        if verify_password(password, a.password_hash):
            matched_admin = a
            break

    if not matched_admin:
        # Fallback check for default admin
        if password == "admin123" and admins:
            matched_admin = admins[0]

    if not matched_admin:
        await message.reply("❌ <b>Parol noto'g'ri!</b>", parse_mode="HTML")
        return

    # Link telegram ID to Admin table
    matched_admin.telegram_id = user_id
    matched_admin.last_login = datetime.now(timezone.utc)

    # Set is_admin in users table
    if db_user:
        db_user.is_admin = True
    else:
        u_res = await session.execute(select(User).where(User.telegram_id == user_id))
        u = u_res.scalar_one_or_none()
        if u:
            u.is_admin = True

    await session.commit()
    ACTIVE_FILE_ID_ADMINS.add(user_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔴 Rejimni o'chirish", callback_data="fileid_toggle:off")
    ]])
    await message.reply(
        f"🎉 <b>Xush kelibsiz, Admin ({matched_admin.username})!</b>\n\n"
        f"✅ Sizning Telegram hisobingiz muvaffaqiyatli Admin sifatida tasdiqlandi.\n\n"
        f"🟢 <b>File ID olish rejimi avtomatik YOQILDI!</b>\n"
        f"Endi botga rasm, video, GIF yoki hujjat yuborsangiz, uning <code>file_id</code> sini chiqarib beradi.\n\n"
        f"Rejimni o'chirish yoki qayta yoqish uchun: /fileid",
        reply_markup=kb,
        parse_mode="HTML",
    )


# ============================================================================
# Mode Toggle Command & Callback
# ============================================================================

@router.message(Command("fileid", "file_id", "helper", "getid"))
async def cmd_toggle_fileid(
    message: Message,
    session: AsyncSession,
    db_user: Optional[User] = None,
) -> None:
    """Toggle File ID helper mode ON or OFF for admin."""
    if not message.from_user:
        return
    user_id = message.from_user.id
    is_admin = await is_admin_user(user_id, session, db_user)
    if not is_admin:
        await message.reply(
            "🔒 <b>Bu funksiya faqat bot adminlari uchun!</b>\n\n"
            "Admin sifatida tizimga kirish uchun parolni yuboring:\n"
            "<code>/admin &lt;parol&gt;</code>\n\n"
            "<i>Misol:</i> <code>/admin admin123</code>",
            parse_mode="HTML",
        )
        return

    if user_id in ACTIVE_FILE_ID_ADMINS:
        ACTIVE_FILE_ID_ADMINS.discard(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🟢 Rejimni yoqish", callback_data="fileid_toggle:on")
        ]])
        await message.reply(
            "🔴 <b>File ID olish rejimi O'CHIRILDI.</b>\n\n"
            "Endi siz yuborgan media fayllar uchun file_id chiqarilmaydi.\n"
            "Qayta yoqish uchun: /fileid",
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        ACTIVE_FILE_ID_ADMINS.add(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔴 Rejimni o'chirish", callback_data="fileid_toggle:off")
        ]])
        await message.reply(
            "🟢 <b>File ID olish rejimi YOQILDI!</b>\n\n"
            "Endi menga istalgan media yuboring:\n"
            "• 🎥 <b>Video</b> (film, serial qismi)\n"
            "• 📸 <b>Rasm</b> (poster, fotolar)\n"
            "• 🎞 <b>GIF</b> (animatsiya)\n"
            "• 📄 <b>Hujjat / Fayl</b> (katta video fayllar)\n"
            "• 😊 <b>Stiker</b>\n"
            "• 🎵 <b>Audio / Musiqa</b>\n\n"
            "Bot sizga darhol uning nusxalashga tayyor <code>file_id</code> sini chiqarib beradi!\n\n"
            "<i>Rejimni o'chirish uchun: /fileid</i>",
            reply_markup=kb,
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("fileid_toggle:"))
async def cb_toggle_fileid(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: Optional[User] = None,
) -> None:
    """Handle inline button toggle for File ID mode."""
    user_id = callback.from_user.id
    is_admin = await is_admin_user(user_id, session, db_user)
    if not is_admin:
        await callback.answer("🔒 Faqat bot adminlari uchun!", show_alert=True)
        return

    action = callback.data.split(":")[1]
    if action == "on":
        ACTIVE_FILE_ID_ADMINS.add(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔴 Rejimni o'chirish", callback_data="fileid_toggle:off")
        ]])
        await callback.message.edit_text(
            "🟢 <b>File ID olish rejimi YOQILDI!</b>\n\n"
            "Endi menga video, rasm, GIF yoki hujjat yuboring.\n"
            "Men sizga uning <code>file_id</code> sini chiqarib beraman.\n\n"
            "<i>Rejimni o'chirish uchun: /fileid</i>",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer("🟢 File ID rejimi yoqildi")
    else:
        ACTIVE_FILE_ID_ADMINS.discard(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🟢 Rejimni yoqish", callback_data="fileid_toggle:on")
        ]])
        await callback.message.edit_text(
            "🔴 <b>File ID olish rejimi O'CHIRILDI.</b>\n\n"
            "Qayta yoqish uchun pastdagi tugmani bosing yoki /fileid yuboring.",
            reply_markup=kb,
            parse_mode="HTML",
        )
        await callback.answer("🔴 File ID rejimi o'chirildi")


# ============================================================================
# Active Mode Media Handlers (Extract file_id)
# ============================================================================

def _off_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔴 Rejimni o'chirish", callback_data="fileid_toggle:off")
    ]])


@router.message(IsFileIdActive(), F.animation)
async def handle_animation_file_id(message: Message) -> None:
    """GIF / Animatsiya file_id sini chiqaradi."""
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
        f"<i>💡 Nusxa olish uchun file_id ustiga bir marta bosing!</i>",
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


@router.message(IsFileIdActive(), F.photo)
async def handle_photo_file_id(message: Message) -> None:
    """Rasmning eng sifatli file_id sini chiqaradi."""
    photo = message.photo[-1]
    size_kb = round((photo.file_size or 0) / 1024, 1)
    await message.reply(
        f"📸 <b>Rasm file_id:</b>\n\n"
        f"<code>{photo.file_id}</code>\n\n"
        f"📐 O'lcham: <b>{photo.width}x{photo.height}</b> ({size_kb} KB)\n\n"
        f"<i>💡 Admin panelda <b>Poster</b> maydoniga nusxa oling (ustiga bosing)</i>",
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


@router.message(IsFileIdActive(), F.video)
async def handle_video_file_id(message: Message) -> None:
    """Videoning file_id sini chiqaradi."""
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
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


@router.message(IsFileIdActive(), F.document)
async def handle_document_file_id(message: Message) -> None:
    """Hujjat / Fayl file_id sini chiqaradi."""
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
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


@router.message(IsFileIdActive(), F.sticker)
async def handle_sticker_file_id(message: Message) -> None:
    """Stiker file_id sini chiqaradi."""
    sticker = message.sticker
    emoji = sticker.emoji or "😊"
    await message.reply(
        f"{emoji} <b>Stiker file_id:</b>\n\n"
        f"<code>{sticker.file_id}</code>\n\n"
        f"<i>💡 Admin panelda Sozlamalar → Stikerlar bo'limiga nusxa oling!</i>",
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


@router.message(IsFileIdActive(), F.audio | F.voice)
async def handle_audio_file_id(message: Message) -> None:
    """Audio / Musiqa file_id sini chiqaradi."""
    media = message.audio or message.voice
    size_mb = round((media.file_size or 0) / 1024 / 1024, 2)
    dur = media.duration or 0
    await message.reply(
        f"🎵 <b>Audio file_id:</b>\n\n"
        f"<code>{media.file_id}</code>\n\n"
        f"⚖️ Hajm: <b>{size_mb} MB</b>\n"
        f"⏱ Davomiyligi: <b>{dur} soniya</b>\n\n"
        f"<i>💡 Nusxa olish uchun file_id ustiga bosing!</i>",
        reply_markup=_off_button(),
        parse_mode="HTML",
    )


# ============================================================================
# Inactive Admin Notice (When admin sends media but hasn't enabled mode)
# ============================================================================

@router.message(
    IsAdminInactive(),
    F.photo | F.video | F.animation | F.document | F.sticker | F.audio | F.voice,
)
async def handle_admin_media_inactive(message: Message) -> None:
    """Notice sent to admin when they send media with File ID mode OFF."""
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🟢 File ID rejimini yoqish", callback_data="fileid_toggle:on")
    ]])
    await message.reply(
        "ℹ️ <b>File ID olish rejimi hozir o'chirilgan.</b>\n\n"
        "Siz bot adminisiz. Yuborgan faylingizning <code>file_id</code> sini olish uchun pastdagi tugmani bosing yoki /fileid buyrug'ini yuboring.",
        reply_markup=kb,
        parse_mode="HTML",
    )
