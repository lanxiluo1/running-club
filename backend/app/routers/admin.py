from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import csv
import io
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.run_record import RunRecord
from app.schemas.run_record import RunRecordResponse
from app.utils.security import get_current_admin_user, get_password_hash

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get("/users", response_model=List[dict])
def get_all_users(
    skip: int = 0,
    limit: int = 50,
    group_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有成员列表（仅管理员）"""
    query = db.query(User)

    if group_type:
        query = query.filter(User.group_type == group_type)

    users = query.offset(skip).limit(limit).all()
    return [
        {
            **{col.name: getattr(user, col.name) for col in User.__table__.columns},
        }
        for user in users
    ]


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新成员信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "username" in user_update and user_update["username"]:
        user.username = user_update["username"]
    if "academy" in user_update:
        user.academy = user_update.get("academy")
    if "grade" in user_update:
        user.grade = user_update.get("grade")
    if "group_type" in user_update and user_update["group_type"]:
        user.group_type = user_update["group_type"]
    if "role" in user_update and user_update["role"]:
        user.role = user_update["role"]

    db.commit()
    db.refresh(user)

    return {
        **{col.name: getattr(user, col.name) for col in User.__table__.columns},
    }


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """重置用户密码为123456（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.hashed_password = get_password_hash("123456")
    db.commit()

    return {"message": "密码已重置为123456"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除成员（仅管理员）"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 先删除用户的打卡记录和活动报名
    from app.models.run_record import RunRecord
    from app.models.activity import ActivitySign

    db.query(RunRecord).filter(RunRecord.user_id == user_id).delete()
    db.query(ActivitySign).filter(ActivitySign.user_id == user_id).delete()

    db.delete(user)
    db.commit()

    return {"message": "删除成功"}


# ============ 打卡审核 ============

@router.get("/run-records/all", response_model=List[dict])
def get_all_records(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有打卡记录（仅管理员）"""
    records = db.query(RunRecord, User.username).join(
        User, RunRecord.user_id == User.id
    ).order_by(RunRecord.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for record, username in records:
        result.append({
            **{col.name: getattr(record, col.name) for col in RunRecord.__table__.columns},
            "username": username
        })
    return result


@router.put("/run-records/{record_id}/review")
def review_run_record(
    record_id: int,
    review_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """审核打卡记录（仅管理员）"""
    status = review_data.get('status')
    if status not in ["approved", "rejected", "pending"]:
        raise HTTPException(
            status_code=400,
            detail="状态只能是 approved、rejected 或 pending"
        )

    record = db.query(RunRecord).filter(RunRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="打卡记录不存在")

    record.status = status
    db.commit()

    status_text = {"approved": "通过", "rejected": "驳回", "pending": "退回审核"}
    return {"message": f"已设置为{status_text.get(status, status)}"}


@router.delete("/run-records/{record_id}")
def delete_run_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除打卡记录（仅管理员）"""
    record = db.query(RunRecord).filter(RunRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="打卡记录不存在")

    db.delete(record)
    db.commit()

    return {"message": "删除成功"}


# ============ 统计概览 ============

@router.get("/stats/overview")
def get_stats_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """获取整体统计数据（仅管理员）"""
    from app.models.activity import Activity
    from app.models.notice import Notice

    total_users = db.query(User).count()
    total_records = db.query(RunRecord).count()
    approved_records = db.query(RunRecord).filter(RunRecord.status == "approved").count()
    pending_records = db.query(RunRecord).filter(RunRecord.status == "pending").count()
    total_activities = db.query(Activity).count()
    total_notices = db.query(Notice).count()

    total_distance = db.query(func.sum(RunRecord.distance)).filter(
        RunRecord.status == "approved"
    ).scalar() or 0

    return {
        "total_users": total_users,
        "total_records": total_records,
        "approved_records": approved_records,
        "pending_records": pending_records,
        "total_distance": round(float(total_distance), 2),
        "total_activities": total_activities,
        "total_notices": total_notices
    }


# ============ 数据导出 ============

@router.get("/export/run-records")
def export_run_records_csv(
    start_date: str = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    导出打卡记录为CSV
    格式：姓名 | 日期1 | 日期2 | ... | 总跑量
    """
    # 查询所有已审核通过的打卡记录
    query = db.query(RunRecord, User.username, User.student_id).join(
        User, RunRecord.user_id == User.id
    ).filter(RunRecord.status == "approved")

    # 日期筛选
    if start_date:
        query = query.filter(RunRecord.run_date >= start_date)
    if end_date:
        query = query.filter(RunRecord.run_date <= end_date)

    records = query.order_by(RunRecord.run_date).all()

    if not records:
        raise HTTPException(status_code=404, detail="没有可导出的数据")

    # 构建数据透视表: {用户ID: {用户名: xxx, 学号: xxx, 日期: 跑量, ...}}
    user_data = {}
    all_dates = set()

    for record, username, student_id in records:
        uid = record.user_id
        if uid not in user_data:
            user_data[uid] = {
                "username": username,
                "student_id": student_id,
                "dates": {}
            }
        date_str = record.run_date.isoformat() if hasattr(record.run_date, 'isoformat') else str(record.run_date)
        # 累加同一天的跑量
        if date_str in user_data[uid]["dates"]:
            user_data[uid]["dates"][date_str] += record.distance
        else:
            user_data[uid]["dates"][date_str] = record.distance
        all_dates.add(date_str)

    # 按日期排序
    sorted_dates = sorted(all_dates)

    # 生成CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    header = ["姓名", "学号"] + sorted_dates + ["总跑量"]
    writer.writerow(header)

    # 数据行
    for uid, data in user_data.items():
        row = [data["username"], data["student_id"]]
        total = 0.0
        for date in sorted_dates:
            distance = data["dates"].get(date, 0)
            row.append(f"{distance:.2f}" if distance else "")
            total += distance
        row.append(f"{total:.2f}")
        writer.writerow(row)

    # 生成文件
    output.seek(0)
    filename = f"run_records_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
