"""
Movie card display, quality selection, favourite toggling,
rating submission, sharing, and list pagination callbacks.
"""
import math

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    back_to_menu_keyboard,
    movie_card_keyboard,
    movie_list_keyboard,
    rating_keyboard,
    single_video_keyboard,
)
from bot.services.movie_service import MovieService
from bot.utils.deep_link import make_movie_deep_link
from bot.utils.stickers import send_sticker
from config import settings
from database.models.movie import ContentType
from database.models.view import View
from database.repositories.favorite_repo import FavoriteRepository
from database.repositories.movie_repo import MovieRepository
from database.repositories.rating_repo import RatingRepository
from database.repositories.setting_repo import SettingRepository

router = Router(name="movie")
log = structlog.get_logger()


# ===========================================================================
# Helpers called by start.py and search.py (not callback-based)
# ===========================================================================


async def _send_poster_or_card(
    msg_target,
    poster_file_id: str | None,
    caption: str,
    reply_markup=None,
) -> None:
    """Send photo with caption (Markdown then plain fallback), or text message if no photo or photo fails."""
    if poster_file_id and str(poster_file_id).strip():
        clean_poster = str(poster_file_id).strip()
        try:
            await msg_target.answer_photo(
                photo=clean_poster,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return
        except TelegramBadRequest as e_photo_md:
            log.warning("send_photo_md_failed", error=str(e_photo_md))
            try:
                await msg_target.answer_photo(
                    photo=clean_poster,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=None,
                )
                return
            except TelegramBadRequest as e_photo_plain:
                log.warning("send_photo_plain_failed", error=str(e_photo_plain))

    # Send text fallback
    try:
        await msg_target.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    except TelegramBadRequest as e_text_md:
        log.warning("send_caption_md_failed", error=str(e_text_md))
        await msg_target.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode=None,
        )


