"""
依赖注入模块

提供 FastAPI 路由中常用的依赖项
"""

from fastapi import HTTPException, status

from app.middleware.request_context import get_user_id, get_session_id


async def get_current_user_id() -> str:
    """
    获取当前已认证用户的 user_id

    如果用户未登录（没有有效的 session），抛出 401 异常

    Usage:
        from app.core.deps import get_current_user_id

        @router.get("/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            # user_id 已验证，可以直接使用
            ...
    """
    user_id = get_user_id()
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Session"},
        )
    return user_id


async def get_current_session_id() -> str:
    """
    获取当前 session_id

    如果没有 session，抛出 401 异常

    Usage:
        from app.core.deps import get_current_session_id

        @router.post("/logout")
        async def logout(session_id: str = Depends(get_current_session_id)):
            # 可以用于登出时删除 session
            ...
    """
    session_id = get_session_id()
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
            headers={"WWW-Authenticate": "Session"},
        )
    return session_id


def get_optional_user_id() -> str:
    """
    获取当前用户 ID（可选）

    不强制要求登录，返回空字符串表示未登录

    Usage:
        from app.core.deps import get_optional_user_id

        @router.get("/public-data")
        async def get_public_data(user_id: str = Depends(get_optional_user_id)):
            if user_id:
                # 已登录用户
                ...
            else:
                # 游客
                ...
    """
    return get_user_id()
