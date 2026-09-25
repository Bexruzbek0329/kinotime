"""Inline keyboard builders for the Kinolar olami bot."""
import math
from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------------------------------------------------------------------------
# Emoji helpers
# ---------------------------------------------------------------------------

QUALITY_EMOJIS: dict[str, str] = {
    "360p": "\U0001f4fd",
    "480p": "\U0001f3a5",
    "720p": "\U0001f4fa",
    "1080p": "\U0001f4fd",
    "4K": "\U0001f31f",
}

# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------


def movie_card_keyboard(
    movie_id: int,
    qualities: List[str],
    is_favorite: bool,
    user_rating: Optional[int],
    bot_username: str,
) -> InlineKeyboardMarkup:
    """
    Build the full inline keyboard shown beneath a movie card.

    Rows (top to bottom):
      1+. Quality buttons — up to 3 per row
      N.  Favorite toggle
      N+1 Rating overview + Share
      N+2 Back
    """
    builder = InlineKeyboardBuilder()

    DEFAULT_QUALITY_ICON = "\U0001f3a5"
    # Quality buttons — max 3 per row
    for i in range(0, len(qualities), 3):
        row_qualities = qualities[i : i + 3]
        builder.row(
            *[
                InlineKeyboardButton(
                    text=f"{QUALITY_EMOJIS.get(q, DEFAULT_QUALITY_ICON)} {q}",
                    callback_data=f"movie:quality:{movie_id}:{q}",
                )
                for q in row_qualities
            ]
        )

    # Favourite toggle
    fav_text = (
        "\u2764\ufe0f Sevimlilardan olib tashlash"
        if is_favorite
        else "\u2764\ufe0f Sevimlilarga"
    )
    builder.row(
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"movie:favorite:{movie_id}",
        )
    )

    # Rating only (share removed)
    star_count = user_rating or 0
    stars = "\u2b50" * star_count + "\u2606" * (5 - star_count)
    builder.row(
        InlineKeyboardButton(
            text=f"{stars} Reyting",
            callback_data=f"movie:rate_menu:{movie_id}",
        ),
    )

    # Back
    builder.row(
        InlineKeyboardButton(
            text="\u2b05\ufe0f Orqaga",
            callback_data="nav:back",
        )
    )

    return builder.as_markup()


def single_video_keyboard(
    movie_id: int,
    is_favorite: bool,
    user_rating: Optional[int],
    bot_username: str = "",
    sponsor_button_text: Optional[str] = None,
    sponsor_button_url: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Build the inline keyboard shown beneath an auto-sent video
    when a movie/serial has only 1 quality.
    """
    builder = InlineKeyboardBuilder()

    # Sponsor ad button row
    if sponsor_button_text and sponsor_button_url:
        builder.row(
            InlineKeyboardButton(text=sponsor_button_text, url=sponsor_button_url)
        )

    fav_text = (
        "\u2764\ufe0f Sevimlilardan olib tashlash"
        if is_favorite
        else "\u2764\ufe0f Sevimlilarga"
    )
    builder.row(
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"movie:favorite:{movie_id}",
        )
    )

    star_count = user_rating or 0
    stars = "\u2b50" * star_count + "\u2606" * (5 - star_count)
    builder.row(
        InlineKeyboardButton(
            text=f"{stars} Reyting",
            callback_data=f"movie:rate_menu:{movie_id}",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="\u2b05\ufe0f Orqaga",
            callback_data="nav:back",
        )
    )

    return builder.as_markup()



def rating_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    """
    Build a 1–5 star rating keyboard for *movie_id*.

    First row: five star buttons (★ through ★★★★★).
    Second row: cancel button that navigates back to the movie card.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(
                text="\u2b50" * i,
                callback_data=f"movie:rate:{movie_id}:{i}",
            )
            for i in range(1, 6)
        ]
    )
    builder.row(
        InlineKeyboardButton(
            text="\u274c Bekor qilish",
            callback_data=f"movie:show:{movie_id}",
        )
    )
    return builder.as_markup()


