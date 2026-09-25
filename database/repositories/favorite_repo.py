from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.favorite import Favorite
from database.models.movie import Movie, MovieStatus
from .base import BaseRepository


class FavoriteRepository(BaseRepository[Favorite]):
    def __init__(self, session: AsyncSession):
        super().__init__(Favorite, session)

    async def toggle(self, user_id: int, movie_id: int) -> bool:
        """Add or remove a favorite. Returns True if added, False if removed."""
        existing = await self.session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.movie_id == movie_id
            )
        )
        fav = existing.scalar_one_or_none()
        if fav:
            await self.session.delete(fav)
            await self.session.flush()
            return False  # removed
        fav = Favorite(user_id=user_id, movie_id=movie_id)
        self.session.add(fav)
        await self.session.flush()
        return True  # added

    async def is_favorite(self, user_id: int, movie_id: int) -> bool:
        result = await self.session.execute(
            select(func.count(Favorite.id)).where(
                Favorite.user_id == user_id, Favorite.movie_id == movie_id
            )
        )
        return result.scalar_one() > 0

    async def get_by_user(
        self, user_id: int, page: int = 1, per_page: int = 5
    ) -> Tuple[List[Movie], int]:
        count_result = await self.session.execute(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        )
        total = count_result.scalar_one()
        result = await self.session.execute(
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .where(
                Favorite.user_id == user_id,
                Movie.status == MovieStatus.published,
            )
            .options(selectinload(Movie.videos), selectinload(Movie.genres))
            .order_by(Favorite.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all()), total
