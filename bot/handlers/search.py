"""Search and numeric-code lookup handlers."""
import math

import structlog
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import back_to_menu_keyboard, movie_list_keyboard
from bot.services.movie_service import MovieService
from bot.states.search import SearchStates
from bot.utils.formatting import format_not_found, format_search_results
from bot.utils.search import normalize_query
from bot.utils.stickers import send_sticker
from config import settings
from database.repositories.search_repo import SearchRepository
from database.repositories.setting_repo import SettingRepository

router = Router(name="search")
log = structlog.get_logger()


# ---------------------------------------------------------------------------
# 🔍 Qidirish — enter search mode
# ---------------------------------------------------------------------------


@router.message(F.text == "\U0001f50e Qidirish")
async def menu_search(message: Message, state: FSMContext) -> None:
    """Set FSM to waiting_for_query and prompt the user for input."""
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        "\U0001f50e *QIDIRISH*\n\n"
        "Kino nomi yoki kodini yuboring.\n\n"
        "_Misol: Interstellar yoki 10245_",
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# FSM: waiting_for_query state
# ---------------------------------------------------------------------------


@router.message(StateFilter(SearchStates.waiting_for_query))
async def handle_search_query(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot,
) -> None:
    """Accept any text while in the search state and run the query."""
    await state.clear()
    query = (message.text or "").strip()
    if not query:
        return
    await process_search(message, session, bot, query)


# ---------------------------------------------------------------------------
# Numeric code input (any state)
# ---------------------------------------------------------------------------


@router.message(F.text.regexp(r"^\d{1,10}$"))
async def handle_code_input(
    message: Message,
    session: AsyncSession,
    bot,
) -> None:
    """
    Intercept any message that looks like a numeric movie code and display
    the matching movie card directly, bypassing the search index.
    """
    code = (message.text or "").strip()
    from bot.handlers.movie import send_movie_card_by_code

    await send_movie_card_by_code(message, session, bot, code)


# ---------------------------------------------------------------------------
# Core search logic (also called by paginated list callbacks)
# ---------------------------------------------------------------------------


async def process_search(
    message: Message,
    session: AsyncSession,
    bot,
    query: str,
    page: int = 1,
) -> None:
    """
    Execute a search query and render the result list or a not-found message.

    Args:
        message:  The originating Telegram message (used for replies).
        session:  Active DB session.
        bot:      Bot instance (for sticker sending).
        query:    Raw user query string.
        page:     Pagination page (default 1).
    """
    per_page: int = settings.movies_per_page
    service = MovieService(session)
    search_repo = SearchRepository(session)

    norm_query = normalize_query(query)
    movies, total = await service.search_movies(norm_query, page=page, per_page=per_page)

    # Persist search analytics regardless of outcome
    await search_repo.log_search(query=norm_query, results_count=total)

    if not movies:
        await send_sticker(bot, message.chat.id, "not_found", session)

        setting_repo = SettingRepository(session)
        not_found_msg: str = (
            await setting_repo.get("not_found_message") or format_not_found(query)
        )
        await message.answer(
            not_found_msg + f"\n\n\U0001f50e Qidiruv: `{query}`",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="Markdown",
        )
        log.info("search_no_results", query=norm_query)
        return

    total_pages = max(1, math.ceil(total / per_page))
    movie_dicts = [{"id": m.id, "title": m.title, "year": m.year} for m in movies]
    text = format_search_results(query, movie_dicts, total)

    await message.answer(
        text,
        reply_markup=movie_list_keyboard(
            movie_dicts, page, total_pages, f"search:{norm_query}"
        ),
        parse_mode="Markdown",
    )
    log.info("search_results", query=norm_query, total=total, page=page)


# ---------------------------------------------------------------------------
# Direct text search fallback (user types name directly without pressing 🔍)
# ---------------------------------------------------------------------------

KNOWN_MENU_TEXTS = {
    "\U0001f50e Qidirish",   # 🔎 Qidirish
    "\U0001f50d Qidirish",   # 🔍 Qidirish
    "\u2b50 Top kinolar",     # ⭐ Top kinolar
    "\U0001f464 Profil",      # 👤 Profil
    "\u2139\ufe0f Yordam",    # ℹ️ Yordam
    "\U0001f3ac Kino",        # 🎬 Kino
    "\U0001f4fa Serial",      # 📺 Serial
    "\U0001f525 Premyeralar",  # 🔥 Premyeralar
}



@router.message(F.text, ~F.text.startswith("/"))
async def handle_direct_text_search(
    message: Message,
    session: AsyncSession,
    bot,
) -> None:
    """
    Catch any plain text input that is not a command, not a menu button,
    and not a numeric code, and run a movie search automatically.
    """
    text = (message.text or "").strip()
    if not text or text in KNOWN_MENU_TEXTS:
        return
    await process_search(message, session, bot, text)

