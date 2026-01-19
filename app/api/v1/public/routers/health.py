"""Public 健康检查路由"""

from fastapi import APIRouter

router = APIRouter(tags=["public"])


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "Public API is healthy"}


@router.get("/")
async def root():
    """根路径"""
    return {"message": "Welcome to Public API"}
