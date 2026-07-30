from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NoticeCreate(BaseModel):
    title: str
    content: str


class NoticeResponse(BaseModel):
    id: int
    title: str
    content: str
    publisher_id: Optional[int]
    created_at: datetime
    publisher_name: Optional[str] = None

    class Config:
        from_attributes = True
