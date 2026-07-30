from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class RunRecordCreate(BaseModel):
    run_date: date
    distance: float = Field(..., gt=0, le=100, description="距离(km)")
    duration: Optional[int] = Field(None, ge=0, description="时长(秒)")
    pace: Optional[float] = Field(None, ge=0, description="配速")
    heart_rate: Optional[int] = Field(None, ge=0, description="心率")
    training_type: Optional[str] = None
    screenshot_path: Optional[str] = None
    check_in_method: str = "manual"


class RunRecordResponse(BaseModel):
    id: int
    user_id: int
    run_date: date
    distance: float
    duration: Optional[int]
    pace: Optional[float]
    heart_rate: Optional[int]
    training_type: Optional[str]
    screenshot_path: Optional[str]
    check_in_method: str
    status: str
    created_at: datetime
    username: Optional[str] = None

    class Config:
        from_attributes = True


class RunRecordReview(BaseModel):
    status: str = Field(..., description="审核状态: approved/rejected")


class OCRResponse(BaseModel):
    distance: Optional[float] = None
    duration: Optional[int] = None
    heart_rate: Optional[int] = None
    date: Optional[str] = None
    success: bool
    message: str


class StatsResponse(BaseModel):
    total_distance: float
    total_runs: int
    avg_pace: Optional[float]
    avg_heart_rate: Optional[float]
    weekly_data: List[dict]
    monthly_data: List[dict]
