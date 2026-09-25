from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.channel import Channel
from .base import BaseRepository


class ChannelRepository(BaseRepository[Channel]):
    def __init__(self, session: AsyncSession):
        super().__init__(Channel, session)

    async def get_all_active(self) -> List[Channel]:
        result = await self.session.execute(
            select(Channel).where(Channel.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_channel_id(self, channel_id: int) -> Optional[Channel]:
        result = await self.session.execute(
            select(Channel).where(Channel.channel_id == channel_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Channel]:
        result = await self.session.execute(
            select(Channel).order_by(Channel.created_at.desc())
        )
        return list(result.scalars().all())