def movie_list_keyboard(
    movies: List[dict],
    page: int,
    total_pages: int,
    prefix: str,
) -> InlineKeyboardMarkup:
    """
    Build a paginated movie-list keyboard.

    Each movie gets its own row.  Navigation buttons are appended at the
    bottom: ◀ current/total ▶.  A ``prefix`` string is embedded in the
    pagination callback data so the handler knows which list to reload
    (e.g. ``"latest"``, ``"top"``, ``"search:<query>"``).
    """
    builder = InlineKeyboardBuilder()

    for m in movies:
        builder.row(
            InlineKeyboardButton(
                text=f"\U0001f3ac {m['title']} ({m.get('year', '')})",
                callback_data=f"movie:show:{m['id']}",
            )
        )

    nav: List[InlineKeyboardButton] = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="\u2b05\ufe0f",
                callback_data=f"list:{prefix}:{page - 1}",
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop",
        )
    )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text="\u27a1\ufe0f",
                callback_data=f"list:{prefix}:{page + 1}",
            )
        )
    if nav:
        builder.row(*nav)

    return builder.as_markup()


def clean_channel_url(username: str) -> str:
    raw = str(username).strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    clean = raw.removeprefix("t.me/").lstrip("@")
    return f"https://t.me/{clean}"


def subscription_keyboard(
    channels: List[dict],
    bot_username: str = "",
) -> InlineKeyboardMarkup:
    """
    Build the mandatory-subscription keyboard.

    One URL button per channel, plus a verification button at the bottom.
    """
    builder = InlineKeyboardBuilder()
    for ch in channels:
        title = ch.get("title") or "Kanalimiz"
        raw_u = ch.get("username") or ""
        url = clean_channel_url(raw_u)
        builder.row(
            InlineKeyboardButton(
                text=f"\U0001f4e2 {title}",
                url=url,
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="\u2705 Obunani tekshirish",
            callback_data="check:subscription",
        )
    )
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Single-button keyboard that navigates back to the main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2b05\ufe0f Bosh menyu",
                    callback_data="nav:main",
                )
            ]
        ]
    )


def catalog_keyboard() -> InlineKeyboardMarkup:
    """Two-button keyboard for the catalog entry point."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="\U0001f525 Premyeralar",
            callback_data="list:latest:1",
        ),
        InlineKeyboardButton(
            text="\u2b50 Top kinolar",
            callback_data="list:top:1",
        ),
    )
    return builder.as_markup()


def serial_catalog_keyboard() -> InlineKeyboardMarkup:
    """Two-button keyboard for the serial catalog entry point."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="\U0001f195 Yangi Seriallar",
            callback_data="serial:latest:1",
        ),
        InlineKeyboardButton(
            text="\U0001f525 Top Seriallar",
            callback_data="serial:top:1",
        ),
    )
    return builder.as_markup()


