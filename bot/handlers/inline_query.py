"""Telegram Inline Query handler for searching and sharing movies in any chat."""
import hashlib
import structlog
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent,
)
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.movie_service import MovieService
from bot.utils.deep_link import make_movie_deep_link
from config import settings

router = Router(name="inline_query")
log = structlog.get_logger()


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, session: AsyncSession) -> None:
    """
    Handle inline queries when users type @bot_username <title> in any chat.
    Renders rich interactive cards with deep link buttons to view inside the bot.
    """
    query = (inline_query.query or "").strip()
    if not query:
        # Default empty result with short cache
        await inline_query.answer([], cache_time=5, is_personal=True)
        return

    service = MovieService(session)
    movies, total = await service.search_movies(query, page=1, per_page=10)

    results = []
    for m in movies:
        item_id = hashlib.md5(f"inline_movie_{m.id}".encode()).hexdigest()
        year_str = f" ({m.year})" if m.year else ""
        imdb_str = f"⭐ IMDb: {m.imdb_rating}" if m.imdb_rating else "⭐ IMDb: N/A"

        deep_link = make_movie_deep_link(settings.bot_username, m.id)

        # Message body sent when the inline result is tapped
        lines = [
            f"🎬 *{m.title}*{year_str}",
            f"{imdb_str}",
        ]
        if m.country:
            lines.append(f"🌍 Davlat: {m.country}")
        if m.description:
            desc_snippet = m.description[:250].strip() + ("..." if len(m.description) > 250 else "")
            lines.append(f"\n_{desc_snippet}_")

        lines.append(f"\n👉 [Kinoni botda tomosha qilish]({deep_link})")

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="▶️ Kinoni tomosha qilish", url=deep_link)
        ]])

        results.append(
            InlineQueryResultArticle(
                id=item_id,
                title=f"🎬 {m.title}{year_str}",
                description=f"{imdb_str} • {m.country or ''}",
                input_message_content=InputTextMessageContent(
                    message_text="\n".join(lines),
                    parse_mode="Markdown",
                    disable_web_page_preview=False,
                ),
                reply_markup=kb,
            )
        )

    await inline_query.answer(results, cache_time=30, is_personal=False)
