# Chat 消息增强设计方案

## 一、需求概述

在现有 `send_message` 接口基础上，新增以下能力：

1. **Suggested Prompts（推荐提示词）** - AI 输出后给用户的快捷跟进提示
2. **Thinking（思考过程）** - 展示 AI 的推理/思考过程

---

## 二、设计目标

| 目标 | 说明 |
|------|------|
| 提升用户体验 | 降低用户输入门槛，引导对话深入 |
| 增强可解释性 | 让用户理解 AI 的推理过程，建立信任 |
| 保持简洁 | 数据结构兼容现有设计，渐进式增强 |
| 灵活可控 | 支持按需开启/关闭功能 |

---

## 三、功能设计

### 3.1 Suggested Prompts（推荐提示词）

#### 3.1.1 功能说明

AI 回复消息后，基于对话上下文生成 2-4 个相关的快捷提问/跟进建议，用户可一键点击继续对话。

**应用场景**：
- 装备推荐后："对比其他品牌"、"查看用户评价"、"了解价格区间"
- 视频分析后："分析我的正手"、"看专业选手示范"、"获取训练计划"
- 通用对话："展开说说"、"还有其他选择吗"、"帮我总结一下"

#### 3.1.2 数据结构设计

```python
class SuggestedPrompt(BaseModel):
    """推荐提示词"""

    id: str = Field(default="", description="提示词ID")
    text: str = Field(default="", description="提示词文本，如'对比其他品牌'")
    prompt_type: int = Field(default=0, description="提示词类型: 0-通用, 1-追问, 2-深入, 3-切换话题")
    icon: str = Field(default="", description="图标标识，可选")


class SuggestedPromptsData(BaseModel):
    """推荐提示词响应数据"""

    session_id: str = Field(default="", description="会话ID")
    message_id: str = Field(default="", description="关联的消息ID")
    prompts: List[SuggestedPrompt] = Field(default_factory=list, description="提示词列表，2-4个")
    expire_at: str = Field(default="", description="过期时间，过期后不再展示")
```

#### 3.1.3 API 设计

**方案 A：集成到 send_message 响应中（推荐）**

在 `MessageItem` 中新增 `suggested_prompts` 字段：

```python
class MessageItem(BaseModel):
    # ... 现有字段 ...

    # 新增字段
    suggested_prompts: List[SuggestedPrompt] = Field(
        default_factory=list,
        description="推荐的跟进提示词，仅 AI 消息有值"
    )
```

**方案 B：独立接口（适用于异步生成场景）**

```
POST /joiiee/api/v1/internal/chat/get_suggested_prompts
```

**请求参数**：
| 字段 | 类型 | 是否必填 | 含义 |
|------|------|----------|------|
| session_id | string | 必填 | 会话ID |
| message_id | string | 必填 | 消息ID |
| count | int | 选填 | 期望数量，默认3，最大5 |

**返回**：
```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "session_id": "session_001",
        "message_id": "msg_002",
        "prompts": [
            {
                "id": "sp_001",
                "text": "对比其他品牌",
                "prompt_type": 1,
                "icon": "compare"
            },
            {
                "id": "sp_002",
                "text": "查看用户评价",
                "prompt_type": 2,
                "icon": "review"
            },
            {
                "id": "sp_003",
                "text": "了解价格区间",
                "prompt_type": 1,
                "icon": "price"
            }
        ],
        "expire_at": "2026-01-21T11:30:00Z"
    }
}
```

#### 3.1.4 生成策略

| 策略 | 说明 |
|------|------|
| 上下文感知 | 基于当前对话内容生成相关提示 |
| 场景适配 | 根据 message_style 生成不同类型的提示 |
| 多样性 | 覆盖追问、深入、切换等不同方向 |
| 简洁性 | 每个提示词不超过 15 个字符 |

**prompt_type 类型说明**：

| 类型值 | 类型名称 | 说明 | 示例 |
|--------|----------|------|------|
| 0 | general | 通用提示 | "帮我总结一下" |
| 1 | follow_up | 追问/补充 | "还有其他选择吗" |
| 2 | deep_dive | 深入了解 | "展开说说这个功能" |
| 3 | switch_topic | 切换话题 | "推荐一下球鞋" |

---

### 3.2 Thinking（思考过程）

#### 3.2.1 功能说明

展示 AI 生成回复前的推理过程，增强回答的可解释性和用户信任感。

