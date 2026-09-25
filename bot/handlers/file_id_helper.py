"""Admin-only file_id helper handler."""
import structlog
from aiogram import Router, F
from aiogram.filters import Filter
from aiogram.types import Message
from config import settings

router = Router(name="file_id_helper")
log = structlog.get_logger()


class IsAdmin(Filter):
    """Pass only if sender is in the ADMIN_IDS list."""
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None and message.from_user.id in settings.admin_id_list


@router.message(IsAdmin(), F.photo)
async def handle_photo_file_id(message: Message) -> None:
    """Rasmning file_id sini qaytaradi."""
    photo = message.photo[-1]  # eng yuqori sifatli versiya
    await message.reply(
        f"📸 *Rasm file\\_id:*\n\n"
        f"`{photo.file_id}`\n\n"
        f"_Admin panelda Poster maydoniga nusxa oling_",
        parse_mode="Markdown",
    )


@router.message(IsAdmin(), F.video)
async def handle_video_file_id(message: Message) -> None:
    """Videoning file_id sini qaytaradi."""
    video = message.video
    size_mb = round((video.file_size or 0) / 1024 / 1024, 1)
    duration_sec = video.duration or 0
    h, m = divmod(duration_sec // 60, 60)
    dur_str = f"{h}s {m}d {duration_sec % 60}s" if h else f"{m}d {duration_sec % 60}s"

    await message.reply(
        f"🎥 *Video file\\_id:*\n\n"
        f"`{video.file_id}`\n\n"
        f"📐 Hajm: *{size_mb} MB*\n"
        f"⏱ Davomiyligi: *{dur_str}*\n\n"
        f"_Admin panelda Video maydoniga nusxa oling_",
        parse_mode="Markdown",
    )


@router.message(IsAdmin(), F.document)
async def handle_document_file_id(message: Message) -> None:
    """Hujjat (video fayl) ning file_id sini qaytaradi."""
    doc = message.document
    size_mb = round((doc.file_size or 0) / 1024 / 1024, 1)
    await message.reply(
        f"📄 *Fayl file\\_id:*\n\n"
        f"`{doc.file_id}`\n\n"
        f"📎 Nom: *{doc.file_name or 'nomsiz'}*\n"
        f"📐 Hajm: *{size_mb} MB*",
        parse_mode="Markdown",
    )


@router.message(IsAdmin(), F.sticker)
async def handle_sticker_file_id(message: Message) -> None:
    """Stikerning file_id sini qaytaradi."""
    sticker = message.sticker
    await message.reply(
        f"😊 *Stiker file\\_id:*\n\n"
        f"`{sticker.file_id}`\n\n"
        f"_Admin panelda Sozlamalar → Stikerlar bo'limiga nusxa oling_",
        parse_mode="Markdown",
    )
