"""API 路由聚合模块"""

from fastapi import APIRouter
from app.api.v1 import router as v1_router

# 创建主路由
api_router = APIRouter()

# 注册 v1 路由
api_router.include_router(v1_router, prefix="/v1")