async def _send_media_file(
    msg_target,
    file_id: str,
    caption: str,
    reply_markup=None,
) -> bool:
    """
    Deliver a video file reliably:
    1. Try answer_video with Markdown.
    2. If Markdown fails, try answer_video with plain text.
    3. If answer_video fails (e.g. file is a Document or invalid video type), try answer_document with Markdown.
    4. If Markdown fails on document, try answer_document with plain text.
    5. If all fail, display an explicit message to user so it never fails silently.
    """
    clean_file_id = str(file_id).strip() if file_id else ""
    if not clean_file_id:
        await msg_target.answer("❌ Video fayli topilmadi (file_id kiritilmagan).")
        return False

    # 1. Try sending as Video with Markdown
    try:
        await msg_target.answer_video(
            video=clean_file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        return True
    except TelegramBadRequest as e_vid_md:
        err_msg = str(e_vid_md).lower()
        log.warning("send_video_md_failed", error=str(e_vid_md), file_id=clean_file_id)

        # If entity parsing error, try video plain text
        if "entities" in err_msg or "parse" in err_msg:
            try:
                await msg_target.answer_video(
                    video=clean_file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=None,
                )
                return True
            except TelegramBadRequest as e_vid_plain:
                log.warning("send_video_plain_failed", error=str(e_vid_plain))
                err_msg = str(e_vid_plain).lower()

        # If video fails (e.g. Telegram says document type or other video constraint)
        # Try sending as document
        try:
            await msg_target.answer_document(
                document=clean_file_id,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return True
        except TelegramBadRequest as e_doc_md:
            err_doc = str(e_doc_md).lower()
            log.warning("send_document_md_failed", error=str(e_doc_md))
            if "entities" in err_doc or "parse" in err_doc:
                try:
                    await msg_target.answer_document(
                        document=clean_file_id,
                        caption=caption,
                        reply_markup=reply_markup,
                        parse_mode=None,
                    )
                    return True
                except Exception as e_doc_plain:
                    log.error("send_document_plain_failed", error=str(e_doc_plain))

            await msg_target.answer(
                f"❌ Videoni yuborib bo'lmadi.\nTelegram xatosi: {str(e_doc_md)}",
                reply_markup=back_to_menu_keyboard(),
            )
            return False
    except Exception as exc:
        log.error("send_media_file_unexpected", error=str(exc))
        await msg_target.answer(
            f"❌ Videoni yuborishda xatolik yuz berdi: {str(exc)}",
            reply_markup=back_to_menu_keyboard(),
        )
        return False


async def deliver_movie_content(
    target,  # Message or CallbackQuery
    session: AsyncSession,
    movie_id: int,
    user_id: int | None = None,
) -> None:
    """
    Deliver movie/serial content matching user requirement:
      - If serial: delegate to deliver_serial_content with episode picker.
      - If 1 quality: send poster + caption with NO inline buttons,
        then immediately send the video with action buttons (Favorite, Rating, Back).
      - If 2+ qualities: send poster + caption with quality buttons.
      - If 0 qualities: send poster + caption with action buttons.
    """
    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=user_id)
    msg_target = target if isinstance(target, Message) else target.message

    if not card:
        await msg_target.answer(
            "\U0001f614 Kino topilmadi.",
            reply_markup=back_to_menu_keyboard(),
        )
        return

    # If content is a serial, delegate to serial delivery with episode picker
    movie_obj = card["movie"]
    c_type = getattr(movie_obj, "content_type", None)
    c_val = c_type.value if hasattr(c_type, "value") else str(c_type or "")
    if c_val == "serial":
        from bot.handlers.serial import deliver_serial_content
        await deliver_serial_content(target, session, movie_id, user_id=user_id)
        return

    movie_repo = MovieRepository(session)
    await movie_repo.increment_views(movie_id)

    num_qualities = len(card["qualities"])
    movie_title = movie_obj.title

    if num_qualities == 1:
        single_q = card["qualities"][0]
        file_id = card["video_map"].get(single_q, "")

        # Log view in DB
        view = View(user_id=user_id, movie_id=movie_id, quality=single_q)
        session.add(view)

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

        video_kb = single_video_keyboard(
            movie_id=movie_id,
            is_favorite=card["is_favorite"],
            user_rating=card["user_rating"],
            bot_username=settings.bot_username,
            sponsor_button_text=sp_btn_text,
            sponsor_button_url=sp_btn_url,
        )

        vid_caption = f"\U0001f3ac *{movie_title}* • {single_q}"
        if sp_text:
            vid_caption += f"\n\n{sp_text}"

        if card["poster_file_id"]:
            # Admin rasm qo'shgan bo'lsa:
            # 1. Rasm va tavsif pastda tugmalarsiz chiqadi
            await _send_poster_or_card(
                msg_target=msg_target,
                poster_file_id=card["poster_file_id"],
                caption=card["caption"],
                reply_markup=None,
            )
            # 2. Keyin pastda video tashalsin tugmalari bilan
            await _send_media_file(
                msg_target=msg_target,
                file_id=file_id,
                caption=vid_caption,
                reply_markup=video_kb,
            )
        else:
            # Admin rasm QO'SHMAGAN bo'lsa:
            # Video va buttonlar describe (tavsif) bilan birga yagona xabarda chiqadi!
            full_caption = card["caption"]
            if sp_text:
                full_caption += f"\n\n{sp_text}"
            if len(full_caption) > 1024:
                full_caption = full_caption[:1020] + "..."

            await _send_media_file(
                msg_target=msg_target,
                file_id=file_id,
                caption=full_caption,
                reply_markup=video_kb,
            )

    elif num_qualities >= 2:
        # 2 xil va undan ortiq sifatda bo'lsa: pastda alohida sifat tugmalari
        kb = movie_card_keyboard(
            movie_id=movie_id,
            qualities=card["qualities"],
            is_favorite=card["is_favorite"],
            user_rating=card["user_rating"],
            bot_username=settings.bot_username,
        )
        await _send_poster_or_card(
            msg_target=msg_target,
            poster_file_id=card["poster_file_id"],
            caption=card["caption"],
            reply_markup=kb,
        )

    else:
        # Video yuklanmagan bo'lsa
        kb = single_video_keyboard(
            movie_id=movie_id,
            is_favorite=card["is_favorite"],
            user_rating=card["user_rating"],
            bot_username=settings.bot_username,
        )
        await _send_poster_or_card(
            msg_target=msg_target,
            poster_file_id=card["poster_file_id"],
            caption=card["caption"],
            reply_markup=kb,
        )


async def send_movie_card(
    message: Message,
    session: AsyncSession,
    bot,
    movie_id: int,
    user_id: int | None = None,
) -> None:
    """Send sticker and deliver movie content to chat."""
    await send_sticker(bot, message.chat.id, "movie", session)
    await deliver_movie_content(message, session, movie_id, user_id=user_id)


async def send_movie_card_by_code(
    message: Message,
    session: AsyncSession,
    bot,
    code: str,
) -> None:
    """Look up a movie by its numeric code string and display the card."""
    movie_repo = MovieRepository(session)
    movie = await movie_repo.get_by_code(code)
    if not movie:
        await message.answer(
            "\U0001f614 Bunday kodli kino topilmadi.",
            reply_markup=back_to_menu_keyboard(),
        )
        return
    user_id = message.from_user.id if message.from_user else None
    await send_movie_card(message, session, bot, movie.id, user_id=user_id)


# ===========================================================================
# movie:show — open a movie from a list keyboard
# ===========================================================================


@router.callback_query(F.data.startswith("movie:show:"))
async def cb_movie_show(
    callback: CallbackQuery,
    session: AsyncSession,
    bot,
    db_user,
) -> None:
    """Display the movie card after the user selects a title from a list."""
    try:
        movie_id = int(callback.data.split(":")[2])
        user_id = db_user.id if db_user else None
        try:
            await callback.answer()
        except Exception:
            pass
        await deliver_movie_content(callback.message, session, movie_id, user_id=user_id)
    except Exception as exc:
        log.error("cb_movie_show_failed", error=str(exc), exc_info=True)
        try:
            await callback.message.answer(
                f"❌ Kinoni ochishda xatolik yuz berdi: {str(exc)}",
                reply_markup=back_to_menu_keyboard(),
            )
        except Exception:
            pass


# ===========================================================================
# movie:quality — send the video file
# ===========================================================================


@router.callback_query(F.data.startswith("movie:quality:"))
async def cb_movie_quality(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user,
) -> None:
    """Send the video file for the selected quality and log a view record."""
    try:
        parts = callback.data.split(":")
        movie_id = int(parts[2])
        quality = parts[3]

        movie_repo = MovieRepository(session)
        movie = await movie_repo.get_by_id_published(movie_id)
        if not movie:
            await callback.answer("\U0001f614 Kino topilmadi.", show_alert=True)
            return

        def _match_quality(v, q: str) -> bool:
            v_q = getattr(v, "quality", None)
            v_str = v_q.value if hasattr(v_q, "value") else str(v_q)
            return v_str == q

        video = next((v for v in movie.videos if _match_quality(v, quality)), None)
        if not video or not video.telegram_file_id:
            await callback.answer("\U0001f4fd Bu sifat mavjud emas.", show_alert=True)
            return

        # Persist view record
        view = View(
            user_id=db_user.id if db_user else None,
            movie_id=movie_id,
            quality=quality,
        )
        session.add(view)

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

        video_kb = single_video_keyboard(
            movie_id=movie_id,
            is_favorite=await FavoriteRepository(session).is_favorite(db_user.id, movie_id) if db_user else False,
            user_rating=await RatingRepository(session).get_user_rating(db_user.id, movie_id) if db_user else None,
            bot_username=settings.bot_username,
            sponsor_button_text=sp_btn_text,
            sponsor_button_url=sp_btn_url,
        )
        caption = f"\U0001f3ac *{movie.title}* • {quality}"
        if sp_text:
            caption += f"\n\n{sp_text}"

        try:
            await callback.answer(f"\U0001f3a5 {quality} yuborilmoqda...")
        except Exception:
            pass

        await _send_media_file(
            msg_target=callback.message,
            file_id=video.telegram_file_id,
            caption=caption,
            reply_markup=video_kb,
        )
        log.info("movie_viewed", movie_id=movie_id, quality=quality, user_id=db_user.id if db_user else None)
    except Exception as exc:
        log.error("cb_movie_quality_failed", error=str(exc), exc_info=True)
        try:
            await callback.message.answer(
                f"❌ Videoni yuklashda xatolik yuz berdi: {str(exc)}",
                reply_markup=back_to_menu_keyboard(),
            )
        except Exception:
            pass


# ===========================================================================
# movie:favorite — toggle favourite
# ===========================================================================


@router.callback_query(F.data.startswith("movie:favorite:"))
async def cb_movie_favorite(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user,
) -> None:
    """Add to or remove from the user's favourites list."""
    movie_id = int(callback.data.split(":")[2])
    if not db_user:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
        return

    fav_repo = FavoriteRepository(session)
    is_added: bool = await fav_repo.toggle(db_user.id, movie_id)

    if is_added:
        await callback.answer("\u2764\ufe0f Sevimlilarga qo\u2018shildi!", show_alert=False)
    else:
        await callback.answer("\U0001f494 Sevimlilardan olib tashlandi.", show_alert=False)

    # Refresh the keyboard to reflect the new favourite state
    movie_service = MovieService(session)
    card = await movie_service.get_movie_card(movie_id, user_id=db_user.id)
    if card:
        if len(card["qualities"]) <= 1:
            kb = single_video_keyboard(
                movie_id=movie_id,
                is_favorite=card["is_favorite"],
                user_rating=card["user_rating"],
                bot_username=settings.bot_username,
            )
        else:
            kb = movie_card_keyboard(
                movie_id=movie_id,
                qualities=card["qualities"],
                is_favorite=card["is_favorite"],
                user_rating=card["user_rating"],
                bot_username=settings.bot_username,
            )
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except TelegramBadRequest:
            pass


# ===========================================================================
# movie:rate_menu — open the rating keyboard
# ===========================================================================


@router.callback_query(F.data.startswith("movie:rate_menu:"))
async def cb_rate_menu(callback: CallbackQuery) -> None:
    """Display the 1–5 star rating keyboard as a separate message."""
    movie_id = int(callback.data.split(":")[2])
    await callback.answer()
    await callback.message.answer(
        "\u2b50 *Filmga baho bering:*",
        reply_markup=rating_keyboard(movie_id),
        parse_mode="Markdown",
    )


# ===========================================================================
# movie:rate — submit a rating
# ===========================================================================


@router.callback_query(F.data.startswith("movie:rate:"))
async def cb_movie_rate(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user,
) -> None:
    """Persist the user's star rating and remove the rating keyboard."""
    parts = callback.data.split(":")
    movie_id = int(parts[2])
    score = int(parts[3])

    if not db_user:
        await callback.answer("Xatolik.", show_alert=True)
        return

    rating_repo = RatingRepository(session)
    await rating_repo.upsert_rating(db_user.id, movie_id, score)

    stars = "\u2b50" * score
    await callback.answer(f"{stars} Bahoyingiz saqlandi!", show_alert=True)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    log.info("movie_rated", movie_id=movie_id, score=score, user_id=db_user.id)


# ===========================================================================
# movie:share — generate share link
# ===========================================================================


@router.callback_query(F.data.startswith("movie:share:"))
async def cb_movie_share(callback: CallbackQuery) -> None:
    """Generate and send a deep-link URL the user can forward to friends."""
    movie_id = int(callback.data.split(":")[2])
    link = make_movie_deep_link(settings.bot_username, movie_id)
    await callback.answer()
    await callback.message.answer(
        f"\U0001f4e4 *Do\u2018stlaringizga yuboring:*\n\n`{link}`",
        parse_mode="Markdown",
    )


# ===========================================================================
# list: — paginated list navigation
# ===========================================================================


@router.callback_query(F.data.startswith("list:"))
async def cb_movie_list(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """
    Handle pagination for latest, top, and search result lists.

    Callback data formats:
      ``list:latest:<page>``
      ``list:top:<page>``
      ``list:search:<encoded_query>:<page>``
    """
    parts = callback.data.split(":")
    prefix = parts[1]
    service = MovieService(session)
    per_page: int = settings.movies_per_page

    await callback.answer()

    if prefix == "latest":
        page = int(parts[2])
        movies, total = await service.get_latest_movies(page=page, per_page=per_page)
        title = "\U0001f525 *SO\u2018NGGI KINOLAR*"

    elif prefix == "top":
        page = int(parts[2])
        movies, total = await service.get_top_movies(page=page, per_page=per_page)
        title = "\u2b50 *TOP KINOLAR*"

    elif prefix == "search":
        # Format: list:search:<query_with_possible_colons>:<page>
        page = int(parts[-1])
        query = ":".join(parts[2:-1])
        movies, total = await service.search_movies(query, page=page, per_page=per_page)
        title = f"\U0001f50e *Qidiruv:* _{query}_"
        prefix = f"search:{query}"

    else:
        return

    total_pages = max(1, math.ceil(total / per_page))
    movie_dicts = [{"id": m.id, "title": m.title, "year": m.year} for m in movies]

    try:
        await callback.message.edit_text(
            f"{title}\n\n_{total}_ ta kino",
            reply_markup=movie_list_keyboard(movie_dicts, page, total_pages, prefix),
            parse_mode="Markdown",
        )
    except TelegramBadRequest:
        pass


# ===========================================================================
# Navigation utilities
# ===========================================================================


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    """Acknowledge pagination page indicator buttons silently."""
    await callback.answer()


@router.callback_query(F.data == "nav:back")
async def cb_nav_back(callback: CallbackQuery) -> None:
    """Delete the current message (acts as a visual 'back' action)."""
    await callback.answer()
    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "nav:main")
async def cb_nav_main(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Return the user to the main menu by sending the welcome message."""
    from bot.keyboards.reply import main_menu_keyboard

    repo = SettingRepository(session)
    msg = await repo.get("welcome_message") or "\U0001f3ac Bosh menyu"

    await callback.answer()
    await callback.message.answer(
        msg, reply_markup=main_menu_keyboard(), parse_mode="Markdown"
    )