**应用场景**：
- 装备推荐：展示"分析用户水平 → 筛选合适价位 → 匹配功能需求 → 综合推荐"的推理链
- 视频分析：展示"识别动作类型 → 提取关键帧 → 对比标准姿势 → 生成建议"的分析流程
- 复杂问答：展示检索和整合信息的过程

#### 3.2.2 数据结构设计

```python
class ThinkingStep(BaseModel):
    """思考步骤"""

    step_id: str = Field(default="", description="步骤ID")
    step_order: int = Field(default=0, description="步骤顺序，从1开始")
    title: str = Field(default="", description="步骤标题，如'分析用户需求'")
    content: str = Field(default="", description="步骤详细内容")
    step_type: int = Field(default=0, description="步骤类型: 0-分析, 1-检索, 2-推理, 3-生成, 4-验证")
    duration_ms: int = Field(default=0, description="该步骤耗时(毫秒)")
    status: int = Field(default=3, description="步骤状态: 1-pending, 2-processing, 3-completed")
    video: Optional[Video] = Field(default=None, description="步骤相关视频，如视频分析时的关键片段")
    img_urls: List[str] = Field(default_factory=list, description="步骤相关图片列表，如动作对比截图、骨架分析图")


class Thinking(BaseModel):
    """思考过程"""

    thinking_id: str = Field(default="", description="思考过程ID")
    message_id: str = Field(default="", description="关联的消息ID")
    summary: str = Field(default="", description="思考过程摘要，如'正在分析您的需求...'")
    steps: List[ThinkingStep] = Field(default_factory=list, description="思考步骤列表")
    total_duration_ms: int = Field(default=0, description="总耗时(毫秒)")
    is_expanded: bool = Field(default=False, description="是否默认展开")
```

#### 3.2.3 ThinkingStep 字段说明

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| step_id | string | 步骤ID | "" | |
| step_order | int | 步骤顺序 | 0 | 从1开始 |
| title | string | 步骤标题 | "" | 如"分析用户需求" |
| content | string | 步骤详细内容 | "" | |
| step_type | int | 步骤类型 | 0 | 见下方类型说明 |
| duration_ms | int | 步骤耗时 | 0 | 毫秒 |
| status | int | 步骤状态 | 3 | 1-pending, 2-processing, 3-completed |
| video | Video | 相关视频 | null | 视频分析场景使用 |
| img_urls | list[string] | 相关图片列表 | [] | 动作截图、骨架图等 |

#### 3.2.4 Video 结构（复用现有定义）

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| id | string | 视频ID | "" | |
| height | int | 视频高度 | 0 | |
| width | int | 视频宽度 | 0 | |
| duration | int | 视频时长 | 0 | 单位：秒 |
| cover_url | string | 封面图 | "" | |
| main_url | string | 主链接 | "" | 视频播放地址 |
| back_urls | list[string] | 备用链接 | [] | 备用CDN地址 |
```

#### 3.2.5 集成到 MessageItem

在 `MessageItem` 中新增 `thinking` 字段：

```python
class MessageItem(BaseModel):
    # ... 现有字段 ...

    # 新增字段
    thinking: Optional[Thinking] = Field(
        default=None,
        description="AI思考过程，仅 AI 消息可能有值"
    )
```

#### 3.2.6 step_type 类型说明

| 类型值 | 类型名称 | 说明 | 示例 |
|--------|----------|------|------|
| 0 | analyze | 分析理解 | "理解您想要一款控制型球拍" |
| 1 | retrieve | 信息检索 | "从装备库中筛选符合条件的产品" |
| 2 | reason | 推理判断 | "根据您的水平推荐中高端产品" |
| 3 | generate | 内容生成 | "整合信息生成推荐列表" |
| 4 | verify | 验证确认 | "确认推荐结果的准确性" |

#### 3.2.7 展示形式

**折叠态（默认）**：
```
🤔 思考中... (3步)
```

**展开态**：
```
🤔 思考过程

1. 分析用户需求
   理解您正在寻找一款适合中级选手的控制型球拍

2. 检索产品库
   从 1,234 款球拍中筛选出 15 款符合条件的产品

3. 综合推荐
   根据性价比和用户评价，最终推荐 3 款产品

