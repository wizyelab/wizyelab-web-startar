"""API 路由聚合模块

实现路由自动发现机制，自动注册所有路由模块
"""

import inspect
from typing import Dict

from fastapi import APIRouter

from app.api.v1.public import routers as public_routers
from app.api.v1.internal import routers as internal_routers


def get_routers() -> Dict[str, APIRouter]:
    """
    自动发现并返回所有路由

    通过 inspect 模块遍历 public 和 internal 下的所有模块，
    自动发现包含 router 属性的模块并返回。

    Returns:
        Dict[str, APIRouter]: {路由名称: 路由实例}
    """
    available = {}

    # 自动发现 public routers
    for name, router_module in inspect.getmembers(public_routers, inspect.ismodule):
        if hasattr(router_module, "router") and isinstance(router_module.router, APIRouter):
            available[f"public_{name}"] = router_module.router

    # 自动发现 internal routers
    for name, router_module in inspect.getmembers(internal_routers, inspect.ismodule):
        if hasattr(router_module, "router") and isinstance(router_module.router, APIRouter):
            available[f"internal_{name}"] = router_module.router

    return available


def create_api_router() -> APIRouter:
    """
    创建并配置 API 路由

    Returns:
        APIRouter: 配置好的主路由
    """
    api_router = APIRouter()

    # 获取所有路由
    routers = get_routers()

    # 注册 public 路由
    for name, router in routers.items():
        if name.startswith("public_"):
            api_router.include_router(router, prefix="/v1/public")
        elif name.startswith("internal_"):
            api_router.include_router(router, prefix="/v1/internal")

    return api_router


# 创建主路由
api_router = create_api_router()
