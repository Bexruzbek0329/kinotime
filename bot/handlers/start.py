"""Handle /start command and deep-link payloads."""
import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import main_menu_keyboard
from bot.utils.deep_link import parse_start_param
from bot.utils.stickers import send_sticker
from database.repositories.setting_repo import SettingRepository

router = Router(name="start")
log = structlog.get_logger()

_DEFAULT_WELCOME = (
    "\U0001f3ac *KINO BOT*\n\n"
    "Assalomu alaykum! \U0001f44b\n\n"
    "Bu yerda sevimli filmlaringizni\n"
    "tez va qulay topishingiz mumkin.\n\n"
    "\U0001f50e Kino nomi yoki kodini yuboring.\n\n"
    "Yoki pastdagi menyudan foydalaning \U0001f447"
)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot,
) -> None:
    """
    Entry point for every new or returning user.

    Flow:
    1. Clear any active FSM state.
    2. Send the welcome sticker (if configured).
    3. Display the welcome message with the main reply keyboard.
    4. If a ``movie_<id>`` deep-link param is present, open that movie card
       immediately after the welcome message.
    """
    await state.clear()

    # Fetch customisable welcome text from the database
    setting_repo = SettingRepository(session)
    welcome_msg: str = await setting_repo.get("welcome_message") or _DEFAULT_WELCOME

    # Always try to send the welcome sticker first
    await send_sticker(bot, message.chat.id, "start", session)

    await message.answer(
        welcome_msg,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

    log.info(
        "user_start",
        user_id=message.from_user.id if message.from_user else None,
        text=message.text,
    )

    # Handle deep links — e.g. /start movie_42
    parts = (message.text or "").split(maxsplit=1)
    start_param = parts[1] if len(parts) > 1 else None
    deep = parse_start_param(start_param)

    if deep and deep["type"] == "movie":
        # Lazy import to avoid circular dependency
        from bot.handlers.movie import send_movie_card

        await send_movie_card(message, session, bot, deep["id"])
