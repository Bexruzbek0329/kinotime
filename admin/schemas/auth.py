from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: int
    username: str
    role: str


class AdminCreate(BaseModel):
    username: str
    password: str
    role: str = "admin"
    telegram_id: Optional[int] = None
