# Profile接口设计文档

## 一、获取用户Profile

**URI**: `POST /joiiee/api/v1/internal/profile/info`

**功能描述**: 获取用户的详细资料信息，包括基本信息、统计数据、是否关注等

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| user_id | string | 必填 | 目标用户ID | - | 要查看的用户ID |

**请求示例**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "正确" | |
| data | ProfileData | 数据 | None | |

---

### ProfileData

| 字段 | 类型        | 含义 | 默认值 | 备注                                          |
|------|-----------|------|--------|---------------------------------------------|
| user_id | string    | 用户ID | "" |                                             |
| user_name | string    | 用户名 | "" |                                             |
| avatar | string    | 头像URL | "" |                                             |
| bio | string    | 个人简介 | "" |                                             |
| gender | int       | 性别 | "" | 1:male 2:female 3:other                     |
| location | string    | 位置 | "" |                                             | |
| interest_tags | list[int] | 兴趣标签ID列表 | [] |                                             |
| follower_count | int       | 粉丝数 | 0 |                                             |
| following_count | int       | 关注数 | 0 |                                             |
| post_count | int       | 帖子数 | 0 |                                             |
| is_followed | boolean   | 是否已关注 | false | 当前用户是否关注该用户                                 |
| is_self | boolean   | 是否本人 | false | 是否查看自己的Profile                              |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_name": "Joan",
        "avatar": "https://example.com/avatar/joan.png",
        "bio": "Paddle enthusiast | 3.5 level player",
        "gender": 2,
        "location": "San Francisco, CA",
        "interest_tags": [1, 2],
        "follower_count": 128,
        "following_count": 56,
        "post_count": 24,
        "is_followed": false,
        "is_self": true
    }
}
```

---

## 二、获取引导列表

**URI**: `POST /joiiee/api/v1/internal/profile/collect/guide_list`

**功能描述**: 获取Profile收集的引导问题列表，用于新用户注册后的引导流程

---

### 请求参数

无

**请求示例**:
```json
{}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | GuideData | 数据 | None | |

---

### GuideData

| 字段    | 类型              | 含义    | 默认值 | 备注                             |
|-------|-----------------|-------|-----|--------------------------------|
| items | list[GuideItem] | 引导项列表 | []  |                                |
| total_steps | int             | 总步骤数  | 0   |                                |

---

### GuideItem

| 字段          | 类型           | 含义           | 默认值 | 备注                      |
|-------------|--------------|--------------|-----|-------------------------|
| id          | string       | 引导项ID        | ""  | 如interests、skill_level、equipment |
| style       | int          | 引导样式         | 0   | 0: 无样式，对话式<br/>1:选项条<br/>2:选项卡 |
| guide_words | string       | 引导话术         | ""  |                         |
| profile_key | string       | profile页的字段名 | ""    |                         |
| sort        | int          | 排序           | 0   | 数字越小优先级越高               |
| options     | list[OptionItem] | 选项列表         | []  |                         |
| is_required | boolean      | 是否必填         | false |                         |

---

### OptionItem

