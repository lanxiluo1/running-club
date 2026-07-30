from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class CheckInStatus(str, enum.Enum):
    PENDING = "pending"        # 待审核
    APPROVED = "approved"      # 已通过
    REJECTED = "rejected"      # 已驳回


class CheckInMethod(str, enum.Enum):
    AUTO = "auto"              # 自动识别
    MANUAL = "manual"          # 手动填写


class RunRecord(Base):
    __tablename__ = "run_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    run_date = Column(Date, nullable=False, comment="跑步日期")
    distance = Column(Float, nullable=False, comment="距离(km)")
    duration = Column(Integer, comment="时长(秒)")
    pace = Column(Float, comment="配速(km/min)")
    heart_rate = Column(Integer, comment="心率")
    training_type = Column(String(50), comment="训练类型")
    screenshot_path = Column(String(500), comment="截图路径")
    check_in_method = Column(String(20), default=CheckInMethod.MANUAL.value, comment="打卡方式")
    status = Column(String(20), default=CheckInStatus.PENDING.value, comment="审核状态")
    created_at = Column(DateTime, default=datetime.utcnow, comment="提交时间")

    # 关联关系
    user = relationship("User", back_populates="run_records")
