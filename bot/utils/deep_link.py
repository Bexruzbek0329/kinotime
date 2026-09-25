"""Parse and generate Telegram deep links for movie sharing."""
from typing import Optional


def parse_start_param(param: Optional[str]) -> Optional[dict]:
    """
    Decode a ``/start <param>`` payload produced by :func:`make_movie_deep_link`.

    Returns a dict like ``{"type": "movie", "id": 42}`` or *None* when the
    payload is absent or malformed.
    """
    if not param:
        return None
    if param.startswith("movie_"):
        try:
            movie_id = int(param.split("_", 1)[1])
            return {"type": "movie", "id": movie_id}
        except (IndexError, ValueError):
            return None
    return None


def make_movie_deep_link(bot_username: str, movie_id: int) -> str:
    """Return a ``t.me`` deep-link URL that opens the bot with a movie payload."""
    return f"https://t.me/{bot_username}?start=movie_{movie_id}"
