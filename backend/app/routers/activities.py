from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import csv
import io

from app.database import get_db
from app.models.user import User
from app.models.activity import Activity, ActivitySign
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.utils.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/activities", tags=["活动"])


@router.get("", response_model=List[ActivityResponse])
def get_activities(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取活动列表"""
    activities = db.query(Activity).order_by(
        Activity.activity_time.desc()
    ).offset(skip).limit(limit).all()

    result = []
    for activity in activities:
        sign_count = db.query(ActivitySign).filter(
            ActivitySign.activity_id == activity.id
        ).count()
        result.append({
            **{col.name: getattr(activity, col.name) for col in Activity.__table__.columns},
            "sign_count": sign_count
        })

    return result


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """获取活动详情"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )

    sign_count = db.query(ActivitySign).filter(
        ActivitySign.activity_id == activity_id
    ).count()

    return {
        **{col.name: getattr(activity, col.name) for col in Activity.__table__.columns},
        "sign_count": sign_count
    }


@router.post("", response_model=ActivityResponse)
def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """创建活动（仅管理员）"""
    new_activity = Activity(
        title=activity_data.title,
        activity_time=activity_data.activity_time,
        location=activity_data.location,
        content=activity_data.content,
        creator_id=current_user.id
    )

    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    return {
        **{col.name: getattr(new_activity, col.name) for col in Activity.__table__.columns},
        "sign_count": 0
    }


@router.post("/{activity_id}/sign")
def sign_up_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """报名活动"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )

    # 检查是否已报名
    existing = db.query(ActivitySign).filter(
        ActivitySign.user_id == current_user.id,
        ActivitySign.activity_id == activity_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已报名该活动"
        )

    sign = ActivitySign(
        user_id=current_user.id,
        activity_id=activity_id
    )

    db.add(sign)
    db.commit()

    return {"message": "报名成功"}


@router.delete("/{activity_id}/sign")
def cancel_sign_up(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消报名"""
    sign = db.query(ActivitySign).filter(
        ActivitySign.user_id == current_user.id,
        ActivitySign.activity_id == activity_id
    ).first()

    if not sign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="您未报名该活动"
        )

    db.delete(sign)
    db.commit()

    return {"message": "取消报名成功"}


# ============ 管理员活动管理 ============

@router.delete("/{activity_id}")
def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除活动（仅管理员）"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    # 删除活动的所有报名记录
    db.query(ActivitySign).filter(ActivitySign.activity_id == activity_id).delete()
    db.delete(activity)
    db.commit()

    return {"message": "删除成功"}


@router.get("/{activity_id}/signs")
def get_activity_signs(
    activity_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """获取活动报名列表（仅管理员）"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    signs = db.query(ActivitySign, User.username, User.student_id).join(
        User, ActivitySign.user_id == User.id
    ).filter(ActivitySign.activity_id == activity_id).order_by(
        ActivitySign.signed_at.desc()
    ).all()

    result = []
    for sign, username, student_id in signs:
        result.append({
            "user_id": sign.user_id,
            "username": username,
            "student_id": student_id,
            "signed_at": sign.signed_at.isoformat() if sign.signed_at else None
        })

    return result


@router.get("/{activity_id}/export")
def export_activity_signs(
    activity_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """导出活动报名为CSV（仅管理员）"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    signs = db.query(ActivitySign, User.username, User.student_id).join(
        User, ActivitySign.user_id == User.id
    ).filter(ActivitySign.activity_id == activity_id).order_by(
        ActivitySign.signed_at.desc()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(["姓名", "学号", "报名时间"])

    # 写入数据
    for sign, username, student_id in signs:
        signed_at = sign.signed_at.strftime("%Y-%m-%d %H:%M:%S") if sign.signed_at else ""
        writer.writerow([username, student_id, signed_at])

    output.seek(0)
    filename = f"activity_{activity_id}_signs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
