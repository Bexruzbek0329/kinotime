"""Channel management routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from database.repositories.channel_repo import ChannelRepository
from admin.schemas.channel import ChannelCreate, ChannelUpdate, ChannelOut
from admin.api.middlewares.auth import get_current_admin

router = APIRouter()


@router.get("", response_model=List[ChannelOut])
async def list_channels(
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = ChannelRepository(session)
    return await repo.get_all()


@router.post("", response_model=ChannelOut)
async def create_channel(
    body: ChannelCreate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = ChannelRepository(session)
    existing = await repo.get_by_channel_id(body.channel_id)
    if existing:
        raise HTTPException(status_code=400, detail="Channel already exists")
    ch = await repo.create(
        channel_id=body.channel_id,
        username=body.username,
        title=body.title,
        is_active=body.is_active,
    )
    await session.commit()
    return ch


@router.put("/{channel_id}", response_model=ChannelOut)
async def update_channel(
    channel_id: int,
    body: ChannelUpdate,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = ChannelRepository(session)
    ch = await repo.get_by_id(channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    update_data = body.model_dump(exclude_none=True)
    ch = await repo.update(ch, **update_data)
    await session.commit()
    return ch


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = ChannelRepository(session)
    ch = await repo.get_by_id(channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.delete(ch)
    await session.commit()
    return {"ok": True}
