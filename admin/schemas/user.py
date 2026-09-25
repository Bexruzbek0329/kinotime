from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_blocked: bool
    is_admin: bool
    joined_at: datetime
    last_activity: datetime


class PaginatedUsers(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    per_page: int
    total_pages: int
