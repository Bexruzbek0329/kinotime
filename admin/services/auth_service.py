"""JWT auth service."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.admin import Admin
from config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24h


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.admin_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.admin_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def authenticate_admin(
    username: str, password: str, session: AsyncSession
) -> Optional[Admin]:
    result = await session.execute(
        select(Admin).where(Admin.username == username, Admin.is_active == True)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    admin.last_login = datetime.now(timezone.utc)
    await session.commit()
    return admin
