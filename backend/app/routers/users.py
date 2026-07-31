from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.security import get_current_user, verify_password, get_password_hash

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户个人档案"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新个人档案"""
    if user_update.username is not None:
        # 检查用户名是否已被其他用户使用
        existing = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        current_user.username = user_update.username

    if user_update.academy is not None:
        current_user.academy = user_update.academy

    if user_update.grade is not None:
        current_user.grade = user_update.grade

    if user_update.group_type is not None:
        current_user.group_type = user_update.group_type

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取指定用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


class PasswordChange(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


@router.put("/me/password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码与确认密码不一致"
        )

    if len(password_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度不能少于6位"
        )

    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "密码修改成功"}


class RoleChange(BaseModel):
    admin_password: str
    target_role: str  # "admin" or "member"


@router.put("/me/role")
def change_my_role(
    role_data: RoleChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """通过管理员密码变更自己的角色"""
    # 管理员验证密码
    ADMIN_PASSWORD = "764759717"  # 管理员验证密码

    if role_data.admin_password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员密码错误"
        )

    if role_data.target_role not in ["admin", "member"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目标角色只能是 admin 或 member"
        )

    current_user.role = role_data.target_role
    db.commit()
    db.refresh(current_user)

    return {"message": f"已成功将自己的角色设置为 {role_data.target_role}"}
