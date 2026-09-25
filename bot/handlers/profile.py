"""User profile display and favourites list callbacks."""
import math

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import favorites_keyboard, profile_keyboard
from bot.utils.formatting import format_profile
from config import settings
from database.repositories.favorite_repo import FavoriteRepository
from database.repositories.user_repo import UserRepository

router = Router(name="profile")


# ---------------------------------------------------------------------------
# 👤 Profil — reply keyboard button
# ---------------------------------------------------------------------------


@router.message(F.text == "\U0001f464 Profil")
async def menu_profile(
    message: Message,
    session: AsyncSession,
    db_user,
) -> None:
    """Display the user's profile stats card."""
    if not db_user:
        await message.answer("\U0001f614 Profil topilmadi.")
        return

    user_repo = UserRepository(session)
    stats: dict = await user_repo.get_user_stats(db_user.id)

    text = format_profile(
        user={
            "telegram_id": db_user.telegram_id,
            "joined_at": db_user.joined_at,
        },
        stats=stats,
    )
    await message.answer(text, reply_markup=profile_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# nav:profile — return to profile from favourites
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "nav:profile")
async def cb_profile(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user,
) -> None:
    """Re-render the profile card (e.g. when navigating back from favourites)."""
    await callback.answer()
    if not db_user:
        return

    user_repo = UserRepository(session)
    stats: dict = await user_repo.get_user_stats(db_user.id)

    text = format_profile(
        user={
            "telegram_id": db_user.telegram_id,
            "joined_at": db_user.joined_at,
        },
        stats=stats,
    )
    await callback.message.answer(
        text, reply_markup=profile_keyboard(), parse_mode="Markdown"
    )


# ---------------------------------------------------------------------------
# fav:page — paginated favourites list
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("fav:page:"))
async def cb_favorites(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user,
) -> None:
    """
    Display a paginated favourites list.

    The page number is embedded in the callback data as ``fav:page:<n>``.
    On the first request (page 1) the handler may need to send a new
    message if the current message type cannot be edited (e.g. a photo).
    """
    page = int(callback.data.split(":")[2])
    per_page: int = settings.movies_per_page

    if not db_user:
        await callback.answer("Xatolik.", show_alert=True)
        return

    fav_repo = FavoriteRepository(session)
    movies, total = await fav_repo.get_by_user(
        db_user.id, page=page, per_page=per_page
    )
    total_pages = max(1, math.ceil(total / per_page))

    await callback.answer()

    if not movies:
        await callback.message.answer("\U0001f494 Sevimlilar bo\u2018sh.")
        return

    movie_dicts = [{"id": m.id, "title": m.title} for m in movies]
    text = f"\u2764\ufe0f *SEVIMLILAR*\n\n_{total}_ ta kino"

    try:
        await callback.message.edit_text(
            text,
            reply_markup=favorites_keyboard(movie_dicts, page, total_pages),
            parse_mode="Markdown",
        )
    except Exception:
        # Fallback for non-text messages (e.g. photo captions)
        await callback.message.answer(
            text,
            reply_markup=favorites_keyboard(movie_dicts, page, total_pages),
            parse_mode="Markdown",
        )
