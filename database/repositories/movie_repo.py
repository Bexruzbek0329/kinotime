from typing import List, Optional, Tuple
from sqlalchemy import select, func, update, desc, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.movie import Movie, MovieStatus, ContentType
from database.models.episode import Episode
from database.models.rating import Rating
from .base import BaseRepository


class MovieRepository(BaseRepository[Movie]):
    def __init__(self, session: AsyncSession):
        super().__init__(Movie, session)

    async def get_by_code(self, code: str) -> Optional[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.code == code, Movie.status == MovieStatus.published)
            .options(
                selectinload(Movie.videos),
                selectinload(Movie.episodes),
                selectinload(Movie.genres),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_published(self, movie_id: int) -> Optional[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.id == movie_id, Movie.status == MovieStatus.published)
            .options(
                selectinload(Movie.videos),
                selectinload(Movie.episodes),
                selectinload(Movie.genres),
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self, query: str, page: int = 1, per_page: int = 5,
        content_type: Optional[ContentType] = None,
    ) -> Tuple[List[Movie], int]:
        q = f"%{query.lower()}%"
        filters = [
            Movie.status == MovieStatus.published,
            or_(
                func.lower(Movie.title).like(q),
                func.lower(Movie.original_title).like(q),
                Movie.code == query,
            ),
        ]
        if content_type:
            filters.append(Movie.content_type == content_type)
        stmt = (
            select(Movie)
            .where(*filters)
            .options(selectinload(Movie.videos), selectinload(Movie.genres))
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        result = await self.session.execute(
            stmt.order_by(Movie.views_count.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all()), total

    async def get_latest(
        self, page: int = 1, per_page: int = 5,
        content_type: Optional[ContentType] = None,
    ) -> Tuple[List[Movie], int]:
        filters = [Movie.status == MovieStatus.published]
        if content_type:
            filters.append(Movie.content_type == content_type)
        stmt = select(Movie).where(*filters)
        total_result = await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = total_result.scalar_one()
        result = await self.session.execute(
            stmt.order_by(Movie.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all()), total

    async def get_top_rated(
        self, page: int = 1, per_page: int = 10,
        content_type: Optional[ContentType] = None,
    ) -> Tuple[List[Movie], int]:
        avg_rating = func.coalesce(func.avg(Rating.score), 0).label("avg_rating")
        filters = [Movie.status == MovieStatus.published]
        if content_type:
            filters.append(Movie.content_type == content_type)
        stmt = (
            select(Movie, avg_rating)
            .outerjoin(Rating, Rating.movie_id == Movie.id)
            .where(*filters)
            .group_by(Movie.id)
            .order_by(desc(avg_rating), Movie.imdb_rating.desc())
        )
        count_stmt = select(func.count(Movie.id)).where(*filters)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        result = await self.session.execute(
            stmt.offset((page - 1) * per_page).limit(per_page)
        )
        movies = [row[0] for row in result.all()]
        return movies, total

    async def increment_views(self, movie_id: int) -> None:
        await self.session.execute(
            update(Movie)
            .where(Movie.id == movie_id)
            .values(views_count=Movie.views_count + 1)
        )

    async def get_avg_rating(self, movie_id: int) -> float:
        result = await self.session.execute(
            select(func.avg(Rating.score)).where(Rating.movie_id == movie_id)
        )
        val = result.scalar_one_or_none()
        return round(float(val), 1) if val else 0.0

    async def get_paginated_admin(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Tuple[List[Movie], int]:
        stmt = select(Movie)
        if search:
            q = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(func.lower(Movie.title).like(q), Movie.code == search)
            )
        if status:
            stmt = stmt.where(Movie.status == MovieStatus(status))
        if content_type:
            stmt = stmt.where(Movie.content_type == ContentType(content_type))
        total_result = await self.session.execute(
            select(func.count()).select_from(stmt.subquery())
        )
        total = total_result.scalar_one()
        result = await self.session.execute(
            stmt.order_by(Movie.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all()), total

    async def get_total_views(self) -> int:
        result = await self.session.execute(select(func.sum(Movie.views_count)))
        return result.scalar_one() or 0

    async def get_top_viewed(self, limit: int = 10) -> List[Movie]:
        result = await self.session.execute(
            select(Movie)
            .where(Movie.status == MovieStatus.published)
            .order_by(Movie.views_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Serial Episodes
    # ------------------------------------------------------------------

    async def get_episodes(
        self, movie_id: int, season_number: Optional[int] = None
    ) -> List[Episode]:
        stmt = select(Episode).where(Episode.movie_id == movie_id)
        if season_number is not None:
            stmt = stmt.where(Episode.season_number == season_number)
        stmt = stmt.order_by(Episode.season_number, Episode.episode_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_episode(
        self, movie_id: int, season_number: int, episode_number: int
    ) -> Optional[Episode]:
        result = await self.session.execute(
            select(Episode).where(
                Episode.movie_id == movie_id,
                Episode.season_number == season_number,
                Episode.episode_number == episode_number,
            )
        )
        return result.scalar_one_or_none()

    async def add_or_update_episode(
        self,
        movie_id: int,
        season_number: int,
        episode_number: int,
        telegram_file_id: str,
        quality: str = "720p",
        title: Optional[str] = None,
        duration_seconds: int = 0,
        file_size_bytes: int = 0,
    ) -> Episode:
        existing = await self.get_episode(movie_id, season_number, episode_number)
        if existing:
            existing.telegram_file_id = telegram_file_id
            existing.quality = quality
            if title is not None:
                existing.title = title
            if duration_seconds:
                existing.duration_seconds = duration_seconds
            if file_size_bytes:
                existing.file_size_bytes = file_size_bytes
            await self.session.flush()
            return existing

        ep = Episode(
            movie_id=movie_id,
            season_number=season_number,
            episode_number=episode_number,
            title=title or f"{episode_number}-qism",
            telegram_file_id=telegram_file_id,
            quality=quality,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes,
        )
        self.session.add(ep)
        await self.session.flush()

        # Update movie total_episodes count
        count_res = await self.session.execute(
            select(func.count(Episode.id)).where(Episode.movie_id == movie_id)
        )
        total_ep = count_res.scalar_one()
        await self.session.execute(
            update(Movie).where(Movie.id == movie_id).values(total_episodes=total_ep)
        )

        return ep

    async def delete_episode(self, movie_id: int, episode_id: int) -> bool:
        result = await self.session.execute(
            select(Episode).where(
                Episode.id == episode_id, Episode.movie_id == movie_id
            )
        )
        ep = result.scalar_one_or_none()
        if not ep:
            return False
        await self.session.delete(ep)
        await self.session.flush()

        # Update movie total_episodes count
        count_res = await self.session.execute(
            select(func.count(Episode.id)).where(Episode.movie_id == movie_id)
        )
        total_ep = count_res.scalar_one()
        await self.session.execute(
            update(Movie).where(Movie.id == movie_id).values(total_episodes=total_ep)
        )
        return True

    async def increment_episode_views(self, episode_id: int) -> None:
        await self.session.execute(
            update(Episode)
            .where(Episode.id == episode_id)
            .values(views_count=Episode.views_count + 1)
        )