def favorites_keyboard(
    movies: List[dict],
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """
    Build a paginated favorites list keyboard.

    Structurally identical to :func:`movie_list_keyboard` but uses
    heart-prefixed labels and ``fav:page:<n>`` pagination callbacks.
    """
    builder = InlineKeyboardBuilder()

    for m in movies:
        builder.row(
            InlineKeyboardButton(
                text=f"\u2764\ufe0f {m['title']}",
                callback_data=f"movie:show:{m['id']}",
            )
        )

    nav: List[InlineKeyboardButton] = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="\u2b05\ufe0f",
                callback_data=f"fav:page:{page - 1}",
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="noop",
        )
    )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton(
                text="\u27a1\ufe0f",
                callback_data=f"fav:page:{page + 1}",
            )
        )
    if nav:
        builder.row(*nav)

    builder.row(
        InlineKeyboardButton(
            text="\u2b05\ufe0f Orqaga",
            callback_data="nav:profile",
        )
    )
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    """Profile page keyboard — currently exposes the favorites list entry."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\u2764\ufe0f Sevimlilar",
                    callback_data="fav:page:1",
                )
            ]
        ]
    )


def serial_card_keyboard(
    movie_id: int,
    episodes: List[dict],
    selected_season: int = 1,
    is_favorite: bool = False,
    user_rating: Optional[int] = None,
    bot_username: str = "",
    page: int = 1,
    per_page: int = 15,
) -> InlineKeyboardMarkup:
    """
    Build interactive episode selection keyboard for a serial:
      - Season tabs if > 1 season
      - Grid of episode buttons (5 per row)
      - Pagination if > per_page episodes
      - Favorite, Rating, Share, and Back buttons
    """
    builder = InlineKeyboardBuilder()

    # Find distinct seasons
    all_seasons = sorted(list({ep.get("season_number", 1) for ep in episodes}))
    if not all_seasons:
        all_seasons = [1]

    # If serial has multiple seasons, show Season switch row
    if len(all_seasons) > 1:
        season_btns = []
        for s in all_seasons:
            prefix = "🔘 " if s == selected_season else ""
            season_btns.append(
                InlineKeyboardButton(
                    text=f"{prefix}{s}-Fasl",
                    callback_data=f"serial:season:{movie_id}:{s}",
                )
            )
        builder.row(*season_btns)

    # Episodes for this season
    season_eps = [
        ep for ep in episodes if ep.get("season_number", 1) == selected_season
    ]
    season_eps.sort(key=lambda x: x.get("episode_number", 0))

    if season_eps:
        total_eps = len(season_eps)
        total_pages = max(1, math.ceil(total_eps / per_page))
        current_page = min(max(1, page), total_pages)
        start_idx = (current_page - 1) * per_page
        paged_eps = season_eps[start_idx : start_idx + per_page]

        # 5 episodes per row
        for i in range(0, len(paged_eps), 5):
            chunk = paged_eps[i : i + 5]
            row_btns = [
                InlineKeyboardButton(
                    text=f"{ep['episode_number']}-qism",
                    callback_data=f"serial:ep:{movie_id}:{selected_season}:{ep['episode_number']}",
                )
                for ep in chunk
            ]
            builder.row(*row_btns)

        # Pagination controls
        if total_pages > 1:
            nav = []
            if current_page > 1:
                nav.append(
                    InlineKeyboardButton(
                        text="⬅️ Oldingi",
                        callback_data=f"serial:page:{movie_id}:{selected_season}:{current_page - 1}",
                    )
                )
            nav.append(
                InlineKeyboardButton(
                    text=f"{current_page}/{total_pages}",
                    callback_data="noop",
                )
            )
            if current_page < total_pages:
                nav.append(
                    InlineKeyboardButton(
                        text="Keyingi ➡️",
                        callback_data=f"serial:page:{movie_id}:{selected_season}:{current_page + 1}",
                    )
                )
            builder.row(*nav)

    # Favorite button
    fav_text = (
        "❤️ Sevimlilardan olib tashlash"
        if is_favorite
        else "❤️ Sevimlilarga"
    )
    builder.row(
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"movie:favorite:{movie_id}",
        )
    )

    # Rating + Share
    star_count = user_rating or 0
    stars = "⭐" * star_count + "☆" * (5 - star_count)
    builder.row(
        InlineKeyboardButton(
            text=f"{stars} Reyting",
            callback_data=f"movie:rate_menu:{movie_id}",
        ),
        InlineKeyboardButton(
            text="📤 Ulashish",
            callback_data=f"movie:share:{movie_id}",
        ),
    )

    # Back to main
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="nav:back",
        )
    )

    return builder.as_markup()


def episode_video_keyboard(
    movie_id: int,
    season_number: int,
    current_episode: int,
    has_prev: bool = False,
    has_next: bool = False,
    is_favorite: bool = False,
    sponsor_button_text: Optional[str] = None,
    sponsor_button_url: Optional[str] = None,
) -> InlineKeyboardMarkup:
    """
    Build direct navigation keyboard attached under an episode video:
      - [ Sponsor button if configured ]
      - [ ⬅️ Oldingi qism ] [ Keyingi qism ➡️ ]
      - [ 📋 Barcha qismlar ] [ ❤️ Sevimlilarga ]
      - [ 🏠 Bosh menyu ]
    """
    builder = InlineKeyboardBuilder()

    # Sponsor ad button row
    if sponsor_button_text and sponsor_button_url:
        builder.row(
            InlineKeyboardButton(text=sponsor_button_text, url=sponsor_button_url)
        )

    # Prev / Next episode row
    nav_btns = []
    if has_prev:
        nav_btns.append(
            InlineKeyboardButton(
                text=f"⬅️ {current_episode - 1}-qism",
                callback_data=f"serial:ep:{movie_id}:{season_number}:{current_episode - 1}",
            )
        )
    if has_next:
        nav_btns.append(
            InlineKeyboardButton(
                text=f"{current_episode + 1}-qism ➡️",
                callback_data=f"serial:ep:{movie_id}:{season_number}:{current_episode + 1}",
            )
        )
    if nav_btns:
        builder.row(*nav_btns)

    # Episode list + Favorite
    fav_text = "❤️ Sevimlilarda" if is_favorite else "❤️ Sevimlilarga"
    builder.row(
        InlineKeyboardButton(
            text="📋 Barcha qismlar",
            callback_data=f"serial:menu:{movie_id}:{season_number}",
        ),
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"movie:favorite:{movie_id}",
        ),
    )

    # Main menu
    builder.row(
        InlineKeyboardButton(
            text="🏠 Bosh menyu",
            callback_data="nav:main",
        )
    )

    return builder.as_markup()
