from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ActivityCreate(BaseModel):
    title: str
    activity_time: datetime
    location: Optional[str] = None
    content: Optional[str] = None


class ActivityResponse(BaseModel):
    id: int
    title: str
    activity_time: datetime
    location: Optional[str]
    content: Optional[str]
    creator_id: Optional[int]
    created_at: datetime
    sign_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ActivitySignResponse(BaseModel):
    id: int
    user_id: int
    activity_id: int
    signed_at: datetime

    class Config:
        from_attributes = True
