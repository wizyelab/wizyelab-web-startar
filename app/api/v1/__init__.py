"""API v1 模块"""

from fastapi import APIRouter
from app.api.v1.public import router as public_router
from app.api.v1.internal import router as internal_router

router = APIRouter()

# 注册子路由
router.include_router(public_router)
router.include_router(internal_router)
