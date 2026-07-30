from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class GroupType(str, enum.Enum):
    BEGINNER = "beginner"      # 新手组
    ADVANCED = "advanced"      # 进阶组


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(15), unique=True, index=True, nullable=False, comment="学号")
    username = Column(String(50), nullable=False, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    academy = Column(String(100), comment="学院")
    grade = Column(String(20), comment="年级")
    role = Column(String(20), default=UserRole.MEMBER.value, comment="角色: admin/member")
    group_type = Column(String(20), default=GroupType.BEGINNER.value, comment="分组: beginner/advanced")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联关系
    run_records = relationship("RunRecord", back_populates="user")
    activity_signs = relationship("ActivitySign", back_populates="user")
