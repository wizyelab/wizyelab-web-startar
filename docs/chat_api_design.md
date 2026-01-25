# 聊天接口设计文档

## 一、创建会话

**URI**: `POST /joiiee/api/v1/internal/chat/create_session`

**功能描述**: 创建新的AI对话会话，支持不同类型的会话场景

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| title | string | 选填 | 会话标题 | "" | 最大200字符 |
| context | object | 选填 | 初始上下文 | null | 传入相关上下文信息 |

**请求示例**:
```json
{
    "title": "",
    "context": null
}
```

**带上下文的请求示例**:
```json
{
    "title": "Racket Recommendation",
    "context": {
        "sport_type": "padel",
        "skill_level": "intermediate"
    }
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "正确" | |
| data | SessionData | 数据 | None | |

---

### SessionData

| 字段          | 类型 | 含义 | 默认值 | 备注 |
|-------------|------|------|--------|------|
| user_id     | string | 用户ID |"" | |
| session_id  | string | 会话ID | "" | |
| title       | string | 会话标题 | "" | |
| create_time | string | 创建时间 | "" | ISO 8601格式 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "user_id": "xxxxx",
        "session_id": "session_001",
        "title": "",
        "create_time": "2026-01-21T10:30:00Z"
    }
}
```

---

## 二、获取会话列表

**URI**: `POST /joiiee/api/v1/internal/chat/session_list`

**功能描述**: 获取用户的会话列表

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| page | int | 选填 | 页码 | 1 | 从1开始 |
| page_size | int | 选填 | 每页数量 | 20 | 最大50 |

**请求示例**:
```json
{
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
| data | SessionListData | 数据 | None | |

---

### SessionListData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[SessionItem] | 会话列表 | [] | |
| user_id     | string | 用户ID |"" | |
| total | int | 总数 | 0 | |
| page | int | 当前页 | 1 | |
| page_size | int | 每页数量 | 20 | |
| has_more | boolean | 是否有更多 | false | |

---

### SessionItem

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| session_id | string | 会话ID | "" | |
| session_type | int | 会话类型 | 1 | |
| title | string | 会话标题 | "" | |
| message_count | int | 消息数量 | 0 | |
| is_pinned | boolean | 是否置顶 | false | |
| last_message_at | string | 最后消息时间 | "" | |
| last_message_preview | string | 最后消息预览 | "" | 最多50字符 |
| create_time | string | 创建时间 | "" | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "session_id": "session_001",
                "session_type": 1,
                "title": "Equipment Chat",
                "message_count": 15,
                "is_pinned": false,
                "last_message_at": "2026-01-21T10:30:00Z",
                "last_message_preview": "I can buy myself flower, write my name in the sand.",
                "create_time": "2026-01-20T08:00:00Z"
            },
            {
                "session_id": "session_002",
                "session_type": 3,
                "title": "Video Analysis",
                "message_count": 8,
                "is_pinned": true,
                "last_message_at": "2026-01-21T09:00:00Z",
                "last_message_preview": "Your backhand stroke mostly come from...",
                "create_time": "2026-01-19T14:00:00Z"
            }
        ],
        "user_id": "xxxx",
        "total": 10,
        "page": 1,
        "page_size": 20,
        "has_more": false
    }
}
```

---

## 三、更新会话

**URI**: `POST /joiiee/api/v1/internal/chat/update_session`

**功能描述**: 更新会话信息，如标题、置顶状态等

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| session_id | string | 必填 | 会话ID | - | |
| title | string | 选填 | 会话标题 | - | 最大200字符 |
| is_pinned | boolean | 选填 | 是否置顶 | - | |
| status | int | 选填 | 状态 | - | 1:active, 2:archived |

