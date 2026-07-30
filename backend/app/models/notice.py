from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="内容")
    publisher_id = Column(Integer, ForeignKey("users.id"), comment="发布人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="发布时间")

    # 关联关系
    publisher = relationship("User")
