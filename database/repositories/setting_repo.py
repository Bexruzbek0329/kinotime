from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.setting import Setting
from .base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    def __init__(self, session: AsyncSession):
        super().__init__(Setting, session)

    async def get(self, key: str) -> Optional[str]:
        result = await self.session.get(Setting, key)
        return result.value if result else None

    async def set(self, key: str, value: str, description: str = "") -> Setting:
        obj = await self.session.get(Setting, key)
        if obj:
            obj.value = value
            await self.session.flush()
            return obj
        obj = Setting(key=key, value=value, description=description)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_all(self) -> List[Setting]:
        result = await self.session.execute(select(Setting).order_by(Setting.key))
        return list(result.scalars().all())

    async def bulk_get(self, keys: List[str]) -> Dict[str, str]:
        result = await self.session.execute(
            select(Setting).where(Setting.key.in_(keys))
        )
        return {s.key: s.value for s in result.scalars().all()}
