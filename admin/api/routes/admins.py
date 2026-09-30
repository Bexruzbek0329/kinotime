"""Admin management routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from admin.api.middlewares.auth import get_current_admin, require_superadmin
from admin.services.auth_service import hash_password

router = APIRouter()


class AdminUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    telegram_id: Optional[int] = None


@router.get("")
async def list_admins(
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    result = await session.execute(select(Admin).order_by(Admin.created_at.desc()))
    admins = result.scalars().all()
    return [
        {
            "id": a.id,
            "username": a.username,
            "role": a.role,
            "telegram_id": a.telegram_id,
            "is_active": a.is_active,
            "last_login": a.last_login,
        }
        for a in admins
    ]


@router.put("/{admin_id}")
async def update_admin(
    admin_id: int,
    body: AdminUpdate,
    session: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    target = await session.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin topilmadi")
    if body.password:
        target.password_hash = hash_password(body.password)
    if body.role:
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.telegram_id is not None:
        target.telegram_id = body.telegram_id
    await session.commit()
    return {"ok": True}


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: int,
    session: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    target = await session.get(Admin, admin_id)
    if not target:
        raise HTTPException(status_code=404, detail="Admin topilmadi")
    if target.id == current_admin.id:
        raise HTTPException(status_code=400, detail="O'zingizni o'chira olmaysiz")

    # Clear audit_logs foreign key reference before deleting
    try:
        from database.models.audit_log import AuditLog
        from sqlalchemy import update
        await session.execute(
            update(AuditLog).where(AuditLog.admin_id == admin_id).values(admin_id=None)
        )
    except Exception:
        pass

    await session.delete(target)
    await session.commit()
    return {"ok": True}
