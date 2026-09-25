"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.engine import get_db
from database.models.admin import Admin
from admin.schemas.auth import LoginRequest, TokenResponse, AdminCreate
from admin.services.auth_service import authenticate_admin, hash_password, create_access_token
from admin.api.middlewares.auth import get_current_admin, require_superadmin

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_db)):
    admin = await authenticate_admin(body.username, body.password, session)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token({"sub": str(admin.id), "role": admin.role})
    return TokenResponse(
        access_token=token,
        admin_id=admin.id,
        username=admin.username,
        role=admin.role,
    )


@router.get("/me")
async def get_me(admin: Admin = Depends(get_current_admin)):
    return {"id": admin.id, "username": admin.username, "role": admin.role}


@router.post("/admins", dependencies=[Depends(require_superadmin)])
async def create_admin(body: AdminCreate, session: AsyncSession = Depends(get_db)):
    existing = await session.execute(
        select(Admin).where(Admin.username == body.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    admin = Admin(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
        telegram_id=body.telegram_id,
    )
    session.add(admin)
    await session.commit()
    return {"id": admin.id, "username": admin.username, "role": admin.role}
