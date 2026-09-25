from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, func, desc, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.search import Search
from .base import BaseRepository


class SearchRepository(BaseRepository[Search]):
    def __init__(self, session: AsyncSession):
        super().__init__(Search, session)

    async def log_search(
        self, query: str, results_count: int, user_id: Optional[int] = None
    ) -> Search:
        return await self.create(
            query=query, results_count=results_count, user_id=user_id
        )

    async def get_not_found_searches(self, limit: int = 50) -> List[dict]:
        """Return queries that returned zero results, ranked by frequency."""
        result = await self.session.execute(
            select(Search.query, func.count(Search.id).label("cnt"))
            .where(Search.results_count == 0)
            .group_by(Search.query)
            .order_by(desc("cnt"))
            .limit(limit)
        )
        return [{"query": row[0], "count": row[1]} for row in result.all()]

    async def get_popular_searches(self, limit: int = 10) -> List[dict]:
        """Return the most frequently searched queries."""
        result = await self.session.execute(
            select(Search.query, func.count(Search.id).label("cnt"))
            .group_by(Search.query)
            .order_by(desc("cnt"))
            .limit(limit)
        )
        return [{"query": row[0], "count": row[1]} for row in result.all()]

    async def get_today_count(self) -> int:
        today = datetime.now(timezone.utc).date()
        result = await self.session.execute(
            select(func.count(Search.id)).where(
                cast(Search.created_at, Date) == today
            )
        )
        return result.scalar_one()
