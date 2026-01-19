"""对外公开 API 路由"""

from fastapi import APIRouter

from app.api.v1.public.files import router as files_router

router = APIRouter(prefix="/public", tags=["public"])

# 注册子路由
router.include_router(files_router)


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "Public API is healthy"}


@router.get("/")
async def root():
    """根路径"""
    return {"message": "Welcome to Public API"}
