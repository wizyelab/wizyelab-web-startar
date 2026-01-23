# 首页接口设计文档

## 一、标签内容列表

**URI**: `POST /joiiee/api/v1/internal/home/tag_content_list`

**功能描述**: 获取首页标签及对应的内容列表，支持装备推荐、AI分析、高光时刻、推荐媒体等多种内容类型

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| tag_id | int | 选填 | 标签id | 0 | 0 会下发所有tag列表和第一个tag的内容 |

**请求示例**:
```json
{
    "tag_id": 0
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "正确" | |
| data | Data | 数据 | None | |

---

### Data

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| tag_list | list[Tag] | tag列表 | [] | |
| first_login | boolean | 是否第一次登录 | false | 用于判断是否展示引导页 |

---

### Tag

| 字段 | 类型 | 含义         | 默认值   | 备注 |
|------|------|------------|-------|------|
| tag_id | int | 标签id       | 0     | |
| tag_name | string | 标签名        | ""    | 如: Padel, Pickleball, Tennis |
| tag_icon | string | 标签图标       | ""    | 可选，用于展示tab图标 |
| content_list | list[Content] | 内容列表       | []    | |
 |is_selected| bool | 是否选中 | false | | 

---

### Content

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| content_id | string | 内容唯一id | "" | 用于跳转详情、埋点等 |
| logo | string | logo图片 | "" | 卡片头部图标 |
| title | string | 标题 | "" | AI风格文案，如"These rackets fit where you are right now." |
| sub_title | string | 副标题 | "" | 如"Real plays. Real moments." |
| content_type | int | 内容类型 | 0 | 0: 默认无类型, 1: 装备推荐, 2: AI分析, 3: 高光时刻, 4: 推荐媒体 |
| video | Video | 视频信息 | null | content_type=2,3,4时可能有视频 |
| cover_image | string | 封面图 | "" | 卡片封面图片 |
| action_type | int | 点击动作类型 | 0 | 0: 无动作, 1: 跳转详情页, 2: 跳转外链, 3: 跳转视频上传 |
| action_url | string | 跳转链接 | "" | 根据action_type决定跳转目标 |
| item_list | list[Item] | 内容条目 | [] | content_type=1(装备推荐)时不为空 |
|button_desc | string | 展示button的文案 | "" | 不为空的时候要展示button|

---

### Item

| 字段 | 类型           | 含义 | 默认值 | 备注 |
|------|--------------|------|--------|------|
| item_id | string       | 条目唯一id | "" | 用于跳转、埋点 |
| logo | string       | logo图片 | "" | 商品/内容缩略图 |
| title | string       | 标题 | "" | 如"Decathlon PR 500" |
| sub_title | string       | 子标题 | "" | 紧跟title，如价格区间"$50 - $80" |
| video | Video        | 视频信息 | null | 装备介绍视频 |
| desc | string       | 描述信息 | "" | 如"Minimal vibration feedback..." |
| rating | string       | 评分 | 0.0 | 商品评分，如4.7 |
---

### Video

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 视频id | "" | |
| height | int | 视频高度 | 0 | |
| width | int | 视频宽度 | 0 | |
| duration | int | 视频时长 | 0 | 单位：秒 |
| cover_url | string | 封面图 | "" | 视频封面 |
| main_url | string | 主链接 | "" | 视频播放地址 |
| back_urls | list[string] | 备用链接 | [] | 备用CDN地址 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "tag_list": [
            {
                "tag_id": 1,
                "tag_name": "Padel",
                "tag_icon": "https://example.com/icons/padel.png",
                "is_selected": true,
                "content_list": [
                    {
                        "content_id": "content_001",
                        "logo": "https://example.com/ai_logo.png",
                        "title": "These rackets fit where you are right now.",
                        "sub_title": "",
                        "content_type": 1,
                        "video": null,
                        "cover_image": "",
                        "action_type": 1,
                        "action_url": "/equipment/list",
                        "button_desc": "",
                        "item_list": [
                            {
                                "item_id": "item_001",
                                "logo": "https://example.com/decathlon_pr500.png",
                                "title": "Decathlon PR 500",
                                "sub_title": "$50 - $80",
                                "video": null,
                                "desc": "Minimal vibration feedback...",
                                "rating": "4.7"
                            },
                            {
                                "item_id": "item_002",
                                "logo": "https://example.com/wilson_optix.png",
                                "title": "Wilson Optix V1",
                                "sub_title": "$50 - $80",
                                "video": null,
                                "desc": "The sweet spot feels big or...",
                                "rating": "4.5"
                            }
                        ]
                    },
                    {
                        "content_id": "content_002",
                        "logo": "https://example.com/ai_analysis_logo.png",
                        "title": "Upload a 10s video, and get your feedback.",
                        "sub_title": "Real plays. Real moments.",
                        "content_type": 2,
                        "video": {
                            "id": "video_001",
                            "height": 1080,
                            "width": 1920,
                            "duration": 15,
                            "cover_url": "https://example.com/video_cover.png",
                            "main_url": "https://example.com/videos/ai_demo.mp4",
                            "back_urls": [
                                "https://cdn1.example.com/videos/ai_demo.mp4"
                            ]
                        },
                        "cover_image": "https://example.com/ai_analysis_cover.png",
                        "action_type": 3,
                        "action_url": "/upload/video",
                        "button_desc": "Upload New Video",
                        "item_list": []
                    },
                    {
                        "content_id": "content_003",
                        "logo": "https://example.com/highlight_logo.png",
                        "title": "This week's highlights",
                        "sub_title": "",
                        "content_type": 3,
                        "video": {
                            "id": "video_002",
                            "height": 1080,
                            "width": 1920,
                            "duration": 60,
                            "cover_url": "https://example.com/highlight_cover.png",
                            "main_url": "https://example.com/videos/highlight.mp4",
                            "back_urls": []
                        },
                        "cover_image": "https://example.com/highlight_cover.png",
                        "action_type": 1,
                        "action_url": "/highlight/detail/content_003",
                        "button_desc": "Post",
                        "item_list": []
                    },
                    {
                        "content_id": "content_004",
                        "logo": "https://example.com/media_logo.png",
                        "title": "Trending on YouTube",
                        "sub_title": "",
                        "content_type": 4,
                        "video": {
                            "id": "video_003",
                            "height": 720,
                            "width": 1280,
                            "duration": 120,
                            "cover_url": "https://example.com/youtube_cover.png",
                            "main_url": "https://example.com/videos/trending.mp4",
                            "back_urls": []
                        },
                        "cover_image": "https://example.com/trending_cover.png",
                        "action_type": 2,
                        "action_url": "https://youtube.com/watch?v=xxx",
                        "button_desc": "",
                        "item_list": []
                    }
                ]
            },
            {
                "tag_id": 2,
                "tag_name": "Pickleball",
                "tag_icon": "https://example.com/icons/pickleball.png",
                "is_selected": false,
                "content_list": []
            },
            {
                "tag_id": 3,
                "tag_name": "Tennis",
                "tag_icon": "https://example.com/icons/tennis.png",
                "content_list": []
            }
        ],
        "first_login": false
    }
}
```

