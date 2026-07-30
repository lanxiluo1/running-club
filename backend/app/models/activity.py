from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="活动标题")
    activity_time = Column(DateTime, nullable=False, comment="活动时间")
    location = Column(String(200), comment="集合地点")
    content = Column(Text, comment="训练内容")
    creator_id = Column(Integer, ForeignKey("users.id"), comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="发布时间")

    # 关联关系
    creator = relationship("User")
    signs = relationship("ActivitySign", back_populates="activity")


class ActivitySign(Base):
    __tablename__ = "activity_signs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, comment="活动ID")
    signed_at = Column(DateTime, default=datetime.utcnow, comment="报名时间")

    # 关联关系
    user = relationship("User", back_populates="activity_signs")
    activity = relationship("Activity", back_populates="signs")
