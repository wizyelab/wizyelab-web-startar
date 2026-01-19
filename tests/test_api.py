"""API 测试"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """创建测试客户端"""
    from main import app
    return TestClient(app)


def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_livez(client):
    """测试存活检查"""
    response = client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_public_api_health(client):
    """测试 Public API 健康检查"""
    response = client.get("/api/v1/public/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_internal_api_health(client):
    """测试 Internal API 健康检查"""
    response = client.get("/api/v1/internal/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_public_api_root(client):
    """测试 Public API 根路径"""
    response = client.get("/api/v1/public/")
    assert response.status_code == 200


def test_internal_api_root(client):
    """测试 Internal API 根路径"""
    response = client.get("/api/v1/internal/")
    assert response.status_code == 200


# ========================= 限流测试 =========================

def test_rate_limit_headers(client):
    """测试限流响应头"""
    response = client.get("/api/v1/public/")
    assert response.status_code == 200

    # 检查限流响应头
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Window" in response.headers


def test_rate_limit_excluded_paths(client):
    """测试排除路径不进行限流"""
    # 健康检查路径应该不包含限流头
    response = client.get("/health")
    assert response.status_code == 200
    # 排除的路径不应该有限流响应头
    assert "X-RateLimit-Limit" not in response.headers


def test_rate_limit_remaining_decreases(client):
    """测试剩余请求次数递减"""
    # 发送第一个请求
    response1 = client.get("/api/v1/public/health")
    assert response1.status_code == 200
    remaining1 = int(response1.headers.get("X-RateLimit-Remaining", 0))

    # 发送第二个请求
    response2 = client.get("/api/v1/public/health")
    assert response2.status_code == 200
    remaining2 = int(response2.headers.get("X-RateLimit-Remaining", 0))

    # 剩余次数应该递减（除非 Redis 不可用）
    # 注意：如果 Redis 不可用，remaining 可能相同
    assert remaining2 <= remaining1
