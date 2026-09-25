from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ChannelCreate(BaseModel):
    channel_id: int
    username: str
    title: str
    is_active: bool = True


class ChannelUpdate(BaseModel):
    username: Optional[str] = None
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: int
    username: str
    title: str
    is_active: bool
    created_at: datetime

