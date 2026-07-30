from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
import os
import shutil
import uuid

from app.database import get_db
from app.models.user import User
from app.models.run_record import RunRecord
from app.schemas.run_record import (
    RunRecordCreate, RunRecordResponse, RunRecordReview,
    OCRResponse, StatsResponse
)
from app.utils.security import get_current_user, get_current_admin_user
from app.services.ocr import ocr_service

router = APIRouter(prefix="/api/run-records", tags=["打卡记录"])


@router.post("", response_model=RunRecordResponse)
def create_run_record(
    record_data: RunRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建打卡记录"""
    new_record = RunRecord(
        user_id=current_user.id,
        run_date=record_data.run_date,
        distance=record_data.distance,
        duration=record_data.duration,
        pace=record_data.pace,
        heart_rate=record_data.heart_rate,
        training_type=record_data.training_type,
        screenshot_path=record_data.screenshot_path,
        check_in_method=record_data.check_in_method,
        status="pending"
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


@router.post("/admin/checkin", response_model=RunRecordResponse)
def admin_create_checkin(
    record_data: RunRecordCreate,
    target_user_id: int = Query(..., description="目标用户ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """管理员代成员打卡"""
    # 验证目标用户存在
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_record = RunRecord(
        user_id=target_user_id,
        run_date=record_data.run_date,
        distance=record_data.distance,
        duration=record_data.duration,
        pace=record_data.pace,
        heart_rate=record_data.heart_rate,
        training_type=record_data.training_type,
        screenshot_path=record_data.screenshot_path,
        check_in_method=record_data.check_in_method,
        status="approved"  # 管理员代打卡直接通过审核
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


@router.get("", response_model=List[RunRecordResponse])
def get_run_records(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取打卡记录列表"""
    query = db.query(RunRecord, User.username).join(User).order_by(RunRecord.created_at.desc())

    # 普通用户只能看到自己的记录，管理员可以看到所有
    if current_user.role != "admin":
        query = query.filter(RunRecord.user_id == current_user.id)

    if status_filter:
        query = query.filter(RunRecord.status == status_filter)

    records = query.offset(skip).limit(limit).all()

    result = []
    for record, username in records:
        record_dict = {
            **{col.name: getattr(record, col.name) for col in RunRecord.__table__.columns},
            "username": username
        }
        result.append(record_dict)

    return result


@router.get("/my")
def get_my_run_records(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的打卡记录（分页）"""
    records = db.query(RunRecord).filter(
        RunRecord.user_id == current_user.id
    ).order_by(RunRecord.run_date.desc()).offset(skip).limit(limit).all()

    total = db.query(func.count(RunRecord.id)).filter(
        RunRecord.user_id == current_user.id
    ).scalar()

    return {
        "data": records,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats", response_model=StatsResponse)
def get_run_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取个人统计数据"""
    # 获取已审核通过的打卡记录
    records = db.query(RunRecord).filter(
        RunRecord.user_id == current_user.id,
        RunRecord.status == "approved"
    ).all()

    total_distance = sum(r.distance for r in records)
    total_runs = len(records)

    avg_pace = None
    avg_heart_rate = None
    valid_paces = [r.pace for r in records if r.pace]
    valid_heart_rates = [r.heart_rate for r in records if r.heart_rate]

    if valid_paces:
        avg_pace = round(sum(valid_paces) / len(valid_paces), 2)
    if valid_heart_rates:
        avg_heart_rate = round(sum(valid_heart_rates) / len(valid_heart_rates), 1)

    # 计算周数据
    today = datetime.now().date()
    weekly_data = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        day_distance = sum(r.distance for r in records if r.run_date == date)
        weekly_data.append({"date": date.isoformat(), "distance": day_distance})

    # 计算月数据
    monthly_data = []
    for i in range(30):
        date = today - timedelta(days=29-i)
        day_distance = sum(r.distance for r in records if r.run_date == date)
        monthly_data.append({"date": date.isoformat(), "distance": day_distance})

    return {
        "total_distance": round(total_distance, 2),
        "total_runs": total_runs,
        "avg_pace": avg_pace,
        "avg_heart_rate": avg_heart_rate,
        "weekly_data": weekly_data,
        "monthly_data": monthly_data
    }


@router.post("/ocr", response_model=OCRResponse)
async def ocr_recognize(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传图片进行OCR识别"""
    # 保存上传的文件
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 调用OCR服务
    run_data = await ocr_service.recognize_run_data(file_path)

    # 删除临时文件
    try:
        os.remove(file_path)
    except:
        pass

    success = run_data.get("distance") is not None

    return OCRResponse(
        distance=run_data.get("distance"),
        duration=run_data.get("duration"),
        heart_rate=run_data.get("heart_rate"),
        date=run_data.get("date"),
        success=success,
        message=run_data.get("message", "识别成功" if success else "未能识别到跑步数据，请手动填写")
    )
