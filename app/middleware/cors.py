"""CORS 中间件"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.core.config import settings


def setup_cors(app: FastAPI):
    """设置 CORS 中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )
