from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.models import User, RunRecord, Activity, ActivitySign, Notice
from app.routers import auth, users, run_records, activities, notices, leaderboard, admin

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="校园跑团训练管理系统",
    description="面向高校跑步社团的轻量化训练管理Web平台",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://running-club-gzc2-lyart.vercel.app",
        "http://localhost:5173",
        "*"
    ],  # 允许所有来源，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(run_records.router)
app.include_router(activities.router)
app.include_router(notices.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)


@app.get("/")
def root():
    """根路径"""
    return {"message": "校园跑团训练管理系统 API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}
