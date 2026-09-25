"""Audit log routes."""
import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.engine import get_db
from database.models.admin import Admin
from database.models.audit_log import AuditLog
from admin.api.middlewares.auth import get_current_admin

router = APIRouter()


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    total_result = await session.execute(select(func.count(AuditLog.id)))
    total = total_result.scalar_one()

    result = await session.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": l.id,
                "admin_id": l.admin_id,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, math.ceil(total / per_page)),
    }
