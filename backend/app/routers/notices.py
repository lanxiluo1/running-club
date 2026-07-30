from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.notice import Notice
from app.schemas.notice import NoticeCreate, NoticeResponse
from app.utils.security import get_current_user, get_current_admin_user

router = APIRouter(prefix="/api/notices", tags=["公告"])


@router.get("", response_model=List[NoticeResponse])
def get_notices(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取公告列表"""
    notices = db.query(Notice).join(
        User, Notice.publisher_id == User.id, isouter=True
    ).order_by(Notice.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for notice in notices:
        result.append({
            **{col.name: getattr(notice, col.name) for col in Notice.__table__.columns},
            "publisher_name": notice.publisher.username if notice.publisher else None
        })
    return result


@router.get("/{notice_id}", response_model=NoticeResponse)
def get_notice(notice_id: int, db: Session = Depends(get_db)):
    """获取公告详情"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    return {
        **{col.name: getattr(notice, col.name) for col in Notice.__table__.columns},
        "publisher_name": notice.publisher.username if notice.publisher else None
    }


@router.post("", response_model=NoticeResponse)
def create_notice(
    notice_data: NoticeCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """发布公告（仅管理员）"""
    new_notice = Notice(
        title=notice_data.title,
        content=notice_data.content,
        publisher_id=current_user.id
    )

    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)

    return {
        **{col.name: getattr(new_notice, col.name) for col in Notice.__table__.columns},
        "publisher_name": current_user.username
    }


@router.delete("/{notice_id}")
def delete_notice(
    notice_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """删除公告（仅管理员）"""
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )

    db.delete(notice)
    db.commit()

    return {"message": "删除成功"}
