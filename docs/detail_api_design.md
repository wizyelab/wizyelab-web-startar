# 详情页接口设计文档

## 一、获取内容详情

**URI**: `POST /joiiee/api/v1/internal/detail/info`

**功能描述**: 获取帖子/内容的详情信息，包括内容、作者信息、互动数据等

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
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "正确" | |
| data | DetailData | 数据 | None | |

---

### DetailData

| 字段 | 类型         | 含义 | 默认值 | 备注 |
|------|------------|------|--------|------|
| post | Post       | 帖子详情 | null | |
| related_posts | list[Post] | 相关推荐 | [] | 相关帖子推荐 |

---

### Post

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 帖子ID | "" | |
| post_type | int | 帖子类型 | 0 | 1:video, 2:image, 3:text |
| title | string | 标题 | "" | |
| description | string | 描述/正文 | "" | |
| content | string | 内容 | "" | 完整内容文本 |
| img_urls | list[string] | 图片列表 | [] | 图片URL列表 |
| video | Video | 视频信息 | null | post_type=1时存在 |
| author | Author | 作者信息 | null | |
| like_count | int | 点赞数 | 0 | |
| comment_count | int | 评论数 | 0 | |
| share_count | int | 分享数 | 0 | |
| is_liked | boolean | 是否已点赞 | false | 当前用户是否点赞 |
| is_collected | boolean | 是否已收藏 | false | 当前用户是否收藏 |
| is_followed | boolean | 是否已关注作者 | false | |
| create_time | string | 创建时间 | "" | ISO 8601格式 |
| update_time | string | 更新时间 | "" | ISO 8601格式 |
| display_time | string | 展示时间 | "" | 如"09 Jan 2026" |

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

