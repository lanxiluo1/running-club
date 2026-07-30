from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    student_id: str = Field(..., min_length=15, max_length=15, description="学号")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    academy: Optional[str] = Field(None, max_length=100, description="学院")
    grade: Optional[str] = Field(None, max_length=20, description="年级")


class UserLogin(BaseModel):
    student_id: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    academy: Optional[str] = None
    grade: Optional[str] = None
    group_type: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    student_id: str
    username: str
    academy: Optional[str]
    grade: Optional[str]
    role: str
    group_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
