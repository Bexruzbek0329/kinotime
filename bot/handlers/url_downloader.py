"""Admin-only video downloader from Web/Google/Social media URLs."""
import html
import os
import re
import structlog
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.file_id_helper import is_admin_user
from bot.services.video_downloader import download_video
from database.models.user import User

router = Router(name="url_downloader")
log = structlog.get_logger()

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


async def process_video_url(
    message: Message,
    bot: Bot,
    url: str,
) -> None:
    """Download video from URL and send to Telegram with its file_id."""
    status_msg = await message.reply(
        "⏳ <b>Video yuklab olinmoqda...</b>\n"
        "<i>Iltimos kuting, havola tekshirilmoqda va serverga yuklanmoqda...</i>",
        parse_mode="HTML",
    )

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="upload_video")
    except Exception:
        pass

    try:
        result = await download_video(url)
    except Exception as e:
        log.error("video_download_error", error=str(e), url=url)
        try:
            await status_msg.edit_text(
                "❌ <b>Xatolik yuz berdi:</b> Videoni yuklab bo'lmadi.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    if not result:
        try:
            await status_msg.edit_text(
                "❌ <b>Ushbu havoladan video topilmadi yoki yuklab bo'lmadi.</b>\n\n"
                "<i>💡 Havola to'g'ri va ommaga ochiqligini (private emasligini) tekshiring.</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    if result.get("error") == "size_limit":
        size_mb = round(result.get("size", 0) / 1024 / 1024, 1)
        try:
            await status_msg.edit_text(
                f"⚠️ <b>Video hajmi juda katta ({size_mb} MB)!</b>\n\n"
                "Telegram Bot API limiti bo'yicha botlar faqat <b>50 MB</b> gacha bo'lgan videolarni yuklay oladi.\n"
                "<i>💡 Maslahat: Qisqaroq yoki pastroq sifatdagi video havolasini yuborib ko'ring.</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    file_path = result.get("file_path")
    if not file_path or not os.path.exists(file_path):
        try:
            await status_msg.edit_text(
                "❌ <b>Faylni saqlashda xatolik yuz berdi.</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    title = result.get("title", "Video")
    safe_title = html.escape(title)
    duration = result.get("duration", 0)
    size_mb = result.get("size_mb", 0)
    width = result.get("width")
    height = result.get("height")

    h, m = divmod(duration // 60, 60)
    dur_str = f"{h}s {m}d {duration % 60}s" if h else f"{m}d {duration % 60}s" if m else f"{duration}s"

    try:
        try:
            await status_msg.edit_text(
                "📤 <b>Video Telegramga yuklanmoqda...</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass

        sent = await message.reply_video(
            video=FSInputFile(file_path),
            caption=(
                f"🎬 <b>{safe_title}</b>\n\n"
                f"⏱ Davomiyligi: <b>{dur_str}</b>\n"
                f"⚖️ Hajmi: <b>{size_mb} MB</b>\n\n"
                f"<i>⏳ File ID olinmoqda...</i>"
            ),
            duration=duration if duration > 0 else None,
            width=width,
            height=height,
            supports_streaming=True,
            parse_mode="HTML",
        )

        if sent.video:
            file_id = sent.video.file_id
            full_caption = (
                f"🎬 <b>{safe_title}</b>\n\n"
                f"⏱ Davomiyligi: <b>{dur_str}</b>\n"
                f"⚖️ Hajmi: <b>{size_mb} MB</b>\n\n"
                f"🆔 <b>Telegram File ID:</b>\n"
                f"<code>{file_id}</code>\n\n"
                f"<i>💡 Nusxa olish uchun File ID ustiga bosing! Ushbu kodni Admin panelda film, treyler yoki serial qismiga qo'yishingiz mumkin.</i>"
            )
            try:
                await sent.edit_caption(caption=full_caption, parse_mode="HTML")
            except Exception:
                pass

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as exc:
        log.error("video_upload_to_telegram_failed", error=str(exc))
        try:
            await status_msg.edit_text(
                f"❌ <b>Telegramga yuklashda xatolik yuz berdi:</b>\n<code>{html.escape(str(exc))}</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass
    finally:
        # Always remove temporary file from disk immediately
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@router.message(Command("dl", "download", "url"), StateFilter("*"))
async def cmd_download_video(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
    db_user: User | None = None,
) -> None:
    """Handle /dl <url> command from admins."""
    if not message.from_user:
        return
    if not await is_admin_user(message.from_user.id, session, db_user):
        return  # Non-admins get nothing

    await state.clear()

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(
            "ℹ️ <b>Video yuklab olish uchun havola yuboring:</b>\n\n"
            "<code>/dl https://...</code>\n\n"
            "<i>Yoki shunchaki to'g'ridan-to'g'ri video havolasini yuboring.</i>",
            parse_mode="HTML",
        )
        return

    url = parts[1].strip()
    match = URL_PATTERN.search(url)
    if not match:
        await message.reply("❌ Yaroqsiz havola kiritildi.", parse_mode="HTML")
        return

    await process_video_url(message, bot, match.group(0))


@router.message(F.text.regexp(r"https?://\S+"), StateFilter("*"))
async def handle_direct_url_message(
    message: Message,
    bot: Bot,
    session: AsyncSession,
    state: FSMContext,
    db_user: User | None = None,
) -> None:
    """If an authorized admin sends a web URL, auto-download video."""
    if not message.from_user:
        return
    if not await is_admin_user(message.from_user.id, session, db_user):
        return  # Regular users get NOTHING

    await state.clear()

    text = message.text or ""
    match = URL_PATTERN.search(text)
    if not match:
        return

    url = match.group(0)
    await process_video_url(message, bot, url)

