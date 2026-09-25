"""Message formatting helpers for the Kinolar olami bot."""
from typing import List, Optional


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def format_duration(minutes: Optional[int]) -> str:
    """Convert a duration in minutes to a human-readable Uzbek string."""
    if not minutes:
        return "N/A"
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} soat {m} daqiqa"
    if h:
        return f"{h} soat"
    return f"{m} daqiqa"


def format_number(n: int) -> str:
    """Format an integer with space thousands separators (e.g. 1 234 567)."""
    return f"{n:,}".replace(",", " ")


# ---------------------------------------------------------------------------
# Complex formatters
# ---------------------------------------------------------------------------


def format_movie_card(
    movie: dict,
    genres: List[str],
    avg_rating: float,
    show_quality_prompt: bool = True,
) -> str:
    """
    Render a full movie card as a Markdown string.

    Args:
        movie:      Flat dict of movie scalar fields.
        genres:     List of genre name strings.
        avg_rating: Bot-internal average rating (0.0 when no ratings yet).

    Returns:
        A Markdown-formatted string suitable for ``parse_mode="Markdown"``.
    """
    title = movie.get("title", "")
    original = movie.get("original_title", "")
    imdb = movie.get("imdb_rating")
    year = movie.get("year", "")
    country = movie.get("country", "")
    description = (movie.get("description") or "").strip()
    views = movie.get("views_count", 0)
    content_type = movie.get("content_type", "movie")
    total_seasons = movie.get("total_seasons")
    total_episodes = movie.get("total_episodes")
    is_serial = content_type == "serial"

    sep = "\u2015" * 16
    genre_str = " \u2022 ".join(genres) if genres else "N/A"
    imdb_str = f"{imdb}" if imdb else "N/A"
    avg_str = f"{avg_rating:.1f}" if avg_rating else "\u2014"

    # Icon and label based on content type
    type_icon = "\U0001f4fa" if is_serial else "\U0001f3ac"
    type_label = "Serial" if is_serial else "Kino"

    lines: List[str] = [
        sep,
        f"{type_icon} *{title}*",
    ]
    if original and original.lower() != title.lower():
        lines.append(f"_{original}_")
    lines += [
        sep,
        f"\u2b50 IMDb: *{imdb_str}* \u2022 \U0001f3a6 Bot: *{avg_str}*",
    ]

    # Duration or season/episode info depending on content type
    if is_serial:
        if total_seasons or total_episodes:
            seasons_str = f"{total_seasons} mavsum" if total_seasons else ""
            episodes_str = f"{total_episodes} qism" if total_episodes else ""
            info_parts = " • ".join(p for p in [seasons_str, episodes_str] if p)
            lines.append(f"\U0001f4c5 {year}   \U0001f30d {country}   \U0001f4fd {info_parts}")
        else:
            lines.append(f"\U0001f4c5 {year}   \U0001f30d {country}")
    else:
        duration = format_duration(movie.get("duration_minutes"))
        lines.append(f"\U0001f4c5 {year}   \U0001f30d {country}   \u23f1 {duration}")

    lines += [
        f"\U0001f3ad {genre_str}",
        sep,
    ]
    if description:
        desc = description[:300] + "..." if len(description) > 300 else description
        lines += [
            f"\U0001f4d6 *{type_label} haqida:*",
            desc,
            sep,
        ]
    lines += [
        f"\U0001f440 Ko\u2018rildi: *{format_number(views)}* marta",
    ]
    if is_serial:
        lines += [
            "",
            "📺 *Kerakli qismni tanlang* 👇",
        ]
    elif show_quality_prompt:
        lines += [
            "",
            "\U0001f3a5 *Sifatni tanlang* \U0001f447",
        ]
    return "\n".join(lines)



def format_search_results(query: str, movies: List[dict], total: int) -> str:
    """Header text shown above the search-results keyboard."""
    return (
        f"\U0001f50e *Qidiruv natijasi:* _{query}_\n"
        f"\U0001f4ca Topildi: *{total}* ta kino\n\n"
        "Kino tanlang \U0001f447"
    )


def format_not_found(query: str) -> str:
    """Message displayed when a search returns zero results."""
    return (
        f"\U0001f614 *Kino topilmadi.*\n\n"
        f"\U0001f50e Qidiruv: `{query}`\n\n"
        "Boshqa nom bilan qidirib ko\u2018ring."
    )


def format_profile(user: dict, stats: dict) -> str:
    """
    Render a user profile card.

    Args:
        user:  Dict with keys ``telegram_id`` and ``joined_at``.
        stats: Dict with keys ``views`` and ``ratings``.
    """
    joined = user.get("joined_at", "")
    if hasattr(joined, "strftime"):
        joined_str = joined.strftime("%d.%m.%Y")
    else:
        joined_str = str(joined)[:10]

    sep = "\u2015" * 16
    return (
        f"\U0001f464 *PROFIL*\n"
        f"{sep}\n"
        f"\U0001f194 ID: `{user.get('telegram_id', '')}`\n"
        f"\U0001f3ac Ko\u2018rgan kinolar: *{stats.get('views', 0)}*\n"
        f"\u2b50 Baholar: *{stats.get('ratings', 0)}*\n"
        f"\U0001f4c5 A\u2018zo bo\u2018lgan sana:\n"
        f"*{joined_str}*"
    )