---

## 二、广场Feed

**URI**: `POST /joiiee/api/v1/internal/home/feed`

**功能描述**: 获取广场的个性化Feed流，包含用户发布的图片、视频、文本内容

---

### 请求参数

| 字段        | 类型     | 是否必填 | 含义   | 默认值 | 备注         |
|-----------|--------|------|------|-----|------------|
| post_id   | string | 选填   | 帖子id | 0   | 作为加载更多的游标  |
| page      | int    | 选填   | 页码   | 1   | 从1开始       |
| page_size | int    | 选填   | 每页数量 | 20  | 最大50       |

**请求示例**:
```json
{
    "post_id": "xxxxxxxx",
    "page": 1,
    "page_size": 20
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "正确" | |
| data | FeedData | 数据 | None | |

---

### FeedData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[Post] | Feed列表 | [] | |
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

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "id": "feed_001",
                "post_type": 1,
                "title": "I'm so excited",
                "description": "Great match today!",
                "content": "Had an amazing paddle session this morning...",
                "thumbnail_url": "https://example.com/thumb_001.png",
                "img_urls": [
                    "https://example.com/videos/feed_001.mp4"
                ],
                "video": {
                    "id": "video_feed_001",
                    "height": 1920,
                    "width": 1080,
                    "duration": 30,
                    "cover_url": "https://example.com/thumb_001.png",
                    "main_url": "https://example.com/videos/feed_001.mp4",
                    "back_urls": []
                },
                "author": {
                    "user_id": "user_001",
                    "user_name": "JohnDoe",
                    "avatar": "https://example.com/avatar_001.png",
                    "is_followed": false
                },
                "like_count": 128,
                "comment_count": 32,
                "share_count": 8,
                "is_liked": false,
                "is_collected": false,
                "create_time": "2026-01-20T10:30:00Z",
                "update_time": "2026-01-20T10:30:00Z",
                "display_time": "3 days ago"
            },
            {
                "id": "feed_002",
                "post_type": 2,
                "title": "New racket arrived!",
                "description": "Finally got my Wilson Optix V1",
                "content": "So happy with this purchase...",
                "thumbnail_url": "https://example.com/thumb_002.png",
                "img_urls": [
                    "https://example.com/images/feed_002_1.png",
                    "https://example.com/images/feed_002_2.png"
                ],
                "video": null,
                "author": {
                    "user_id": "user_002",
                    "user_name": "JaneSmith",
                    "avatar": "https://example.com/avatar_002.png",
                    "is_followed": true
                },
                "like_count": 256,
                "comment_count": 48,
                "share_count": 12,
                "is_liked": true,
                "is_collected": false,
                "create_time": "2026-01-19T15:20:00Z",
                "update_time": "2026-01-19T15:20:00Z", 
                "display_time": "3 days ago"

            },
            {
                "id": "feed_003",
                "post_type": 3,
                "title": "Tips for beginners",
                "description": "",
                "content": "Here are some tips I wish I knew when I started playing paddle...",
                "thumbnail_url": "",
                "img_urls": [],
                "video": null,
                "author": {
                    "user_id": "user_003",
                    "user_name": "PaddlePro",
                    "avatar": "https://example.com/avatar_003.png",
                    "is_followed": false
                },
                "like_count": 89,
                "comment_count": 15,
                "share_count": 5,
                "is_liked": false,
                "is_collected": true,
                "create_time": "2026-01-18T09:00:00Z",
                "update_time": "2026-01-18T09:00:00Z", 
                "display_time": "3 days ago"

            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "has_more": true
    }
}
```

