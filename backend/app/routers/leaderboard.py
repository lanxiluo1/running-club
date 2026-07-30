from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.run_record import RunRecord
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/leaderboard", tags=["排行榜"])


def get_user_stats(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    """获取用户在指定时间范围内的跑步统计"""
    records = db.query(RunRecord).filter(
        RunRecord.user_id == user_id,
        RunRecord.status == "approved",
        RunRecord.run_date >= start_date.date(),
        RunRecord.run_date <= end_date.date()
    ).all()

    total_distance = sum(r.distance for r in records)
    total_runs = len(records)

    return {
        "total_distance": round(total_distance, 2),
        "total_runs": total_runs
    }


@router.get("/weekly")
def get_weekly_leaderboard(
    group_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取周跑量排行榜"""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    users = db.query(User)
    if group_type:
        users = users.filter(User.group_type == group_type)

    leaderboard = []
    for user in users.all():
        stats = get_user_stats(db, user.id, start_of_week, today)
        leaderboard.append({
            "user_id": user.id,
            "username": user.username,
            "academy": user.academy,
            "group_type": user.group_type,
            **stats
        })

    # 按跑量排序
    leaderboard.sort(key=lambda x: x["total_distance"], reverse=True)

    # 添加排名
    for i, item in enumerate(leaderboard):
        item["rank"] = i + 1

    return leaderboard


@router.get("/monthly")
def get_monthly_leaderboard(
    group_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取月跑量排行榜"""
    today = datetime.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    users = db.query(User)
    if group_type:
        users = users.filter(User.group_type == group_type)

    leaderboard = []
    for user in users.all():
        stats = get_user_stats(db, user.id, start_of_month, today)
        leaderboard.append({
            "user_id": user.id,
            "username": user.username,
            "academy": user.academy,
            "group_type": user.group_type,
            **stats
        })

    leaderboard.sort(key=lambda x: x["total_distance"], reverse=True)

    for i, item in enumerate(leaderboard):
        item["rank"] = i + 1

    return leaderboard


@router.get("/attendance")
def get_attendance_leaderboard(
    group_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取打卡出勤排行榜"""
    today = datetime.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    users = db.query(User)
    if group_type:
        users = users.filter(User.group_type == group_type)

    leaderboard = []
    for user in users.all():
        count = db.query(RunRecord).filter(
            RunRecord.user_id == user.id,
            RunRecord.status == "approved",
            RunRecord.run_date >= start_of_month.date()
        ).count()

        leaderboard.append({
            "user_id": user.id,
            "username": user.username,
            "academy": user.academy,
            "group_type": user.group_type,
            "total_runs": count
        })

    leaderboard.sort(key=lambda x: x["total_runs"], reverse=True)

    for i, item in enumerate(leaderboard):
        item["rank"] = i + 1

    return leaderboard
