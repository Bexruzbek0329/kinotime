from datetime import datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy import select, func, update, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import User
from database.models.view import View
from database.models.rating import Rating
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        telegram_id: int,
        first_name: str,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """Return (user, created). created=True when a new row was inserted."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.first_name = first_name
            user.username = username
            user.last_name = last_name
            user.last_activity = datetime.now(timezone.utc)
            await self.session.flush()
            return user, False
        try:
            user = await self.create(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
                last_name=last_name,
                language_code=language_code,
            )
            return user, True
        except Exception:
            # Handle concurrent insert race condition gracefully
            existing = await self.get_by_telegram_id(telegram_id)
            if existing:
                existing.first_name = first_name
                existing.username = username
                existing.last_name = last_name
                existing.last_activity = datetime.now(timezone.utc)
                await self.session.flush()
                return existing, False
            raise


    async def block(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_blocked=True)
        )

    async def unblock(self, telegram_id: int) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(is_blocked=False)
        )

    async def get_broadcast_user_ids(self, active_days: Optional[int] = None) -> List[int]:
        stmt = select(User.telegram_id).where(User.is_blocked == False)
        if active_days:
            from datetime import timedelta
            threshold = datetime.now(timezone.utc) - timedelta(days=active_days)
            stmt = stmt.where(User.last_activity >= threshold)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_paginated(
        self, page: int = 1, per_page: int = 20
    ) -> Tuple[List[User], int]:
        total_result = await self.session.execute(select(func.count(User.id)))
        total = total_result.scalar_one()
        result = await self.session.execute(
            select(User)
            .order_by(User.joined_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(result.scalars().all()), total

    async def get_total_count(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def get_today_count(self) -> int:
        today = datetime.now(timezone.utc).date()
        result = await self.session.execute(
            select(func.count(User.id)).where(cast(User.joined_at, Date) == today)
        )
        return result.scalar_one()

    async def get_user_stats(self, user_id: int) -> dict:
        views_result = await self.session.execute(
            select(func.count(View.id)).where(View.user_id == user_id)
        )
        ratings_result = await self.session.execute(
            select(func.count(Rating.id)).where(Rating.user_id == user_id)
        )
        return {
            "views": views_result.scalar_one(),
            "ratings": ratings_result.scalar_one(),
        }
