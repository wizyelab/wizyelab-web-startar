"""Joiiee API 测试"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """创建测试客户端"""
    from main import app
    return TestClient(app)


# ========================= Home API 测试 =========================


class TestHomeAPI:
    """首页 API 测试"""

    def test_tag_content_list_default(self, client):
        """测试获取标签内容列表 - 默认参数"""
        response = client.post(
            "/api/v1/internal/home/tag_content_list",
            json={"tag_id": 0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "正确"
        assert "tag_list" in data["data"]
        assert "first_login" in data["data"]
        # 验证第一个 tag 被选中
        tag_list = data["data"]["tag_list"]
        assert len(tag_list) > 0
        assert tag_list[0]["is_selected"] is True
        # 验证内容列表不为空
        assert len(tag_list[0]["content_list"]) > 0

    def test_tag_content_list_specific_tag(self, client):
        """测试获取特定标签内容列表"""
        response = client.post(
            "/api/v1/internal/home/tag_content_list",
            json={"tag_id": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        # 验证标签 2 被选中
        tag_list = data["data"]["tag_list"]
        for tag in tag_list:
            if tag["tag_id"] == 2:
                assert tag["is_selected"] is True
            else:
                assert tag["is_selected"] is False

    def test_feed_default(self, client):
        """测试获取 Feed - 默认参数"""
        response = client.post(
            "/api/v1/internal/home/feed",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "has_more" in data["data"]
        # 验证帖子结构
        items = data["data"]["items"]
        assert len(items) > 0
        post = items[0]
        assert "id" in post
        assert "post_type" in post
        assert "author" in post

    def test_feed_with_pagination(self, client):
        """测试获取 Feed - 分页参数"""
        response = client.post(
            "/api/v1/internal/home/feed",
            json={"page": 2, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["page"] == 2
        assert data["data"]["page_size"] == 10

    def test_user_action_like(self, client):
        """测试用户行为 - 点赞"""
        response = client.post(
            "/api/v1/internal/home/user/action",
            json={"post_id": "feed_001", "action_type": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["action_type"] == 1
        assert data["data"]["is_active"] is True
        assert data["data"]["count"] > 0

    def test_user_action_unlike(self, client):
        """测试用户行为 - 取消点赞"""
        response = client.post(
            "/api/v1/internal/home/user/action",
            json={"post_id": "feed_001", "action_type": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["action_type"] == 2
        assert data["data"]["is_active"] is False

    def test_user_action_collect(self, client):
        """测试用户行为 - 收藏"""
        response = client.post(
            "/api/v1/internal/home/user/action",
            json={"post_id": "feed_001", "action_type": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["action_type"] == 3
        assert data["data"]["is_active"] is True

    def test_generate_share_link(self, client):
        """测试生成分享链接"""
        response = client.post(
            "/api/v1/internal/home/share/generate_link",
            json={"post_id": "feed_001", "share_type": "h5"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "share_url" in data["data"]
        assert "share_text" in data["data"]
        assert "share_image" in data["data"]
        assert "feed_001" in data["data"]["share_url"]


# ========================= Detail API 测试 =========================


class TestDetailAPI:
    """详情页 API 测试"""

    def test_get_detail_info(self, client):
        """测试获取内容详情"""
        response = client.post(
            "/api/v1/internal/detail/info",
            json={"post_id": "post_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "post" in data["data"]
        assert "related_posts" in data["data"]
        # 验证帖子结构
        post = data["data"]["post"]
        assert post["id"] == "post_001"
        assert "author" in post
        assert "video" in post

    def test_get_comment_list(self, client):
        """测试获取评论列表"""
        response = client.post(
            "/api/v1/internal/detail/comment_list",
            json={"post_id": "post_001", "page": 1, "page_size": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "comments" in data["data"]
        assert "total" in data["data"]
        # 验证评论结构
        comments = data["data"]["comments"]
        assert len(comments) > 0
        comment = comments[0]
        assert "comment_id" in comment
        assert "user" in comment
        assert "text" in comment

    def test_get_comment_list_with_sort(self, client):
        """测试获取评论列表 - 排序"""
        response = client.post(
            "/api/v1/internal/detail/comment_list",
            json={"post_id": "post_001", "sort_by": 1}  # 热门排序
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_create_comment(self, client):
        """测试发表评论"""
        response = client.post(
            "/api/v1/internal/detail/create_comment",
            json={
                "post_id": "post_001",
                "text": "Great post!",
                "level": 0
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "comment_id" in data["data"]
        assert "comment" in data["data"]
        assert data["data"]["comment"]["text"] == "Great post!"

    def test_create_reply(self, client):
        """测试回复评论"""
        response = client.post(
            "/api/v1/internal/detail/create_comment",
            json={
                "post_id": "post_001",
                "text": "I agree!",
                "comment_id": "comment_001",
                "level": 1,
                "reply_to_user_id": "user_sean"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["comment"]["level"] == 1
        assert data["data"]["comment"]["reply_to_user"] is not None

    def test_delete_comment(self, client):
        """测试删除评论"""
        response = client.post(
            "/api/v1/internal/detail/delete_comment",
            json={"comment_id": "comment_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_get_comment_by_level(self, client):
        """测试获取评论回复列表"""
        response = client.post(
            "/api/v1/internal/detail/get_comment_by_level",
            json={
                "comment_id": "comment_001",
                "level": 1,
                "page": 1,
                "page_size": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "has_more" in data["data"]


# ========================= Profile API 测试 =========================


class TestProfileAPI:
    """Profile API 测试"""

    def test_get_profile_info(self, client):
        """测试获取用户 Profile"""
        response = client.post(
            "/api/v1/internal/profile/info",
            json={"user_id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        profile = data["data"]
        assert profile["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert "user_name" in profile
        assert "avatar" in profile
        assert "follower_count" in profile
        assert "following_count" in profile

    def test_get_guide_list(self, client):
        """测试获取引导列表"""
        response = client.post(
            "/api/v1/internal/profile/collect/guide_list",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total_steps" in data["data"]
        # 验证引导项结构
        items = data["data"]["items"]
        assert len(items) > 0
        item = items[0]
        assert "id" in item
        assert "guide_words" in item
        assert "options" in item

    def test_update_profile(self, client):
        """测试更新 Profile"""
        response = client.post(
            "/api/v1/internal/profile/update",
            json={
                "name": "NewName",
                "bio": "New bio",
                "tag_content": ["padel", "tennis"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_get_user_posts(self, client):
        """测试获取用户帖子列表"""
        response = client.post(
            "/api/v1/internal/profile/posts",
            json={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "page": 1,
                "page_size": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        # 验证帖子结构
        items = data["data"]["items"]
        assert len(items) > 0
        post = items[0]
        assert "id" in post
        assert "post_type" in post

    def test_create_post(self, client):
        """测试创建帖子"""
        response = client.post(
            "/api/v1/internal/profile/post/create",
            json={
                "post_type": 1,
                "description": "Great match today!",
                "img_urls": ["https://example.com/video.mp4"],
                "tags": [1, 2]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "post_id" in data["data"]

    def test_delete_post(self, client):
        """测试删除帖子"""
        response = client.post(
            "/api/v1/internal/profile/post/delete",
            json={"post_id": "post_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_follow_user(self, client):
        """测试关注用户"""
        response = client.post(
            "/api/v1/internal/profile/follow",
            json={
                "target_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "is_follow": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_followed"] is True
        assert "follower_count" in data["data"]

    def test_unfollow_user(self, client):
        """测试取关用户"""
        response = client.post(
            "/api/v1/internal/profile/follow",
            json={
                "target_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "is_follow": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["is_followed"] is False

    def test_get_followers(self, client):
        """测试获取粉丝列表"""
        response = client.post(
            "/api/v1/internal/profile/followers",
            json={
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "page": 1,
                "page_size": 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "items" in data["data"]
        assert "total" in data["data"]
        # 验证用户项结构
        items = data["data"]["items"]
        assert len(items) > 0
        user = items[0]
        assert "user_id" in user
        assert "user_name" in user

    def test_submit_feedback(self, client):
        """测试提交反馈"""
        response = client.post(
            "/api/v1/internal/profile/feedback",
            json={
                "post_id": "post_001",
                "feedback_type": 3,
                "reason": "inappropriate_content",
                "detail": "This content contains misleading information."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0


# ========================= 边界测试 =========================


class TestBoundaryConditions:
    """边界条件测试"""

    def test_feed_page_size_max(self, client):
        """测试 Feed 页大小最大值"""
        response = client.post(
            "/api/v1/internal/home/feed",
            json={"page_size": 50}
        )
        assert response.status_code == 200

    def test_feed_page_size_exceed_max(self, client):
        """测试 Feed 页大小超过最大值"""
        response = client.post(
            "/api/v1/internal/home/feed",
            json={"page_size": 100}
        )
        assert response.status_code == 422  # Validation error

    def test_comment_text_max_length(self, client):
        """测试评论内容最大长度"""
        long_text = "a" * 1000
        response = client.post(
            "/api/v1/internal/detail/create_comment",
            json={
                "post_id": "post_001",
                "text": long_text,
                "level": 0
            }
        )
        assert response.status_code == 200

    def test_comment_text_exceed_max_length(self, client):
        """测试评论内容超过最大长度"""
        long_text = "a" * 1001
        response = client.post(
            "/api/v1/internal/detail/create_comment",
            json={
                "post_id": "post_001",
                "text": long_text,
                "level": 0
            }
        )
        assert response.status_code == 422  # Validation error