| 字段           | 类型 | 含义    | 默认值 | 备注 |
|--------------|------|-------|--------|---|
| content      | string | 展示内容  | "" |   |
| description  | string | 选项描述  | "" |   |
| icon_url     | string | 图标URL | "" |   |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "id": "interests",
                "style": 2,
                "guide_words": "What sports are you interested in?",
                "profile_key": "interest_tags",
                "sort": 1,
                "options": [
                    {
                        "content": "Padel",
                        "description": "",
                        "icon_url": "https://example.com/icons/padel.png"
                    },
                    {
                        "content": "Tennis",
                        "description": "",
                        "icon_url": "https://example.com/icons/tennis.png"
                    },
                    {
                        "content": "Pickleball",
                        "description": "",
                        "icon_url": "https://example.com/icons/pickleball.png"
                    }
                ],
                "is_required": true
            },
            {
                "id": "skill_level",
                "style": 1,
                "guide_words": "What's your skill level?",
                "profile_key": "skill_level",
                "sort": 2,
                "options": [
                    {
                        "content": "Beginner",
                        "description": "Just getting started",
                        "icon_url": ""
                    },
                    {
                        "content": "Intermediate",
                        "description": "Have some experience",
                        "icon_url": ""
                    },
                    {
                        "content": "Advanced",
                        "description": "Skilled player",
                        "icon_url": ""
                    },
                    {
                        "content": "Professional",
                        "description": "Pro level",
                        "icon_url": ""
                    }
                ],
                "is_required": true
            },
            {
                "id": "equipment",
                "style": 0,
                "guide_words": "Tell me about your equipment",
                "profile_key": "equipment_config",
                "sort": 3,
                "options": [],
                "is_required": false
            }
        ],
        "total_steps": 3
    }
}
```

---

## 三、更新Profile数据

**URI**: `POST /joiiee/api/v1/internal/profile/update`

**功能描述**: 更新个人profile页

---

### 请求参数

| 字段         | 类型           | 是否必填 | 含义    | 默认值 | 备注 |
|------------|--------------|------|-------|---|------|
| name | string | 选填 | 用户名 | - | 最大50字符 |
| avatar | string | 选填 | 头像URL | - | |
| bio | string | 选填 | 个人简介 | - | 最大500字符 |
| gender | int       | 性别 | "" | 1:male 2:female 3:other                     |
| location | string | 选填 | 位置 | - | |
| ....       | list[string] | 选填   | 引导的数据 | - | |

**注**: 除了固定的个人信息外, guide_list接口中guide_key的值都可以作为参数，参数值为 list[string] 填入optionItem的content,支持多选
eg: tag_content = ["padel", "tennis"]
**请求示例**:
```json
{
    "tag_content": ["padel", "tennis"]
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | object | 数据 | None | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": null
}
```

---

## 四、用户帖子列表

**URI**: `POST /joiiee/api/v1/internal/profile/posts`

**功能描述**: 获取用户发布的帖子列表，用于Profile页展示

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| user_id | string | 必填 | 用户ID | - | |
| page | int | 选填 | 页码 | 1 | 从1开始 |
| page_size | int | 选填 | 每页数量 | 20 | 最大50 |

**请求示例**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "page": 1,
    "page_size": 20
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | PostListData | 数据 | None | |

---

### PostListData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[Post] | 帖子列表 | [] | |
| total | int | 总数 | 0 | |
| page | int | 当前页 | 1 | |
| page_size | int | 每页数量 | 20 | |
| has_more | boolean | 是否有更多 | false | |

---

### Post

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 内容ID | "" | |
| post_type | int | 内容类型 | 0 | 1:video, 2:image, 3:text |
| title | string | 标题 | "" | |
| description | string | 描述 | "" | |
| content | string | 内容 | "" | |
| thumbnail_url | string | 缩略图 | "" | |
| img_urls | list[string] | 图片列表 | [] | 图片URL列表 |
| video | Video | 视频信息 | null | post_type=1时存在 |
| author | Author | 作者信息 | null | |
| like_count | int | 点赞数 | 0 | |
| comment_count | int | 评论数 | 0 | |
| share_count | int | 分享数 | 0 | |
| is_liked | boolean | 是否已点赞 | false | 当前用户是否点赞 |
| is_collected | boolean | 是否已收藏 | false | 当前用户是否收藏 |
| create_time | string | 创建时间 | "" | ISO 8601格式 |
| update_time | string | 更新时间 | "" | ISO 8601格式 |
| display_time  | string        | 展示时间 | "" | 如"30 minutes ago" |


---

### Author

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| user_id | string | 用户ID | "" | |
| user_name | string | 用户名 | "" | |
| avatar | string | 头像URL | "" | |
| is_followed | boolean | 是否已关注 | false | |

---

### Video

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 视频id | "" | |
| height | int | 视频高度 | 0 | |
| width | int | 视频宽度 | 0 | |
| duration | int | 视频时长 | 0 | 单位：秒 |
| cover_url | string | 封面图 | "" | |
| main_url | string | 主链接 | "" | |
| back_urls | list[string] | 备用链接 | [] | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "id": "post_001",
                "post_type": 1,
                "title": "I'm so excited",
                "description": "Voulez-vous couch...",
                "content": "",
                "thumbnail_url": "https://example.com/thumb_001.png",
                "img_urls": [],
                "video": {
                    "id": "video_001",
                    "height": 1920,
                    "width": 1080,
                    "duration": 30,
                    "cover_url": "https://example.com/thumb_001.png",
                    "main_url": "https://example.com/videos/post_001.mp4",
                    "back_urls": []
                },
                "author": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_name": "Joan",
                    "avatar": "https://example.com/avatar/joan.png",
                    "is_followed": false
                },
                "like_count": 128,
                "comment_count": 32,
                "share_count": 8,
                "is_liked": false,
                "is_collected": false,
                "create_time": "2026-01-20T10:30:00Z",
                "update_time": "2026-01-20T10:30:00Z",
                "display_time": "20 Jan 2026"
            },
            {
                "id": "post_002",
                "post_type": 2,
                "title": "I'm so excited",
                "description": "Voulez-vous couch...",
                "content": "",
                "thumbnail_url": "https://example.com/thumb_002.png",
                "img_urls": [
                    "https://example.com/images/post_002.png"
                ],
                "video": null,
                "author": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_name": "Joan",
                    "avatar": "https://example.com/avatar/joan.png",
                    "is_followed": false
                },
                "like_count": 64,
                "comment_count": 16,
                "share_count": 4,
                "is_liked": true,
                "is_collected": false,
                "create_time": "2026-01-19T15:20:00Z",
                "update_time": "2026-01-19T15:20:00Z",
                "display_time": "19 Jan 2026"
            }
        ],
        "total": 24,
        "page": 1,
        "page_size": 20,
        "has_more": true
    }
}
```