⏱️ 总耗时: 1.2秒
```

---

## 四、完整 MessageItem 结构（增强后）

```python
class MessageItem(BaseModel):
    """消息详情（增强版）"""

    # ========== 基础字段（已有）==========
    message_id: str = Field(default="", description="消息ID")
    session_id: str = Field(default="", description="会话ID")
    role: int = Field(default=0, description="角色: 1-user, 2-assistant, 3-system")
    content: str = Field(default="", description="消息内容")
    message_type: int = Field(default=3, description="消息类型: 1-video, 2-image, 3-text, 4-voice")
    message_style: int = Field(default=0, description="消息样式: 0-chat, 1-equipment, 2-analysis, 3-highlight, 4-media")
    attachments: List[Attachment] = Field(default_factory=list, description="附件列表")
    cards: List[Card] = Field(default_factory=list, description="卡片列表")
    generation_status: int = Field(default=3, description="生成状态: 1-pending, 2-generating, 3-completed, 4-failed, 5-stopped")
    create_time: str = Field(default="", description="创建时间")
    display_time: str = Field(default="", description="展示时间")
    media_reference: List[MediaReference] = Field(default_factory=list, description="参考媒体源")
    summary: str = Field(default="", description="总结")
    component: Optional[Component] = Field(default=None, description="交互组件")

    # ========== 新增字段 ==========
    thinking: Optional[Thinking] = Field(
        default=None,
        description="AI思考过程，仅 role=2(assistant) 时可能有值"
    )
    suggested_prompts: List[SuggestedPrompt] = Field(
        default_factory=list,
        description="推荐的跟进提示词，仅 role=2(assistant) 且为最后一条消息时有值"
    )
