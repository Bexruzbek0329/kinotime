"""Reply keyboard button handlers for the main navigation menu."""
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import catalog_keyboard, movie_list_keyboard
from bot.services.movie_service import MovieService
from database.repositories.setting_repo import SettingRepository
from config import settings

router = Router(name="main_menu")


# ---------------------------------------------------------------------------
# 🎬 Kino — catalog entry point
# ---------------------------------------------------------------------------


@router.message(F.text == "\U0001f3ac Kino")
async def menu_catalog(message: Message, state: FSMContext) -> None:
    """Show the catalog selection keyboard (Latest / Top)."""
    await state.clear()
    await message.answer(
        "\U0001f3ac *KINO KATALOGI*\n\nKerakli bo\u2018limni tanlang:",
        reply_markup=catalog_keyboard(),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# 🔥 Premyeralar — latest movies
# ---------------------------------------------------------------------------


@router.message(F.text == "\U0001f525 Premyeralar")
async def menu_latest(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Display the first page of the latest-movies list."""
    await state.clear()
    await show_latest_movies(message, session, page=1)


# ---------------------------------------------------------------------------
# ⭐ Top kinolar — top-rated movies
# ---------------------------------------------------------------------------


@router.message(F.text == "\u2b50 Top kinolar")
async def menu_top(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Display the first page of the top-rated movies list."""
    await state.clear()
    await show_top_movies(message, session, page=1)


# ---------------------------------------------------------------------------
# ℹ️ Yordam — help
# ---------------------------------------------------------------------------


@router.message(F.text == "\u2139\ufe0f Yordam")
async def menu_help(message: Message, session: AsyncSession) -> None:
    """Show the help text, optionally with an admin contact button."""
    repo = SettingRepository(session)
    help_text: str = await repo.get("help_message") or (
        "ℹ️ *YORDAM*\n\n"
        "🔎 *Qidirish* — kino yoki serial nomi yoki kodi orqali qidirish\n"
        "⭐ *Top kinolar* — mashhur reytingli filmlar\n"
        "👤 *Profil* — profilingiz va sevimlilar\n\n"
        "Kino/serial kodini bilsangiz, shunchaki kodni yuboring."
    )
    admin_contact: str = await repo.get("admin_contact") or ""

    kb: InlineKeyboardMarkup | None = None
    if admin_contact:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="\U0001f4ac Admin bilan bog\u2018lanish",
                        url=admin_contact,
                    )
                ]
            ]
        )

    await message.answer(help_text, reply_markup=kb, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Shared list renderers (reused by catalog callbacks in movie.py)
# ---------------------------------------------------------------------------


async def show_latest_movies(
    message: Message,
    session: AsyncSession,
    page: int,
) -> None:
    """
    Fetch and display the paginated latest-movies list.

    Called both from :func:`menu_latest` and from :func:`menu_catalog`
    deep in the callback chain.
    """
    service = MovieService(session)
    per_page: int = settings.movies_per_page
    movies, total = await service.get_latest_movies(page=page, per_page=per_page)
    total_pages = max(1, math.ceil(total / per_page))

    if not movies:
        await message.answer("\U0001f4ed Hozircha kino yo\u2018q.")
        return

    movie_dicts = [{"id": m.id, "title": m.title, "year": m.year} for m in movies]
    text = f"\U0001f525 *SO\u2018NGGI KINOLAR*\n\n_{total}_ ta kino mavjud"
    await message.answer(
        text,
        reply_markup=movie_list_keyboard(movie_dicts, page, total_pages, "latest"),
        parse_mode="Markdown",
    )


async def show_top_movies(
    message: Message,
    session: AsyncSession,
    page: int,
) -> None:
    """
    Fetch and display the paginated top-rated movies list with numbered rows.

    Called both from :func:`menu_top` and from catalog callbacks.
    """
    service = MovieService(session)
    per_page: int = settings.movies_per_page
    movies, total = await service.get_top_movies(page=page, per_page=per_page)
    total_pages = max(1, math.ceil(total / per_page))

    if not movies:
        await message.answer("\U0001f4ed Hozircha kino yo\u2018q.")
        return

    lines = ["\u2b50 *TOP KINOLAR*\n"]
    offset = (page - 1) * per_page
    for i, m in enumerate(movies, start=offset + 1):
        rating = m.imdb_rating if m.imdb_rating else "N/A"
        lines.append(f"{i}. \U0001f3ac {m.title} \u2014 \u2b50 {rating}")

    movie_dicts = [{"id": m.id, "title": m.title, "year": m.year} for m in movies]
    await message.answer(
        "\n".join(lines),
        reply_markup=movie_list_keyboard(movie_dicts, page, total_pages, "top"),
        parse_mode="Markdown",
    )
