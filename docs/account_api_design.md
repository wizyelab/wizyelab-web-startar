# Account接口设计文档

## 一、用户登录

**URI**: `POST /joiiee/api/v1/internal/account/login`

**功能描述**: 用户登录接口，支持两种登录方式：第三方登录（Google/Apple）和邮箱验证码登录

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| id_token | string | 选填 | 第三方登录Token | "" | Google/Apple OAuth后获取的Firebase ID Token |
| verify_code | string | 选填 | 邮箱验证码 | "" | 6位数字验证码 |
| email | string | 选填 | 邮箱地址 | "" | 邮箱登录时必填 |
| device_info | DeviceInfo | 选填 | 设备信息 | null | |

**注意**: 必须提供 `id_token`（第三方登录）或 `email + verify_code`（邮箱登录）其中一种方式

---

### DeviceInfo

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| device_id | string | 选填 | 设备ID | "" | 设备唯一标识 |

---

### 请求示例

**第三方登录（Google/Apple）**:
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "device_info": {
        "device_id": "00008150-000E54610C01401C"
    }
}
```

**邮箱验证码登录**:
```json
{
    "email": "user@example.com",
    "verify_code": "016782",
    "device_info": {
        "device_id": "00008150-000E54610C01401C"
    }
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 其他: 异常 |
| message | string | 返回信息 | "成功" | |
| data | LoginData | 数据 | null | |

---

### LoginData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| custom_token | string | 自定义Token | "" | 用于后续API调用的身份凭证 |
| user_info | UserInfo | 用户信息 | null | |

---

### UserInfo

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| user_id | string | 用户ID | "" | UUID格式 |
| user_name | string | 用户名 | "" | |
| avatar | string | 头像URL | "" | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "成功",
    "data": {
        "custom_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user_info": {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_name": "joy",
            "avatar": "https://example.com/avatar.png"
        }
    }
}
```

---

### 业务流程

#### 第三方登录流程

```
User          App            Web Server       Firebase       Third Party
 |             |                 |               |               |
 |--选择登录方式-->|                 |               |               |
 |             |--请求授权URL----------------------------->|
 |             |<--------------------------------------登录并授权--|
 |             |<---------------------------返回idToken--|         |
 |             |--携带idToken验证--->|                    |         |
 |             |                 |--验证idToken-->|        |         |
 |             |                 |<--用户信息----|        |         |
 |             |                 |--查询/创建用户-------->|         |
 |             |                 |<--用户信息-------------|         |
 |             |                 |--创建自定义token------>|         |
 |             |                 |<--token----------------|         |
 |             |<--返回token和用户信息--|                  |         |
 |<--验证成功---|                 |                       |         |
```

#### 邮箱验证码登录流程

```
User          App            Web Server       Firebase       Email Service
 |             |                 |               |               |
 |--邮箱登录--->|                 |               |               |
 |             |--发送验证码----->|               |               |
 |             |                 |--发送邮件-------------------->|
 |             |<--成功----------|               |               |
 |<--输入验证码-|                 |               |               |
 |--提交验证码->|                 |               |               |
 |             |--验证码验证----->|               |               |
 |             |                 |--校验-------->|               |
 |             |                 |--查询/创建用户-->|              |
 |             |                 |<--用户信息----|               |
 |             |                 |--创建token--->|               |
 |             |                 |<--token------|               |
 |             |<--返回token和用户信息--|                        |
 |<--验证成功---|                 |               |               |
```

---

## 二、发送验证码

**URI**: `POST /joiiee/api/v1/internal/account/send_verify_code`

**功能描述**: 发送邮箱验证码，用于邮箱登录验证

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| mail_url | string | 必填 | 邮箱地址 | - | 接收验证码的邮箱 |
| device_info | DeviceInfo | 选填 | 设备信息 | null | |

**请求示例**:
```json
{
    "mail_url": "user@example.com",
    "device_info": {
        "device_id": "00008150-000E54610C01401C"
    }
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 其他: 异常 |
| message | string | 返回信息 | "成功" | |
| data | object | 数据 | null | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "成功",
    "data": null
}
```

---

### 业务说明

1. **验证码生成**: 生成6位数字验证码
2. **存储**: 验证码存储到Redis，有效期10分钟
3. **发送限制**: 同一邮箱+设备10分钟内只能发送一次
4. **邮件发送**: 通过SMTP发送验证码邮件

---

## 三、用户登出

**URI**: `POST /joiiee/api/v1/internal/account/logout`

**功能描述**: 用户登出，使当前会话Token失效

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| user_id | string | 必填 | 用户ID | - | UUID格式 |
| device_info | DeviceInfo | 选填 | 设备信息 | null | |

**请求示例**:
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_info": {
        "device_id": "00008150-000E54610C01401C"
    }
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 其他: 异常 |
| message | string | 返回信息 | "成功" | |
| data | object | 数据 | null | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "成功",
    "data": null
}
```

---

### 业务说明

登出流程：
1. **获取用户信息**: 根据user_id获取用户的Firebase UID
2. **撤销Firebase Token**: 调用Firebase Admin SDK撤销用户的Refresh Token
3. **删除Redis会话**: 删除Redis中存储的会话缓存
4. **数据库会话失效**: 将数据库中该设备的会话标记为无效
5. **更新设备状态**: 将该设备标记为非活跃状态

---

## 四、错误码定义

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
| 1003 | 验证码错误 |
| 1004 | 验证码已过期 |
| 1005 | 邮件发送失败 |
| 1006 | 用户不存在 |
| 1007 | 用户已禁用 |
| 1008 | 设备信息不存在 |
| 2001 | Firebase认证错误 |
| 2002 | Firebase Token无效 |
| 2003 | Firebase用户不存在 |

---

## 五、接口依赖

### 5.1 外部服务依赖

| 服务 | 用途 | 说明 |
|------|------|------|
| Firebase Admin SDK | 身份认证 | 验证第三方登录Token、创建自定义Token、撤销Token |
| Redis | 缓存 | 存储验证码、会话信息 |
| SMTP邮件服务 | 邮件发送 | 发送验证码邮件 |

### 5.2 数据表依赖

| 数据表 | 用途 |
|--------|------|
| users | 用户信息存储 |
| user_devices | 设备信息存储 |
| user_sessions | 会话记录存储 |

---

## 六、缓存设计

### 6.1 验证码缓存

| 缓存键 | 数据类型 | TTL | 说明 |
|--------|----------|-----|------|
| `verify:{email}:{device_id}` | String | 10分钟 | 存储验证码 |

### 6.2 会话缓存

| 缓存键 | 数据类型 | TTL | 说明 |
|--------|----------|-----|------|
| `session:{user_id}` | Hash | 7天 | 存储用户会话信息 |

会话缓存数据结构：
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_id": "00008150-000E54610C01401C",
    "custom_token": "eyJhbGciOiJSUzI1NiIs...",
    "created_at": "2026-01-23T10:30:00Z"
}
```

---

## 七、安全说明

1. **Token安全**: 使用Firebase自定义Token，支持撤销机制
2. **验证码安全**: 验证码10分钟过期，验证成功后立即删除
3. **设备绑定**: 验证码与设备ID绑定，防止跨设备使用
4. **登出安全**: 登出时撤销Firebase Refresh Token，确保Token无法再被使用

---

**文档版本**: v1.0
**更新日期**: 2026-01-23
**编写人**: Joiiee Tech Team
