"""Serial catalog handler — reply keyboard '📺 Serial' button and serial: callbacks."""
import math
import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    movie_list_keyboard,
    serial_catalog_keyboard,
    serial_card_keyboard,
    episode_video_keyboard,
    back_to_menu_keyboard,
)
from bot.services.movie_service import MovieService
from database.models.movie import ContentType
from database.repositories.movie_repo import MovieRepository
from database.repositories.favorite_repo import FavoriteRepository
from database.repositories.setting_repo import SettingRepository
from config import settings

router = Router(name="serial")
log = structlog.get_logger()

SERIAL_CT = ContentType.serial


# ---------------------------------------------------------------------------
# 📺 Serial — reply keyboard entry
# ---------------------------------------------------------------------------


@router.message(F.text == "\U0001f4fa Serial")
async def menu_serial(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """Show serial catalog options."""
    await state.clear()
    service = MovieService(session)
    total_latest, total_count = await _count_serials(service)

    await message.answer(
        f"\U0001f4fa *SERIAL KATALOGI*\n\n"
        f"Jami *{total_count}* ta serial mavjud\n\n"
        "Qaysi bo'limni ko'rmoqchisiz?",
        reply_markup=serial_catalog_keyboard(),
        parse_mode="Markdown",
    )


async def _count_serials(service: MovieService) -> tuple:
    _, latest_total = await service.repo.get_latest(page=1, per_page=1, content_type=SERIAL_CT)
    _, top_total = await service.repo.get_top_rated(page=1, per_page=1, content_type=SERIAL_CT)
    return latest_total, latest_total


# ---------------------------------------------------------------------------
# Serial card delivery
# ---------------------------------------------------------------------------


async def deliver_serial_content(
    target,  # Message or CallbackQuery
    session: AsyncSession,
    movie_id: int,
    user_id: int | None = None,
    season_number: int = 1,
    page: int = 1,
) -> None:
    """Display the serial card with season tabs and episode buttons."""
    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=user_id)
    msg_target = target if isinstance(target, Message) else target.message

    if not card:
        await msg_target.answer(
            "😔 Serial topilmadi.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    movie_repo = MovieRepository(session)
    await movie_repo.increment_views(movie_id)

    episodes = card.get("episodes", [])
    kb = serial_card_keyboard(
        movie_id=movie_id,
        episodes=episodes,
        selected_season=season_number,
        is_favorite=card["is_favorite"],
        user_rating=card["user_rating"],
        bot_username=settings.bot_username,
        page=page,
    )

    if card["poster_file_id"]:
        try:
            await msg_target.answer_photo(
                photo=card["poster_file_id"],
                caption=card["caption"],
                reply_markup=kb,
                parse_mode="Markdown",
            )
        except TelegramBadRequest:
            await msg_target.answer(card["caption"], reply_markup=kb, parse_mode="Markdown")
    else:
        await msg_target.answer(card["caption"], reply_markup=kb, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# serial: — paginated list callbacks
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("serial:latest:") | F.data.startswith("serial:top:"))
async def cb_serial_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """
    Handle pagination for serial lists.

    Callback formats:
      serial:latest:<page>
      serial:top:<page>
    """
    parts = callback.data.split(":")
    prefix = parts[1]
    page = int(parts[2])
    per_page = settings.movies_per_page

    service = MovieService(session)
    await callback.answer()

    if prefix == "latest":
        movies, total = await service.repo.get_latest(
            page=page, per_page=per_page, content_type=SERIAL_CT
        )
        title = "\U0001f195 *YANGI SERIALLAR*"

    elif prefix == "top":
        movies, total = await service.repo.get_top_rated(
            page=page, per_page=per_page, content_type=SERIAL_CT
        )
        title = "\U0001f525 *TOP SERIALLAR*"

    else:
        return

    total_pages = max(1, math.ceil(total / per_page))

    if not movies:
        try:
            await callback.message.edit_text(
                "\U0001f4ed Hozircha serial yo'q.",
                reply_markup=serial_catalog_keyboard(),
            )
        except TelegramBadRequest:
            pass
        return

    serial_dicts = [_serial_dict(m) for m in movies]

    try:
        await callback.message.edit_text(
            f"{title}\n\n_{total}_ ta serial",
            reply_markup=movie_list_keyboard(serial_dicts, page, total_pages, f"serial:{prefix}"),
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# Episode interaction callbacks
# ---------------------------------------------------------------------------


@router.callback_query(F.data.startswith("serial:season:"))
async def cb_serial_season(callback: CallbackQuery, session: AsyncSession) -> None:
    """Switch active season in serial episode list."""
    parts = callback.data.split(":")
    movie_id = int(parts[2])
    season = int(parts[3])
    user_id = callback.from_user.id if callback.from_user else None

    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=user_id)
    if not card:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return

    kb = serial_card_keyboard(
        movie_id=movie_id,
        episodes=card.get("episodes", []),
        selected_season=season,
        is_favorite=card["is_favorite"],
        user_rating=card["user_rating"],
        bot_username=settings.bot_username,
        page=1,
    )
    await callback.answer(f"{season}-fasl tanlandi")
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("serial:page:"))
async def cb_serial_page(callback: CallbackQuery, session: AsyncSession) -> None:
    """Paginate episodes inside a season."""
    parts = callback.data.split(":")
    movie_id = int(parts[2])
    season = int(parts[3])
    page = int(parts[4])
    user_id = callback.from_user.id if callback.from_user else None

    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=user_id)
    if not card:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return

    kb = serial_card_keyboard(
        movie_id=movie_id,
        episodes=card.get("episodes", []),
        selected_season=season,
        is_favorite=card["is_favorite"],
        user_rating=card["user_rating"],
        bot_username=settings.bot_username,
        page=page,
    )
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("serial:menu:"))
async def cb_serial_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    """Show episode selection menu for a serial."""
    parts = callback.data.split(":")
    movie_id = int(parts[2])
    season = int(parts[3])
    user_id = callback.from_user.id if callback.from_user else None

    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=user_id)
    if not card:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return

    kb = serial_card_keyboard(
        movie_id=movie_id,
        episodes=card.get("episodes", []),
        selected_season=season,
        is_favorite=card["is_favorite"],
        user_rating=card["user_rating"],
        bot_username=settings.bot_username,
        page=1,
    )
    await callback.answer()
    await callback.message.answer(
        f"📋 *{card['movie'].title}* ({season}-fasl)\n\nKerakli qismni tanlang 👇",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("serial:ep:"))