---

## 四、用户行为

**URI**: `POST /joiiee/api/v1/internal/home/user/action`

**功能描述**: 用户点赞、收藏、分享等行为

---

### 请求参数

| 字段          | 类型     | 是否必填 | 含义 | 默认值 | 备注                                                         |
|-------------|--------|------|------|-----|------------------------------------------------------------|
| comment_id  | string | 选填   | 评论ID  | -   | 评论id和内容id 二选一                                              |
| post_id     | string | 选填   | 内容ID | -   |                                                            |
| action_type | int    | 必填   | 行为类型 | 0   | 0: view, 1:like, 2:unlike, 3:collect, 4:uncollect, 5:share |

**请求示例**:
```json
{
    "post_id": "feed_001",
  
    "action_type": 1
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | ActionData | 数据 | None | |

---

### ActionData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| action_type | int | 行为类型 | 0 | 1:like, 2:unlike, 3:collect, 4:uncollect, 5:share, 6:view |
| is_active | boolean | 当前状态 | false | true表示已点赞/收藏 |
| count | int | 更新后数量 | 0 | 如点赞后的总点赞数 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "action_type": 1,
        "is_active": true,
        "count": 129
    }
}
```

---

## 五、生成分享链接

**URI**: `POST /joiiee/api/v1/internal/home/share/generate_link`

**功能描述**: 生成内容的H5分享链接或DeepLink

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| post_id | string | 必填 | 内容ID | - | |
| share_type | string | 选填 | 分享类型 | "h5" | h5: H5链接, deeplink: 深度链接 |

**请求示例**:
```json
{
    "post_id": "feed_001",
    "share_type": "h5"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | ShareData | 数据 | None | |

---

### ShareData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| share_url | string | 分享链接 | "" | H5或DeepLink链接 |
| share_text | string | 分享文案 | "" | 分享时的默认文案 |
| share_image | string | 分享图片 | "" | 分享缩略图URL |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "share_url": "https://joiiee.com/share/feed_001?t=abc123",
        "share_text": "I'm so excited - Great match today!",
        "share_image": "https://example.com/thumb_001.png"
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
| 3001 | 内容不存在 |
| 3002 | 标签不存在 |
| 3003 | 操作过于频繁 |

---

## 七、content_type 类型说明

| 类型值 | 类型名称 | 说明 | UI展示 |
|--------|----------|------|--------|
| 0 | 默认无类型 | 通用内容 | 标准卡片 |
| 1 | 装备推荐 | AI推荐的装备列表 | 横向滚动商品卡片，含评分、价格 |
| 2 | AI分析 | 视频分析引导 | 视频上传引导卡片，含示例视频 |
| 3 | 高光时刻 | 精彩视频集锦 | 视频卡片，可播放 |
| 4 | 推荐媒体 | 推荐的外部媒体内容 | 视频/图文卡片，点击跳转外链 |

---

**文档版本**: v1.0
**更新日期**: 2026-01-21
**编写人**: Joiiee Tech Team