### Author

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| user_id | string | 用户ID | "" | |
| user_name | string | 用户名 | "" | |
| avatar | string | 头像URL | "" | |
| is_followed | boolean | 是否已关注 | false | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "post": {
            "id": "post_001",
            "post_type": 1,
            "title": "",
            "description": "I'm so excited. Voulez-vous coucher avec moi, ce soir. I love Hot dog and Oyster, and I think my champaign is from England, should I call it English Sparkling instead?",
            "content": "I'm so excited. Voulez-vous coucher avec moi, ce soir. I love Hot dog and Oyster, and I think my champaign is from England, should I call it English Sparkling instead?",
            "img_urls": [],
            "video": {
                "id": "video_001",
                "height": 1920,
                "width": 1080,
                "duration": 60,
                "cover_url": "https://example.com/cover_001.png",
                "main_url": "https://example.com/videos/post_001.mp4",
                "back_urls": []
            },
            "author": {
                "user_id": "user_louis",
                "user_name": "Louis",
                "avatar": "https://example.com/avatar/louis.png",
                "is_followed": false
            },
            "like_count": 161,
            "comment_count": 11,
            "share_count": 2,
            "is_liked": false,
            "is_collected": false,
            "is_followed": false,
            "create_time": "2026-01-09T10:30:00Z",
            "update_time": "2026-01-09T10:30:00Z",
            "display_time": "09 Jan 2026"
        },
        "related_posts": [
            {
                "id": "post_002",
                "post_type": 1,
                "title": "Morning practice",
                "description": "Great session today",
                "content": "",
                "img_urls": [],
                "video": {
                    "id": "video_002",
                    "height": 1920,
                    "width": 1080,
                    "duration": 45,
                    "cover_url": "https://example.com/cover_002.png",
                    "main_url": "https://example.com/videos/post_002.mp4",
                    "back_urls": []
                },
                "author": {
                    "user_id": "user_002",
                    "user_name": "Emma",
                    "avatar": "https://example.com/avatar/emma.png",
                    "is_followed": false
                },
                "like_count": 89,
                "comment_count": 12,
                "share_count": 3,
                "is_liked": false,
                "is_collected": false,
                "is_followed": false,
                "create_time": "2026-01-20T08:00:00Z",
                "update_time": "2026-01-20T08:00:00Z",
                "display_time": "20 Jan 2026"
            }
        ]
    }
}
```

---

## 二、获取评论列表

**URI**: `POST /joiiee/api/v1/internal/detail/comment_list`

**功能描述**: 获取帖子的评论列表，支持分页和嵌套回复

---

### 请求参数

| 字段         | 类型     | 是否必填 | 含义   | 默认值 | 备注              |
|------------|--------|------|------|--|-----------------|
| post_id    | string | 必填   | 帖子ID | - |                 |
| comment_id | string | 选填   | 评论ID | "" | 通过指定id加载更多      |
| page       | int    | 选填   | 页码   | 1 | 从1开始            |
| page_size  | int    | 选填   | 每页数量 | 20 | 最大50            |
| sort_by    | int    | 选填   | 排序方式 | 0 | 0: 最新<br/>1: 热门 |

**请求示例**:
```json
{
    "post_id": "post_001",
    "page": 1,
    "page_size": 20,
    "sort_by": 1
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | CommentListData | 数据 | None | |

---

### CommentListData

| 字段        | 类型 | 含义 | 默认值 | 备注 |
|-----------|------|------|--------|------|
| comments  | list[Comment] | 评论列表 | [] | |
| total     | int | 总数 | 0 | |
| page      | int | 当前页 | 1 | |
| page_size | int | 每页数量 | 20 | |
| has_more  | boolean | 是否有更多 | false | |

---

### Comment

| 字段            | 类型            | 含义 | 默认值 | 备注 |
|---------------|---------------|------|--------|------|
| comment_id    | string        | 评论ID | "" | |
| post_id       | string        | 帖子ID | "" | |
| user          | Author        | 评论者信息 | null | |
| text          | string        | 评论内容 | "" | |
| level         | int           | 评论层级 | 0 | 0:一级评论, 1:二级回复 |
| like_count    | int           | 点赞数 | 0 | |
| reply_count   | int           | 回复数 | 0 | |
| is_liked      | boolean       | 是否已点赞 | false | 当前用户是否点赞该评论 |
| parent_id     | string        | 父评论ID | "" | 为空表示一级评论 |
| reply_to_user | Author        | 回复的用户 | null | 回复某人时显示 |
| replies       | list[Comment] | 子回复列表 | [] | 嵌套的回复 |
| create_time   | string        | 创建时间 | "" | ISO 8601格式 |
| display_time  | string        | 展示时间 | "" | 如"30 minutes ago" |
| update_time | string | 更新时间 | "" | ISO 8601格式 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "comments": [
            {
                "comment_id": "comment_001",
                "post_id": "post_001",
                "user": {
                    "user_id": "user_sean",
                    "user_name": "Sean Clark",
                    "avatar": "https://example.com/avatar/sean.png",
                    "is_followed": false
                },
                "text": "I have no clue what this is...",
                "level": 0,
                "like_count": 12,
                "reply_count": 1,
                "is_liked": false,
                "parent_id": "",
                "reply_to_user": null,
                "replies": [
                    {
                        "comment_id": "comment_002",
                        "post_id": "post_001",
                        "user": {
                            "user_id": "user_david",
                            "user_name": "Daivd Cho",
                            "avatar": "https://example.com/avatar/david.png",
                            "is_followed": false
                        },
                        "text": "Oi agreed",
                        "level": 1,
                        "like_count": 3,
                        "reply_count": 0,
                        "is_liked": false,
                        "parent_id": "comment_001",
                        "reply_to_user": {
                            "user_id": "user_sean",
                            "user_name": "Sean Clark",
                            "avatar": "https://example.com/avatar/sean.png",
                            "is_followed": false
                        },
                        "replies": [],
                        "create_time": "2026-01-21T10:27:00Z",
                        "display_time": "3 minutes ago",
                        "update_time": "2026-01-21T10:27:00Z"
                    }
                ],
                "create_time": "2026-01-21T10:00:00Z",
                "display_time": "30 minutes ago",
                "update_time": "2026-01-21T10:00:00Z"
            },
            {
                "comment_id": "comment_003",
                "post_id": "post_001",
                "user": {
                    "user_id": "user_alessandro",
                    "user_name": "Alessandro Massimo",
                    "avatar": "https://example.com/avatar/alessandro.png",
                    "is_followed": false
                },
                "text": "Hell yes",
                "level": 0,
                "like_count": 8,
                "reply_count": 0,
                "is_liked": false,
                "parent_id": "",
                "reply_to_user": null,
                "replies": [],
                "create_time": "2026-01-19T10:30:00Z",
                "display_time": "2 days ago",
                "update_time": "2026-01-19T10:30:00Z"
            },
            {
                "comment_id": "comment_004",
                "post_id": "post_001",
                "user": {
                    "user_id": "user_adrian",
                    "user_name": "Adrian Lee",
                    "avatar": "https://example.com/avatar/adrian.png",
                    "is_followed": false
                },
                "text": "?What?",
                "level": 0,
                "like_count": 2,
                "reply_count": 0,
                "is_liked": false,
                "parent_id": "",
                "reply_to_user": null,
                "replies": [],
                "create_time": "2026-01-21T07:30:00Z",
                "display_time": "3 hours ago",
                "update_time": "2026-01-21T07:30:00Z"
            },
            {
                "comment_id": "comment_005",
                "post_id": "post_001",
                "user": {
                    "user_id": "user_aidan",
                    "user_name": "Aidan Parry",
                    "avatar": "https://example.com/avatar/aidan.png",
                    "is_followed": false
                },
                "text": "Oh...Absolutely relatable, I remember when I was in Paris, I ran into this beautiful bakery, I wen in side, and guess what? They don't sell any bakery, Alcohol only!",
                "level": 0,
                "like_count": 25,
                "reply_count": 0,
                "is_liked": false,
                "parent_id": "",
                "reply_to_user": null,
                "replies": [],
                "create_time": "2026-01-21T10:00:00Z",
                "display_time": "30 minutes ago",
                "update_time": "2026-01-21T10:00:00Z"
            }
        ],
        "total": 11,
        "page": 1,
        "page_size": 20,
        "has_more": false
    }
}
```

---

## 三、发表评论

**URI**: `POST /joiiee/api/v1/internal/detail/create_comment`

**功能描述**: 对帖子发表评论或回复他人评论

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| post_id | string | 必填 | 帖子ID | - | |
| text | string | 必填 | 评论内容 | - | 最大1000字符 |
| comment_id | string | 选填 | 父评论ID | "" | 回复评论时填写 |
| level | int | 选填| 评论的层级 | 0 | |
| reply_to_user_id | string | 选填 | 回复的用户ID | "" | 回复某人时填写 |

**请求示例**:
```json
{
    "post_id": "post_001",
    "text": "Great post!",
    "comment_id": "",
    "level": 0,
    "reply_to_user_id": ""
}
```

**回复评论示例**:
```json
{
    "post_id": "post_001",
    "text": "I totally agree with you!",
    "comment_id": "comment_001",
    "level": 1,
    "reply_to_user_id": "user_sean"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | CreateCommentData | 数据 | None | |

---

### CreateCommentData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| comment_id | string | 新评论ID | "" | |
| comment | Comment | 评论详情 | null | 新创建的评论信息 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "comment_id": "comment_new_001",
        "comment": {
            "comment_id": "comment_new_001",
            "post_id": "post_001",
            "user": {
                "user_id": "current_user",
                "user_name": "CurrentUser",
                "avatar": "https://example.com/avatar/current.png",
                "is_followed": false
            },
            "text": "Great post!",
            "level": 0,
            "like_count": 0,
            "reply_count": 0,
            "is_liked": false,
            "parent_id": "",
            "reply_to_user": null,
            "replies": [],
            "create_time": "2026-01-21T10:30:00Z",
            "display_time": "Just now",
            "update_time": "2026-01-21T10:30:00Z"
        }
    }
}
```

---

## 四、删除评论

**URI**: `POST /joiiee/api/v1/internal/detail/delete_comment`

**功能描述**: 删除自己发表的评论

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| comment_id | string | 必填 | 评论ID | - | |

**请求示例**:
```json
{
    "comment_id": "comment_001"
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

## 五、获取评论回复列表

**URI**: `POST /joiiee/api/v1/internal/detail/get_comment_by_level`

**功能描述**: 获取某条评论的回复列表，用于"查看更多回复"场景

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| comment_id | string | 必填 | 父评论ID | - | |
| level | int | 选填| 评论的层级 | 0 | |
| page | int | 选填 | 页码 | 1 | 从1开始 |
| page_size | int | 选填 | 每页数量 | 20 | 最大50 |

**请求示例**:
```json
{
    "comment_id": "comment_001",
    "level": 1,
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
| data | ReplyListData | 数据 | None | |

---

### CommentListData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[Comment] | 回复列表 | [] | |
| total | int | 总数 | 0 | |
| has_more | boolean | 是否有更多 | false | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "comment_id": "comment_002",
                "post_id": "post_001",
                "user": {
                    "user_id": "user_david",
                    "user_name": "Daivd Cho",
                    "avatar": "https://example.com/avatar/david.png",
                    "is_followed": false
                },
                "text": "Oi agreed",
                "level": 1,
                "like_count": 3,
                "reply_count": 0,
                "is_liked": false,
                "parent_id": "comment_001",
                "reply_to_user": {
                    "user_id": "user_sean",
                    "user_name": "Sean Clark",
                    "avatar": "https://example.com/avatar/sean.png",
                    "is_followed": false
                },
                "replies": [],
                "create_time": "2026-01-21T10:27:00Z",
                "display_time": "3 minutes ago",
                "update_time": "2026-01-21T10:27:00Z"
            }
        ],
        "total": 1,
        "has_more": false
    }
}
```

---

## 六、错误码定义

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
| 5001 | 帖子不存在 |
| 5002 | 评论不存在 |
| 5003 | 无权删除该帖子 |
| 5004 | 无权删除该评论 |
| 5005 | 评论内容不能为空 |
| 5006 | 评论内容过长 |

---

## 七、post_type 类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | video | 视频帖子 |
| 2 | image | 图片帖子 |
| 3 | text | 纯文本帖子 |

---


## 八、sort_by 排序说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| hot | 热门 | 按热度排序（点赞数+回复数） |
| new | 最新 | 按时间倒序 |

---

**文档版本**: v1.0
**更新日期**: 2026-01-21
**编写人**: Joiiee Tech Team