async def cb_serial_episode(callback: CallbackQuery, session: AsyncSession) -> None:
    """Deliver the requested episode video with prev/next navigation."""
    parts = callback.data.split(":")
    movie_id = int(parts[2])
    season = int(parts[3])
    ep_num = int(parts[4])

    movie_repo = MovieRepository(session)
    movie = await movie_repo.get_by_id_published(movie_id)
    if not movie:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return

    episode = await movie_repo.get_episode(movie_id, season, ep_num)
    if not episode:
        await callback.answer(f"😔 {ep_num}-qism hali yuklanmagan.", show_alert=True)
        return

    # Increment views
    await movie_repo.increment_episode_views(episode.id)
    await movie_repo.increment_views(movie_id)

    # Check prev and next episodes for navigation buttons
    prev_ep = await movie_repo.get_episode(movie_id, season, ep_num - 1)
    next_ep = await movie_repo.get_episode(movie_id, season, ep_num + 1)

    user_id = callback.from_user.id if callback.from_user else None
    fav_repo = FavoriteRepository(session)
    is_fav = await fav_repo.is_favorite(user_id, movie_id) if user_id else False

    # Check sponsor ads
    setting_repo = SettingRepository(session)
    s_settings = await setting_repo.bulk_get([
        "sponsor_ad_enabled",
        "sponsor_ad_text",
        "sponsor_ad_button_text",
        "sponsor_ad_button_url",
    ])
    sp_enabled = s_settings.get("sponsor_ad_enabled") == "true"
    sp_text = s_settings.get("sponsor_ad_text", "").strip() if sp_enabled else ""
    sp_btn_text = s_settings.get("sponsor_ad_button_text", "").strip() if sp_enabled else None
    sp_btn_url = s_settings.get("sponsor_ad_button_url", "").strip() if sp_enabled else None

    video_kb = episode_video_keyboard(
        movie_id=movie_id,
        season_number=season,
        current_episode=ep_num,
        has_prev=prev_ep is not None,
        has_next=next_ep is not None,
        is_favorite=is_fav,
        sponsor_button_text=sp_btn_text,
        sponsor_button_url=sp_btn_url,
    )

    await callback.answer(f"📺 {ep_num}-qism yuborilmoqda...")

    caption_lines = [f"📺 *{movie.title}* | {season}-Fasl, {ep_num}-qism"]
    if episode.title and episode.title != f"{ep_num}-qism":
        caption_lines.append(f"_{episode.title}_")
    if episode.quality:
        caption_lines.append(f"Sifat: *{episode.quality}*")
    if sp_text:
        caption_lines.append(f"\n{sp_text}")

    caption = "\n".join(caption_lines)

    try:
        await callback.message.answer_video(
            video=episode.telegram_file_id,
            caption=caption,
            reply_markup=video_kb,
            parse_mode="Markdown",
        )
    except TelegramBadRequest as e:
        log.warning("send_episode_video_failed", error=str(e), file_id=episode.telegram_file_id)
        await callback.message.answer(
            f"😕 {ep_num}-qism videosini yuklashda xatolik yuz berdi.\n\nFile ID tekshirilishi kerak.",
            reply_markup=video_kb,
        )


def _serial_dict(m) -> dict:
    """Build the dict that movie_list_keyboard expects, adding serial info."""
    seasons_str = f" • {m.total_seasons} mavsum" if m.total_seasons else ""
    episodes_str = f" • {m.total_episodes} qism" if m.total_episodes else ""
    suffix = seasons_str or episodes_str
    title = f"{m.title}{suffix}"
    return {"id": m.id, "title": title, "year": m.year}
