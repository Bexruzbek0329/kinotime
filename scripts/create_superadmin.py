#!/usr/bin/env python3
"""
Create the first superadmin account.
Run: python scripts/create_superadmin.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import AsyncSessionLocal, engine
from database.models.base import Base
from database.models.admin import Admin, AdminRole
from sqlalchemy import select
import bcrypt


def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


async def create_superadmin(username: str, password: str) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin).where(Admin.username == username))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[!] Admin '{username}' already exists.")
            return

        admin = Admin(
            username=username,
            password_hash=hash_password(password),
            role=AdminRole.superadmin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"[✓] Superadmin '{username}' created successfully!")
        print(f"    Login at: http://localhost:3000/login")


if __name__ == "__main__":
    import getpass

    print("=== KinoBot Superadmin Creator ===")
    if len(sys.argv) >= 3:
        username = sys.argv[1].strip()
        password = sys.argv[2].strip()
    elif len(sys.argv) == 2:
        username = sys.argv[1].strip()
        try:
            password = getpass.getpass("Password: ")
        except Exception:
            password = "admin123"
    else:
        try:
            username = input("Username (default: admin): ").strip() or "admin"
            password = getpass.getpass("Password (default: admin123): ")
        except Exception:
            username = "admin"
            password = "admin123"

    if not password:
        password = "admin123"
        print(f"[!] Using default password: {password} — CHANGE THIS IN PRODUCTION!")

    asyncio.run(create_superadmin(username, password))