```

---

## 五、send_message 响应示例（增强后）

```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "user_message": {
            "message_id": "msg_001",
            "session_id": "session_001",
            "role": 1,
            "content": "推荐一款适合中级选手的网球拍",
            "message_type": 3,
            "message_style": 0,
            "attachments": [],
            "cards": [],
            "generation_status": 3,
            "create_time": "2026-01-21T10:30:00Z",
            "display_time": "2026-01-21T10:30:00Z",
            "thinking": null,
            "suggested_prompts": []
        },
        "ai_message": {
            "message_id": "msg_002",
            "session_id": "session_001",
            "role": 2,
            "content": "根据您的中级水平，我推荐以下几款网球拍：",
            "message_type": 3,
            "message_style": 1,
            "attachments": [],
            "cards": [
                {
                    "card_type": 1,
                    "title": "推荐球拍",
                    "equipments": [
                        {
                            "id": "equip_001",
                            "name": "Wilson Clash 100",
                            "brand": "Wilson",
                            "price": "$249",
                            "description": "控制与力量兼具，适合进阶选手"
                        }
                    ]
                }
            ],
            "generation_status": 3,
            "create_time": "2026-01-21T10:30:02Z",
            "display_time": "2026-01-21T10:30:02Z",
            "thinking": {
                "thinking_id": "think_001",
                "message_id": "msg_002",
                "summary": "已完成需求分析和产品匹配",
                "steps": [
                    {
                        "step_id": "step_001",
                        "step_order": 1,
                        "title": "分析用户需求",
                        "content": "识别到您是中级选手，需要一款提升控制力的球拍",
                        "step_type": 0,
                        "duration_ms": 120,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    },
                    {
                        "step_id": "step_002",
                        "step_order": 2,
                        "title": "检索产品库",
                        "content": "从 856 款网球拍中筛选出 12 款适合中级选手的产品",
                        "step_type": 1,
                        "duration_ms": 350,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    },
                    {
                        "step_id": "step_003",
                        "step_order": 3,
                        "title": "综合推荐",
                        "content": "根据用户评价、性价比和专业评测，推荐 3 款最佳选择",
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
                    "text": "对比这几款的区别",
                    "prompt_type": 2,
                    "icon": "compare"
                },
                {
                    "id": "sp_002",
                    "text": "查看用户真实评价",
                    "prompt_type": 2,
                    "icon": "review"
                },
                {
                    "id": "sp_003",
                    "text": "有更便宜的选择吗",
                    "prompt_type": 1,
                    "icon": "price"
                },
                {
                    "id": "sp_004",
                    "text": "顺便推荐网球鞋",
                    "prompt_type": 3,
                    "icon": "shoe"
                }
            ]
        },
        "session_updated": true
    }
}
```

**视频分析场景示例（含 video 和 img_urls）**:
```json
{
    "code": 0,
    "message": "正确",
    "data": {
        "user_message": {
            "message_id": "msg_005",
            "session_id": "session_002",
            "role": 1,
            "content": "帮我分析一下这个正手动作",
            "message_type": 1,
            "message_style": 2,
            "attachments": [
                {
                    "media_type": 1,
                    "url": "https://example.com/user_video.mp4",
                    "extra": {}
                }
            ],
            "cards": [],
            "generation_status": 3,
            "create_time": "2026-01-21T14:00:00Z",
            "display_time": "2026-01-21T14:00:00Z",
            "thinking": null,
            "suggested_prompts": []
        },
        "ai_message": {
            "message_id": "msg_006",
            "session_id": "session_002",
            "role": 2,
            "content": "您的正手动作整体不错，但挥拍轨迹和击球点可以优化：",
            "message_type": 3,
            "message_style": 2,
            "attachments": [],
            "cards": [
                {
                    "card_type": 2,
                    "title": "动作分析报告",
                    "summary": "整体评分: 7.5/10",
                    "img_urls": [
                        "https://example.com/analysis/skeleton_compare.png"
                    ]
                }
            ],
            "generation_status": 3,
            "create_time": "2026-01-21T14:00:05Z",
            "display_time": "2026-01-21T14:00:05Z",
            "thinking": {
                "thinking_id": "think_002",
                "message_id": "msg_006",
                "summary": "已完成视频分析和动作对比",
                "steps": [
                    {
                        "step_id": "step_001",
                        "step_order": 1,
                        "title": "视频解析",
                        "content": "提取视频关键帧，识别正手击球动作片段",
                        "step_type": 0,
                        "duration_ms": 500,
                        "status": 3,
                        "video": {
                            "id": "clip_001",
                            "height": 720,
                            "width": 1280,
                            "duration": 3,
                            "cover_url": "https://example.com/clips/forehand_cover.png",
                            "main_url": "https://example.com/clips/forehand_clip.mp4",
                            "back_urls": []
                        },
                        "img_urls": [
                            "https://example.com/frames/frame_001.png",
                            "https://example.com/frames/frame_002.png"
                        ]
                    },
                    {
                        "step_id": "step_002",
                        "step_order": 2,
                        "title": "骨架识别",
                        "content": "提取人体骨架关键点，分析挥拍轨迹",
                        "step_type": 0,
                        "duration_ms": 800,
                        "status": 3,
                        "video": null,
                        "img_urls": [
                            "https://example.com/skeleton/user_skeleton.png",
                            "https://example.com/skeleton/trajectory.png"
                        ]
                    },
                    {
                        "step_id": "step_003",
                        "step_order": 3,
                        "title": "标准动作对比",
                        "content": "与费德勒正手动作进行对比分析",
                        "step_type": 2,
                        "duration_ms": 600,
                        "status": 3,
                        "video": {
                            "id": "pro_001",
                            "height": 720,
                            "width": 1280,
                            "duration": 5,
                            "cover_url": "https://example.com/pro/federer_cover.png",
                            "main_url": "https://example.com/pro/federer_forehand.mp4",
                            "back_urls": []
                        },
                        "img_urls": [
                            "https://example.com/compare/side_by_side.png",
                            "https://example.com/compare/angle_diff.png"
                        ]
                    },
                    {
                        "step_id": "step_004",
                        "step_order": 4,
                        "title": "生成建议",
                        "content": "基于差异点生成改进建议",
                        "step_type": 3,
                        "duration_ms": 200,
                        "status": 3,
                        "video": null,
                        "img_urls": []
                    }
                ],
                "total_duration_ms": 2100,
                "is_expanded": true
            },
            "suggested_prompts": [
                {
                    "id": "sp_001",
                    "text": "分析我的反手",
                    "prompt_type": 3,
                    "icon": "backhand"
                },
                {
                    "id": "sp_002",
                    "text": "看更多专业示范",
                    "prompt_type": 2,
                    "icon": "video"
                },
                {
                    "id": "sp_003",
                    "text": "获取训练计划",
                    "prompt_type": 1,
                    "icon": "training"
                }
            ]
        },
        "session_updated": true
    }
}
```

---

## 六、流式输出支持

对于 SSE/WebSocket 流式场景，thinking 和 suggested_prompts 的输出时序：

```
1. [thinking.step_1] → 分析用户需求...
2. [thinking.step_2] → 检索产品库...
3. [thinking.step_3] → 综合推荐...
4. [content.chunk_1] → 根据您的...
5. [content.chunk_2] → 中级水平...
6. [content.chunk_N] → ...
7. [cards] → 卡片数据
8. [suggested_prompts] → 推荐提示词
9. [done] → 完成
```

**SSE 事件类型扩展**：

| event | 说明 |
|-------|------|
| thinking_start | 开始思考 |
| thinking_step | 思考步骤 |
| thinking_end | 思考结束 |
| content_chunk | 内容片段 |
| card | 卡片数据 |
| suggested_prompts | 推荐提示词 |
| done | 完成 |

---

## 七、配置与开关

在 `settings` 中添加 Chat 功能配置：

```python
class ChatFeatureConfig(BaseSettings):
    """Chat 功能配置"""

    # Thinking 功能
    thinking_enabled: bool = True          # 是否启用思考过程
    thinking_default_expanded: bool = False # 默认是否展开
    thinking_max_steps: int = 5            # 最大思考步骤数

    # Suggested Prompts 功能
    suggested_prompts_enabled: bool = True  # 是否启用推荐提示词
    suggested_prompts_count: int = 3        # 默认推荐数量
    suggested_prompts_max: int = 5          # 最大推荐数量
    suggested_prompts_ttl_minutes: int = 30 # 提示词过期时间