---

## 五、创建帖子

**URI**: `POST /joiiee/api/v1/internal/profile/post/create`

**功能描述**: 发布新帖子，支持图片、视频、纯文本类型

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| post_type | int | 必填 | 帖子类型 | - | 1:video, 2:image, 3:text |
| title | string | 选填 | 标题 | "" | 最大200字符 |
| description | string | 选填 | 描述/正文 | "" | 最大2000字符 |
| content | string | 选填 | 内容 | "" | |
| img_urls | list[string] | 选填 | 图片URL列表 | [] | 图片URL |
| video | Video | 选填 | 视频信息 | null | post_type=1时使用 |
| tags | list[int] | 选填 | 标签ID列表 | [] | 帖子标签 |

---

### Video

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 视频ID | "" | |
| height | int | 视频高度 | 0 | |
| width | int | 视频宽度 | 0 | |
| duration | int | 视频时长 | 0 | 单位：秒 |
| cover_url | string | 封面图 | "" | |
| main_url | string | 主链接 | "" | 视频播放地址 |
| back_urls | list[string] | 备用链接 | [] | 备用CDN地址 |

**请求示例**:
```json
{
    "post_type": 1,
    "title": "",
    "description": "Great match today! Had so much fun playing paddle.",
    "content": "",
    "img_urls": [],
    "video": {
        "id": "video_001",
        "height": 1920,
        "width": 1080,
        "duration": 30,
        "cover_url": "https://example.com/covers/video_001.png",
        "main_url": "https://example.com/videos/upload_001.mp4",
        "back_urls": []
    },
    "tags": [1, 2]
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | CreatePostData | 数据 | None | |

---

### CreatePostData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| post_id | string | 帖子ID | "" | 新创建的帖子ID |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "post_id": "post_new_001"
    }
}
```

---

## 六、删除帖子

**URI**: `POST /joiiee/api/v1/internal/profile/post/delete`

