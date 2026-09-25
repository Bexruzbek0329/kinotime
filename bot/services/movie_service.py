"""High-level movie operations used by handlers."""
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.favorite_repo import FavoriteRepository
from database.repositories.movie_repo import MovieRepository
from database.repositories.rating_repo import RatingRepository
from bot.utils.formatting import format_movie_card

# Canonical quality ordering — cheapest to best
QUALITY_ORDER: List[str] = ["360p", "480p", "720p", "1080p", "4K"]


class MovieService:
    """
    Facade over the movie, favourite, and rating repositories.

    All methods are coroutines and expect an active
    :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.movie_repo = MovieRepository(session)
        self.repo = self.movie_repo  # alias for convenience
        self.fav_repo = FavoriteRepository(session)
        self.rating_repo = RatingRepository(session)


    async def get_movie_card(
        self,
        movie_id: int,
        user_id: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Assemble all data needed to display a movie card.

        Returns a dict with the following keys, or *None* when the movie
        does not exist or is not published:

        .. code-block:: python

            {
                "movie":          <ORM Movie>,
                "qualities":      ["480p", "720p"],
                "video_map":      {"720p": "BAADBAADabc..."},
                "is_favorite":    True,
                "user_rating":    3,          # None when not rated
                "avg_rating":     4.2,
                "caption":        "...",       # Markdown string
                "genres":         ["Drama"],
                "poster_file_id": "AgADBAAD...",  # or empty string
            }
        """
        movie = await self.movie_repo.get_by_id_published(movie_id)
        if not movie:
            return None

        # Sort available qualities in canonical order
        qualities: List[str] = sorted(
            [v.quality.value for v in movie.videos],
            key=lambda q: QUALITY_ORDER.index(q) if q in QUALITY_ORDER else 99,
        )
        video_map: dict[str, str] = {
            v.quality.value: v.telegram_file_id for v in movie.videos
        }

        is_favorite = False
        user_rating: Optional[int] = None
        if user_id:
            is_favorite = await self.fav_repo.is_favorite(user_id, movie_id)
            user_rating = await self.rating_repo.get_user_rating(user_id, movie_id)

        avg_rating: float = await self.rating_repo.get_movie_avg_rating(movie_id)
        genres: List[str] = [g.name for g in movie.genres]

        caption = format_movie_card(
            movie={
                "title": movie.title,
                "original_title": movie.original_title,
                "imdb_rating": float(movie.imdb_rating) if movie.imdb_rating else None,
                "year": movie.year,
                "country": movie.country,
                "duration_minutes": movie.duration_minutes,
                "description": movie.description or "",
                "views_count": movie.views_count,
                "content_type": movie.content_type.value if hasattr(movie, "content_type") and movie.content_type else "movie",
                "total_seasons": getattr(movie, "total_seasons", None),
                "total_episodes": getattr(movie, "total_episodes", None),
            },
            genres=genres,
            avg_rating=avg_rating,
            show_quality_prompt=len(qualities) >= 2 if getattr(movie, "content_type", None) != "serial" else False,
        )

        episodes_list = [
            {
                "id": ep.id,
                "season_number": ep.season_number,
                "episode_number": ep.episode_number,
                "title": ep.title,
                "telegram_file_id": ep.telegram_file_id,
                "quality": ep.quality,
                "duration_seconds": ep.duration_seconds,
            }
            for ep in (movie.episodes or [])
        ]

        return {
            "movie": movie,
            "qualities": qualities,
            "video_map": video_map,
            "episodes": episodes_list,
            "is_favorite": is_favorite,
            "user_rating": user_rating,
            "avg_rating": avg_rating,
            "caption": caption,
            "genres": genres,
            "poster_file_id": movie.poster_file_id or "",
        }

    async def search_movies(
        self,
        query: str,
        page: int = 1,
        per_page: int = 5,
    ) -> Tuple[list, int]:
        """
        Full-text search delegated to the movie repository.

        Returns a ``(movies, total_count)`` tuple.
        """
        return await self.movie_repo.search(query, page=page, per_page=per_page)

    async def get_latest_movies(
        self,
        page: int = 1,
        per_page: int = 5,
    ) -> Tuple[list, int]:
        """Return the most recently published movies, paginated."""
        return await self.movie_repo.get_latest(page=page, per_page=per_page)

    async def get_top_movies(
        self,
        page: int = 1,
        per_page: int = 10,
    ) -> Tuple[list, int]:
        """Return movies ordered by IMDb rating descending, paginated."""
        return await self.movie_repo.get_top_rated(page=page, per_page=per_page)
