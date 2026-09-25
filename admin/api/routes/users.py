"""User management routes."""
import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from database.repositories.user_repo import UserRepository
from admin.api.middlewares.auth import get_current_admin

router = APIRouter()


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = UserRepository(session)
    users, total = await repo.get_all_paginated(page=page, per_page=per_page)
    return {
        "items": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "is_blocked": u.is_blocked,
                "joined_at": u.joined_at.isoformat(),
                "last_activity": u.last_activity.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, math.ceil(total / per_page)),
    }


@router.post("/{telegram_id}/block")
async def block_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = UserRepository(session)
    await repo.block(telegram_id)
    await session.commit()
    return {"ok": True}


@router.post("/{telegram_id}/unblock")
async def unblock_user(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    repo = UserRepository(session)
    await repo.unblock(telegram_id)
    await session.commit()
    return {"ok": True}