```

---

## 八、数据库设计（可选）

如果需要持久化 thinking 和 suggested_prompts，可以扩展消息表：

```sql
-- 在 chat_messages 表中新增字段
ALTER TABLE chat_messages ADD COLUMN thinking JSONB;
ALTER TABLE chat_messages ADD COLUMN suggested_prompts JSONB;

-- 或者创建独立表（推荐，更灵活）
CREATE TABLE chat_message_thinking (
    id VARCHAR(32) PRIMARY KEY,
    message_id VARCHAR(32) NOT NULL,
    summary VARCHAR(200),
    steps JSONB,
    total_duration_ms INT DEFAULT 0,
    create_time BIGINT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id)
);

CREATE TABLE chat_suggested_prompts (
    id VARCHAR(32) PRIMARY KEY,
    message_id VARCHAR(32) NOT NULL,
    session_id VARCHAR(32) NOT NULL,
    prompts JSONB,
    expire_at BIGINT,
    create_time BIGINT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id)
);

CREATE INDEX idx_thinking_message_id ON chat_message_thinking(message_id);
CREATE INDEX idx_prompts_message_id ON chat_suggested_prompts(message_id);
CREATE INDEX idx_prompts_session_id ON chat_suggested_prompts(session_id);
```

---

## 九、实现建议

### 9.1 Thinking 生成策略

| 场景 | 思考步骤 |
|------|----------|
| 装备推荐 | 需求分析 → 产品筛选 → 评价参考 → 综合推荐 |
| 视频分析 | 视频解析 → 动作识别 → 姿态对比 → 建议生成 |
| 通用问答 | 问题理解 → 知识检索 → 答案组织 |
| 复杂推理 | 问题拆解 → 逐步推理 → 结论整合 |

### 9.2 Suggested Prompts 生成策略

1. **基于 LLM 生成**：将对话上下文 + 最新回复传给 LLM，生成相关提示
2. **模板 + 动态填充**：预设模板库，根据 message_style 和内容动态填充
3. **混合策略**：高优先级使用模板（确保稳定），补充使用 LLM 生成（增加多样性）

### 9.3 性能优化

- Thinking：与主响应同步生成，不增加延迟
- Suggested Prompts：可异步生成，在主内容返回后补充（SSE 场景）
- 缓存：对相似问题的 thinking 模式和 prompts 进行缓存复用

---

## 十、错误码扩展

| 错误码 | 含义 |
|--------|------|
| 6009 | Thinking 生成失败 |
| 6010 | Suggested Prompts 生成失败 |
| 6011 | 消息已过期，无法获取 Suggested Prompts |

---

## 十一、版本兼容

- 新增字段均设置默认值，旧版客户端可忽略
- `thinking` 默认为 `null`
- `suggested_prompts` 默认为 `[]`
- 客户端通过版本号或 Feature Flag 控制是否渲染新功能

---

**文档版本**: v1.1
**更新日期**: 2026-01-24
**编写人**: Joiiee Tech Team