**请求示例**:
```json
{
    "session_id": "session_001",
    "title": "My Equipment Chat",
    "is_pinned": true
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

## 四、删除会话

**URI**: `POST /joiiee/api/v1/internal/chat/delete_session`

**功能描述**: 删除对话会话

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| session_id | string | 必填 | 会话ID | - | |

**请求示例**:
```json
{
    "session_id": "session_001"
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

## 五、发送消息

**URI**: `POST /joiiee/api/v1/internal/chat/send_message`

**功能描述**: 发送消息并获取AI回复，支持文本、图片、语音等多种消息类型

---

### 请求参数

| 字段           | 类型           | 是否必填 | 含义 | 默认值 | 备注                                  |
|--------------|--------------|------|------|--------|-------------------------------------|
| session_id   | string       | 选填   | 会话ID | - | 第一次开启会话的session时不填/ 拿已有消息的seesion_id|
| source       | Source       | 选填 | 会话来源| null | 只有首页的content卡片开启的会话才填入|
| content      | string       | 必填   | 消息内容 | - | 最大10000字符                           |
| message_type | int          | 选填   | 消息类型 | 1 | 1:video, 2:image, 3:text, 4:voice   |
| attachments  | list[Attachment] | 选填   | 附件列表 | [] | 图片、视频等附件                            |

### Source

| 字段              | 类型     | 含义           | 默认值 | 备注                                            |
|-----------------|--------|--------------|-----|-----------------------------------------------|
| home_tag_id     | int    | 首页tag_id     | 0   |                                               |
| home_content_id | string | 首页content_id | ""  |                                               |
| source_type     | int    | 会话来源         | 0   | 0: chat对话, 1: 装备推荐, 2: AI分析, 3: 高光时刻, 4: 推荐媒体 |

**请求示例**:
```json
{
    "session_id": "session_001",
    "source": {
        "home_tag_id": 1,
        "home_content_id": "1",
        "source_type": 0
    },
    "content": "I can buy myself flower, write my name in the sand.",
    "message_type": 3,
    "attachments": []
}
```

**带图片的请求示例**:
```json
{
    "session_id": "session_001",
    "source": {
        "home_tag_id": 1,
        "home_content_id": "1",
        "source_type": 0
    },
    "content": "What racket is this?",
    "message_type": 2,
    "attachments": [
        {
            "media_type": 2,
            "url": "https://example.com/images/racket.png",
            "extra": {}
        }
    ]
}
```

---

### Attachment

| 字段         | 类型     | 含义    | 默认值 | 备注                        |
|------------|--------|-------|----|---------------------------|
| media_type | int    | 附件类型  | 0  | 1:video, 2:image, 3:voice |
| url        | string | 附件URL | "" |                           |
| extra      | dict   | 附件数据  | {} | 扩展数据                      |

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | MessageResponseData | 数据 | None | |

---

### MessageResponseData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| user_message | MessageItem | 用户消息 | null | |
| ai_message | MessageItem | AI回复消息 | null | |
| session_updated | boolean | 会话是否更新 | false | 如标题自动生成 |

---

### MessageItem

| 字段                | 类型 | 含义  | 默认值 | 备注 |
|-------------------|-----|-----|--------|------|
| message_id        | string | 消息ID | "" | |
| session_id        | string | 会话ID | "" | |
| role              | int | 角色  | 0 | 1:user, 2:assistant, 3:system |
| content           | string | 消息内容或卡片文本消息 | "" | |
| message_type      | int | 消息类型 | 1 |1:video, 2:image, 3:text, 4:voice |
| message_style     | int| 消息样式 | 0 ｜ 0: chat对话, 1: 装备推荐, 2: AI分析, 3: 高光时刻, 4: 推荐媒体 |
| attachments       | list[Attachment] | 附件列表 | [] | |
| cards             | list[Card] | 卡片列表 | [] | AI回复中的卡片组件 |
| generation_status | int | 生成状态 | 3 | 1:pending, 2:generating, 3:completed, 4:failed, 5:stopped |
| create_time       | string | 创建时间 | "" | |
| display_time      | string | 展示时间 | "" | |
| media_reference   | list[MediaReference] | 参考媒体源 | [] | |
| summary           | string      | 总结  | ""                     |                            |
| component         | Component | 组件  |  null | 有才展示|
| thinking          | Thinking | 思考过程 | null | 仅AI消息有值，展示AI推理过程 |
| suggested_prompts | list[SuggestedPrompt] | 推荐提示词 | [] | 仅AI消息有值，用于引导用户跟进提问 |

___

### SuggestedPrompt

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 提示词ID | "" | |
| text | string | 提示词文本 | "" | 如"对比其他品牌"，不超过15字符 |
| prompt_type | int | 提示词类型 | 0 | 0:通用, 1:追问, 2:深入, 3:切换话题 |
| icon | string | 图标标识 | "" | 可选，如"compare"、"price" |

___

### Thinking

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| thinking_id | string | 思考过程ID | "" | |
| message_id | string | 关联的消息ID | "" | |
| summary | string | 思考摘要 | "" | 如"已完成需求分析和产品匹配" |
| steps | list[ThinkingStep] | 思考步骤列表 | [] | |
| total_duration_ms | int | 总耗时 | 0 | 毫秒 |
| is_expanded | boolean | 是否默认展开 | false | |

___

### ThinkingStep

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| step_id | string | 步骤ID | "" | |
| step_order | int | 步骤顺序 | 0 | 从1开始 |
| title | string | 步骤标题 | "" | 如"分析用户需求" |
| content | string | 步骤详细内容 | "" | |
| step_type | int | 步骤类型 | 0 | 0:分析, 1:检索, 2:推理, 3:生成, 4:验证 |
| duration_ms | int | 步骤耗时 | 0 | 毫秒 |
| status | int | 步骤状态 | 3 | 1:pending, 2:processing, 3:completed |
| video | Video | 相关视频 | null | 视频分析场景使用 |
| img_urls | list[string] | 相关图片列表 | [] | 动作截图、骨架图等 |

___

### Component
| 字段                | 类型 | 含义        | 默认值 | 备注 |
|-------------------|-----|-----------|--------|------|
| text              |  string | 文本消息      | "" | |
| button_left_desc  | string | 左button描述 | "" | |
| button_right_desc | string | 右button描述 | "" | |



### MediaReference
| 字段   | 类型 | 含义   | 默认值 | 备注 |
|------|-----|------|--------|------|
| logo | string | logo | "" | |
| desc | string | 描述   | "" | |

---

### Card

| 字段                | 类型          | 含义       | 默认值                    | 备注                         |
|-------------------|-------------|----------|------------------------|----------------------------|
| card_type         | int         | 卡片类型     | 0                      | 1:装备, 2:ai分析, 3:分析报告, 4:高光时刻 |
| title             | string      | 卡片标题     | ""                     |                            |
| equipments        | list[Equipment] | 装备列表     | null                   | 装备商品                       |
| social_media_data | SocialMediaData | 媒体数据  ｜ null |                        |
| button_desc       | string      | 按钮文案 ｜ "" | 当不为空展示                 |
| video             | Video       | 视频信息     | null                   | ai 分析和 高光的视频               |
| summary           | string      | 总结       | ""                     |                            |
| channel           | Channel     | 第二视频信息   | ai分析的频道，learn from pro |
| img_urls | list[string] | 图片列表 | 分析报告的图片                |

___

### Equipment

| 字段          | 类型           | 含义      | 默认值 | 备注 |
|-------------|--------------|---------|--------|------|
| id          | string       | 装备ID    | "" | |
| name        | string       | 装备名称    | "" | 如"Decathlon" |
| brand       | string       | 品牌      | "" | |
| model       | string       | 型号      | "" | |
| img_urls    | list[string] | 图片URL列表 | "" | |
| price       | string       | 价格      | "" | 如"$25 - $29" |
| description | string       | 描述      | "" | |
| tags        | list[string] | 标签      | [] | 如["Find Cheapest"] |
___

### SocialMediaData

| 字段      | 类型              | 含义         | 默认值 | 备注                 |
|---------|-----------------|------------|-----|--------------------|
| youtube | list[channel]   | Youtube 视频 | []  |  |
| amazon  | list[channel]    | Amazon 评论  | []  |                    |
| reddit  | list[channel] | Reddit  评论 | []  |

___

### Channel

| 字段           | 类型     | 含义     | 默认值               | 备注              |
|--------------|--------|--------|-------------------|-----------------|
| video        | Video  | 主视频信息  | null              |                 |
| title        | string | 卡片标题   | ""                |                 |
| import_time  | string | 重要视频时间 | ""                | "00:52 - 01:23" |
| summary      | string      | 视频总结   | ""                     |                 |
| author       | Author | 作者信息   |  null |                 |
| rating       | string       | 评分     | 0.0 | 商品评分，如4.7 |
| display_time | string        | 展示时间   | "" | 如"30 minutes ago" |
| user_comment | string | 用户评论   | "" | |
| digg_desc    | string | 点赞数文案 | ""| |

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
        "user_message": {
            "message_id": "msg_001",
            "session_id": "session_001",
            "role": 1,
            "content": "I can buy myself flower, write my name in the sand.",
            "message_type": 3,
            "message_style": 0,
            "attachments": [],
            "cards": [],
            "generation_status": 3,
            "create_time": "2026-01-21T10:30:00Z",
            "display_time": "2026-01-21T10:30:00Z",
            "media_reference": [],
            "summary": "",
            "component": null,
            "thinking": null,
            "suggested_prompts": []
        },
        "ai_message": {
            "message_id": "msg_002",
            "session_id": "session_001",
            "role": 2,
            "content": "I can take myself dancing, and I can hold my own hand.",
            "message_type": 3,
            "message_style": 0,
            "attachments": [],
            "cards": [],
            "generation_status": 3,
            "create_time": "2026-01-21T10:30:01Z",
            "display_time": "2026-01-21T10:30:01Z",
            "media_reference": [],
            "summary": "",
            "component": null,
            "thinking": null,
            "suggested_prompts": [
                {
                    "id": "sp_001",
                    "text": "Tell me more",
                    "prompt_type": 2,
                    "icon": ""
                },
                {
                    "id": "sp_002",
                    "text": "What else can you do?",
                    "prompt_type": 1,
                    "icon": ""
                }
            ]
        },
        "session_updated": false
    }
}
```

**带卡片的AI回复示例**:
```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "user_message": {
            "message_id": "msg_003",
            "session_id": "session_001",
            "role": 1,
            "content": "Recommend me a padel racket",
            "message_type": 3,
            "message_style": 0,
            "attachments": [],
            "cards": [],
            "generation_status": 3,
            "create_time": "2026-01-21T11:00:00Z",
            "display_time": "2026-01-21T11:00:00Z",
            "media_reference": [],
            "summary": "",
            "component": null,
            "thinking": null,
            "suggested_prompts": []
        },
        "ai_message": {
            "message_id": "msg_004",
            "session_id": "session_001",
            "role": 2,
            "content": "Based on your skill level, here are some recommended rackets:",
            "message_type": 3,
            "message_style": 1,
            "attachments": [],
            "cards": [
                {
                    "card_type": 1,
                    "title": "Recommended Rackets",
                    "equipments": [
                        {
                            "id": "equip_001",
                            "name": "Bullpadel Vertex 03",
                            "brand": "Bullpadel",
                            "model": "Vertex 03",
                            "img_urls": ["https://example.com/images/vertex03.png"],
                            "price": "$199 - $249",
                            "description": "Professional level racket with excellent control",
                            "tags": ["Pro Level", "Control"]
                        }
                    ],
                    "social_media_data": null,
                    "button_desc": "View Details",
                    "video": null,
                    "summary": "",
                    "channel": null,
                    "img_urls": []
                }
            ],
            "generation_status": 3,
            "create_time": "2026-01-21T11:00:02Z",
            "display_time": "2026-01-21T11:00:02Z",
            "media_reference": [
                {
                    "logo": "https://example.com/youtube_logo.png",
                    "desc": "YouTube Reviews"
                }
            ],
            "summary": "Recommended 1 racket based on your preferences",
            "component": {
                "text": "Would you like more recommendations?",
                "button_left_desc": "Yes",
                "button_right_desc": "No"
            },
            "thinking": {
                "thinking_id": "think_001",
                "message_id": "msg_004",
                "summary": "Analyzed your needs and matched products",
                "steps": [
                    {
                        "step_id": "step_001",
                        "step_order": 1,
                        "title": "Analyzing requirements",
                        "content": "Identified your skill level and preference for control",
                        "step_type": 0,
                        "duration_ms": 120,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    },
                    {
                        "step_id": "step_002",
                        "step_order": 2,
                        "title": "Searching products",
                        "content": "Filtered 12 rackets from 856 products for intermediate players",
                        "step_type": 1,
                        "duration_ms": 350,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    },
                    {
                        "step_id": "step_003",
                        "step_order": 3,
                        "title": "Generating recommendations",
                        "content": "Selected top 3 based on reviews and value",
                        "step_type": 2,
                        "duration_ms": 180,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    }
                ],
                "total_duration_ms": 650,
                "is_expanded": false
            },
            "suggested_prompts": [
                {
                    "id": "sp_001",
                    "text": "Compare with others",
                    "prompt_type": 2,
                    "icon": "compare"
                },
                {
                    "id": "sp_002",
                    "text": "Show user reviews",
                    "prompt_type": 2,
                    "icon": "review"
                },
                {
                    "id": "sp_003",
                    "text": "Any cheaper options?",
                    "prompt_type": 1,
                    "icon": "price"
                },
                {
                    "id": "sp_004",
                    "text": "Recommend shoes too",
                    "prompt_type": 3,
                    "icon": "shoe"
                }
            ]
        },
        "session_updated": true
    }
}
```

---

## 六、获取消息列表

**URI**: `POST /joiiee/api/v1/internal/chat/message_list`

**功能描述**: 获取会话的消息列表，支持向前加载更多历史消息

---

### 请求参数

| 字段         | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------------|------|----------|------|--------|------|
| session_id | string | 必填 | 会话ID | - | |
| message_id | string | 选填 | 消息ID | "" | 获取此消息之前的消息 |
| limit      | int | 选填 | 数量限制 | 50 | 最大100 |

**请求示例**:
```json
{
    "session_id": "session_001",
    "message_id": "",
    "limit": 50
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | |
| message | string | 返回信息 | "正确" | |
| data | MessageListData | 数据 | None | |

---

### MessageListData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| items | list[MessageItem] | 消息列表 | [] | 按时间正序排列 |
| has_more | boolean | 是否有更多 | false | 是否还有更早的消息 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "items": [
            {
                "message_id": "msg_001",
                "session_id": "session_001",
                "role": 1,
                "content": "I can buy myself flower, write my name in the sand.",
                "message_type": 3,
                "message_style": 0,
                "attachments": [],
                "cards": [],
                "generation_status": 3,
                "create_time": "2026-01-21T10:30:00Z",
                "display_time": "2026-01-21T10:30:00Z",
                "media_reference": [],
                "summary": "",
                "component": null,
                "thinking": null,
                "suggested_prompts": []
            },
            {
                "message_id": "msg_002",
                "session_id": "session_001",
                "role": 2,
                "content": "I can take myself dancing, and I can hold my own hand.",
                "message_type": 3,
                "message_style": 0,
                "attachments": [],
                "cards": [],
                "generation_status": 3,
                "create_time": "2026-01-21T10:30:01Z",
                "display_time": "2026-01-21T10:30:01Z",
                "media_reference": [],
                "summary": "",
                "component": null,
                "thinking": null,
                "suggested_prompts": [
                    {
                        "id": "sp_001",
                        "text": "Tell me more",
                        "prompt_type": 2,
                        "icon": ""
                    },
                    {
                        "id": "sp_002",
                        "text": "What else?",
                        "prompt_type": 1,
                        "icon": ""
                    }
                ]
            }
        ],
        "has_more": false
    }
}
```

---

## 七、停止生成

**URI**: `POST /joiiee/api/v1/internal/chat/stop_word`

**功能描述**: 停止AI消息生成

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|------|------|--------|------|
| session_id | string | 必填   | 会话ID | - | |
| message_id | string | 选填   | 消息ID | - | 正在生成的消息ID |

**请求示例**:
```json
{
    "session_id": "session_001",
    "message_id": "msg_002"
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

## 八、错误码定义

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
| 6001 | 会话不存在 |
| 6002 | 消息不存在 |
| 6003 | 会话已结束 |
| 6004 | 消息生成中 |
| 6005 | 视频分析失败 |
| 6006 | 视频格式不支持 |
| 6007 | 视频时长超限 |
| 6008 | 分析结果不存在 |

---

## 九、session_type 类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | general | 通用对话 |
| 2 | equipment | 装备推荐 |
| 3 | analysis | 视频分析 |
| 4 | training | 训练指导 |

---

## 十、message_type 消息类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | video | 视频消息 |
| 2 | image | 图片消息 |
| 3 | text | 文本消息 |
| 4 | voice | 语音消息 |

---

## 十一、role 角色类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | user | 用户 |
| 2 | assistant | AI助手 |
| 3 | system | 系统 |

---

## 十二、generation_status 生成状态说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | pending | 等待中 |
| 2 | generating | 生成中 |
| 3 | completed | 已完成 |
| 4 | failed | 失败 |
| 5 | stopped | 已停止 |

---

## 十三、card_type 卡片类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | equipment | 装备推荐卡片 |
| 2 | analysis | 分析结果卡片 |
| 3 | report | 分析报告卡片 |
| 4 | highlight | 高光时刻卡片 |

---

## 十四、action_type 动作类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 0 | auto | 自动识别 |
| 1 | forehand | 正手 |
| 2 | backhand | 反手 |
| 3 | serve | 发球 |
| 4 | volley | 截击 |
| 5 | footwork | 步伐 |

---

## 十五、source_type 会话来源类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 0 | chat | chat对话 |
| 1 | equipment | 装备推荐 |
| 2 | ai_analysis | AI分析 |
| 3 | highlight | 高光时刻 |
| 4 | recommend_media | 推荐媒体 |

---

## 十六、media_type 附件类型说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | video | 视频 |
| 2 | image | 图片 |
| 3 | voice | 语音 |

---

## 十七、session_status 会话状态说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | active | 活跃 |
| 2 | archived | 已归档 |

---

## 十八、message_style 消息样式说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 0 | chat | chat对话 |
| 1 | equipment | 装备推荐 |
| 2 | ai_analysis | AI分析 |
| 3 | highlight | 高光时刻 |
| 4 | recommend_media | 推荐媒体 |

---

## 十九、prompt_type 提示词类型说明

| 类型值 | 类型名称 | 说明 | 示例 |
|--------|----------|------|------|
| 0 | general | 通用提示 | "帮我总结一下" |
| 1 | follow_up | 追问/补充 | "有更便宜的吗" |
| 2 | deep_dive | 深入了解 | "详细对比一下" |
| 3 | switch_topic | 切换话题 | "推荐一下球鞋" |

---

## 二十、step_type 思考步骤类型说明

| 类型值 | 类型名称 | 说明 | 示例 |
|--------|----------|------|------|
| 0 | analyze | 分析理解 | "理解您想要一款控制型球拍" |
| 1 | retrieve | 信息检索 | "从装备库中筛选符合条件的产品" |
| 2 | reason | 推理判断 | "根据您的水平推荐中高端产品" |
| 3 | generate | 内容生成 | "整合信息生成推荐列表" |
| 4 | verify | 验证确认 | "确认推荐结果的准确性" |

---

## 二十一、thinking_step_status 思考步骤状态说明

| 类型值 | 类型名称 | 说明 |
|--------|----------|------|
| 1 | pending | 等待中 |
| 2 | processing | 处理中 |
| 3 | completed | 已完成 |

---

**文档版本**: v1.3
**更新日期**: 2026-01-24
**编写人**: Joiiee Tech Team