**功能描述**: 删除自己发布的帖子

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| post_id | string | 必填 | 帖子ID | - | |

**请求示例**:
```json
{
    "post_id": "post_001"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | object | 数据 | None | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": null
}
```

---

## 七、关注取关用户（暂时没用)

**URI**: `POST /joiiee/api/v1/internal/profile/follow`

**功能描述**: 关注和取关目标用户

---

### 请求参数

| 字段             | 类型      | 是否必填 | 含义 | 默认值  | 备注                |
|----------------|---------|----------|------|------|-------------------|
| target_user_id | string  | 必填 | 目标用户ID | -    | 要关注的用户ID          |
| is_follow      | boolean | 必填| 动作类型| true |  |

**请求示例**:
```json
{
    "target_user_id": "660e8400-e29b-41d4-a716-446655440001",
    "is_follow": true
  
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | FollowData | 数据 | None | |

---

### FollowData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| is_followed | boolean | 是否已关注 | false | |
| follower_count | int | 目标用户粉丝数 | 0 | 关注后的最新粉丝数 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "is_followed": true,
        "follower_count": 129
    }
}
```

---

## 八、获取用户粉丝列表和关注的人(暂时没用)

**URI**: `POST /joiiee/api/v1/internal/profile/followers`

**功能描述**: 获取用户的粉丝列表

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| user_id | string | 必填 | 用户ID | - | |
| page | int | 选填 | 页码 | 1 | 从1开始 |
| page_size | int | 选填 | 每页数量 | 20 | 最大50 |

**请求示例**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "page": 1,
    "page_size": 20
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | FollowListData | 数据 | None | |

---

### FollowListData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[UserItem] | 用户列表 | [] | |
| total | int | 总数 | 0 | |
| has_more | boolean | 是否有更多 | false | |

---

### UserItem

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| user_id | string | 用户ID | "" | |
| user_name | string | 用户名 | "" | |
| avatar | string | 头像URL | "" | |
| bio | string | 个人简介 | "" | |
| is_following | boolean | 是否已关注 | false | 当前用户是否关注该用户 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "user_id": "user_001",
                "user_name": "Louis Hendrix",
                "avatar": "https://example.com/avatar_001.png",
                "bio": "Tennis lover",
                "is_following": true
            },
            {
                "user_id": "user_002",
                "user_name": "Emma Wilson",
                "avatar": "https://example.com/avatar_002.png",
                "bio": "Paddle beginner",
                "is_following": false
            }
        ],
        "total": 128,
        "has_more": true
    }
}
```

---


## 九、用户反馈

**URI**: `POST /joiiee/api/v1/internal/profile/feedback`

**功能描述**: 提交用户反馈，包括不喜欢、举报等

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|------|------|-----|------|
| post_id | string | 选填   | 内容ID | 0   | |
| feedback_type | int | 必填   | 反馈类型 | -   | 1:dislike, 2:not_interested, 3:report, 4:spam |
| reason | string | 选填   | 反馈原因 | -   | 最大200字符 |
| detail | string | 选填   | 详细描述 | -   | 最大1000字符 |

**请求示例**:
```json
{
    "post_id": "post_001",
    "feedback_type": 3,
    "reason": "inappropriate_content",
    "detail": "This content contains misleading information."
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | object | 数据 | None | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": null
}
```

---


## 十、错误码定义

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 系统错误 |
| 100 | 参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 1001 | 无效的Token |
| 1002 | Token已过期 |
| 1006 | 用户不存在 |
| 4001 | 不能关注自己 |
| 4002 | 已经关注该用户 |
| 4003 | 未关注该用户 |
| 4004 | 反馈提交失败 |

---

## 十一、feedback_type 类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | dislike | 不喜欢 |
| 2 | not_interested | 不感兴趣 |
| 3 | report | 举报 |
| 4 | spam | 垃圾内容 |

---

**文档版本**: v1.0
**更新日期**: 2026-01-21
**编写人**: Joiiee Tech Team
