from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.rating import Rating
from .base import BaseRepository


class RatingRepository(BaseRepository[Rating]):
    def __init__(self, session: AsyncSession):
        super().__init__(Rating, session)

    async def upsert_rating(self, user_id: int, movie_id: int, score: int) -> Rating:
        """Insert or update a user's rating for a movie."""
        existing = await self.session.execute(
            select(Rating).where(
                Rating.user_id == user_id, Rating.movie_id == movie_id
            )
        )
        rating = existing.scalar_one_or_none()
        if rating:
            rating.score = score
            await self.session.flush()
            return rating
        rating = Rating(user_id=user_id, movie_id=movie_id, score=score)
        self.session.add(rating)
        await self.session.flush()
        return rating

    async def get_user_rating(self, user_id: int, movie_id: int) -> Optional[int]:
        result = await self.session.execute(
            select(Rating.score).where(
                Rating.user_id == user_id, Rating.movie_id == movie_id
            )
        )
        return result.scalar_one_or_none()

    async def get_movie_avg_rating(self, movie_id: int) -> float:
        result = await self.session.execute(
            select(func.avg(Rating.score)).where(Rating.movie_id == movie_id)
        )
        val = result.scalar_one_or_none()
        return round(float(val), 1) if val else 0.0
