# Firebase 认证流程设计文档

## 一、为什么需要服务端验证？

### 1.1 客户端不可信原则

```
❌ 错误方式：客户端验证后直接声明"我已登录"

   攻击者可以：
   - 修改客户端代码绕过验证
   - 伪造网络请求
   - 篡改本地存储的登录状态

✅ 正确方式：服务端亲自验证 Token

   客户端 → Token → 服务端 → Firebase 服务器验证
   服务端验证 Token 的签名和有效性，确保不可伪造
```

### 1.2 为什么要转换成 Firebase ID Token？

| Token 类型 | 说明 |
|-----------|------|
| Google ID Token | 只证明"用户在 Google 登录了" |
| Apple ID Token | 只证明"用户在 Apple 登录了" |
| Firebase ID Token | 统一的身份凭证，包含用户 UID、登录方式、签名、过期时间 |

**好处**：
- **统一管理**：不管用户用 Google/Apple/邮箱登录，后端验证逻辑一致
- **用户关联**：同一用户用不同方式登录，Firebase 可以关联为同一账户
- **安全控制**：Firebase 可以禁用用户、撤销 Token 等

---

## 二、完整认证架构

### 2.1 系统角色

```
┌─────────────────────────────────────────────────────────────────────┐
│                           认证系统架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────────┐   │
│  │  用户   │     │  客户端  │     │  服务端  │     │   Firebase  │   │
│  │         │     │  (App)  │     │(Web Server)│    │   Server   │   │
│  └────┬────┘     └────┬────┘     └─────┬─────┘     └──────┬──────┘   │
│       │               │                │                  │         │
│       │   操作设备    │                │                  │         │
│       │──────────────>│                │                  │         │
│       │               │                │                  │         │
│       │               │  Firebase ID   │                  │         │
│       │               │     Token      │    验证 Token    │         │
│       │               │───────────────>│─────────────────>│         │
│       │               │                │                  │         │
│       │               │                │<─────────────────│         │
│       │               │                │   用户信息/验证结果│         │
│       │               │                │                  │         │
│       │               │<───────────────│                  │         │
│       │               │  业务 Token +   │                  │         │
│       │               │   用户信息      │                  │         │
│       │               │                │                  │         │
│  └────┴────┘     └────┴────┘     └─────┴─────┘     └──────┴──────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 各端职责

| 角色 | 职责 |
|------|------|
| **客户端** | 1. 调用第三方 SDK 获取原始 Token<br>2. 通过 Firebase SDK 转换为 Firebase ID Token<br>3. 将 Firebase ID Token 发送给服务端<br>4. 存储服务端返回的 Custom Token |
| **服务端** | 1. 验证 Firebase ID Token<br>2. 创建/查询本地用户<br>3. 生成 Custom Token<br>4. 管理用户会话 |
| **Firebase** | 1. 管理第三方登录集成<br>2. 签发和验证 ID Token<br>3. 用户身份统一管理<br>4. Token 撤销机制 |

---

## 三、认证流程详解

### 3.1 第三方登录（Google/Apple）完整流程

```
┌──────┐          ┌──────┐          ┌──────────┐          ┌──────────┐          ┌──────────┐
│ 用户 │          │ 客户端 │          │ Third Party│         │ Firebase │          │ 服务端   │
└──┬───┘          └──┬───┘          │(Google/Apple)│       │  Server  │          └────┬─────┘
   │                 │               └─────┬──────┘         └────┬─────┘               │
   │  1.点击登录      │                     │                     │                     │
   │────────────────>│                     │                     │                     │
   │                 │                     │                     │                     │
   │                 │  2.发起OAuth请求     │                     │                     │
   │                 │────────────────────>│                     │                     │
   │                 │                     │                     │                     │
   │                 │  3.用户授权登录      │                     │                     │
   │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│                     │                     │
   │                 │                     │                     │                     │
   │                 │  4.返回原始ID Token  │                     │                     │
   │                 │<────────────────────│                     │                     │
   │                 │                     │                     │                     │
   │                 │  5.signInWithCredential(原始Token)         │                     │
   │                 │────────────────────────────────────────────>│                     │
   │                 │                     │                     │                     │
   │                 │  6.返回 Firebase ID Token                  │                     │
   │                 │<────────────────────────────────────────────│                     │
   │                 │                     │                     │                     │
   │                 │  7.发送 Firebase ID Token 到服务端                               │
   │                 │──────────────────────────────────────────────────────────────────>│
   │                 │                     │                     │                     │
   │                 │                     │                     │  8.验证 ID Token    │
   │                 │                     │                     │<─────────────────────│
   │                 │                     │                     │                     │
   │                 │                     │                     │  9.返回验证结果      │
   │                 │                     │                     │─────────────────────>│
   │                 │                     │                     │                     │
   │                 │                     │                     │    10.服务端处理     │
   │                 │                     │                     │    (见下方详解)      │
   │                 │                     │                     │                     │
   │                 │  11.返回 Custom Token + 用户信息                                 │
   │                 │<──────────────────────────────────────────────────────────────────│
   │                 │                     │                     │                     │
   │  12.登录成功     │                     │                     │                     │
   │<────────────────│                     │                     │                     │
   │                 │                     │                     │                     │
```

### 3.2 客户端代码示例

#### iOS (Swift)

```swift
// 1. Google Sign-In 获取原始 Token
GIDSignIn.sharedInstance.signIn(withPresenting: viewController) { result, error in
    guard let user = result?.user,
          let idToken = user.idToken?.tokenString else { return }

    // 2. 转换为 Firebase Credential
    let credential = GoogleAuthProvider.credential(
        withIDToken: idToken,
        accessToken: user.accessToken.tokenString
    )

    // 3. 使用 Firebase SDK 登录，获取 Firebase ID Token
    Auth.auth().signIn(with: credential) { authResult, error in
        authResult?.user.getIDToken { firebaseIdToken, error in
            // 4. 发送 Firebase ID Token 到服务端
            self.loginToServer(firebaseIdToken: firebaseIdToken)
        }
    }
}
```

#### Android (Kotlin)

```kotlin
// 1. Google Sign-In 获取原始 Token
val googleIdToken = account.idToken

// 2. 转换为 Firebase Credential
val credential = GoogleAuthProvider.getCredential(googleIdToken, null)

// 3. 使用 Firebase SDK 登录
Firebase.auth.signInWithCredential(credential)
    .addOnSuccessListener { authResult ->
        // 4. 获取 Firebase ID Token
        authResult.user?.getIdToken(true)?.addOnSuccessListener { result ->
            val firebaseIdToken = result.token
            // 5. 发送到服务端
            loginToServer(firebaseIdToken)
        }
    }
```

---

## 四、服务端认证后处理流程

### 4.1 完整处理步骤

```
Firebase ID Token 验证成功后，服务端执行以下步骤：

┌─────────────────────────────────────────────────────────────────────────────┐
│                        服务端认证后处理流程                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: 验证 Token                                                         │
│  ├── 调用 Firebase Admin SDK verify_id_token()                              │
│  ├── 验证签名有效性                                                          │
│  ├── 检查过期时间                                                            │
│  └── 可选：检查 Token 是否已撤销 (check_revoked=True)                         │
│                                                                             │
│  Step 2: 提取用户信息                                                        │
│  ├── firebase_uid: Firebase 用户唯一标识                                     │
│  ├── email: 用户邮箱                                                         │
│  ├── name: 用户名称                                                          │
│  ├── picture: 头像 URL                                                       │
│  └── provider: 登录方式 (google.com / apple.com / password)                  │
│                                                                             │
│  Step 3: 用户管理                                                            │
│  ├── 查询本地用户表 (by firebase_uid)                                        │
│  ├── 如不存在 → 查询 (by email) 并关联                                       │
│  ├── 如仍不存在 → 创建新用户                                                  │
│  └── 更新用户信息 (名称、头像等)                                              │
│                                                                             │
│  Step 4: 设备管理                                                            │
│  ├── 记录设备 ID                                                             │
│  ├── 更新设备活跃状态                                                        │
│  └── 支持多设备登录管理                                                       │
│                                                                             │
│  Step 5: 会话管理                                                            │
│  ├── 生成 Custom Token (可选)                                                │
│  ├── 创建会话记录                                                            │
│  ├── 存储到 Redis (快速验证)                                                 │
│  └── 持久化到数据库 (审计追踪)                                                │
│                                                                             │
│  Step 6: 返回响应                                                            │
│  ├── custom_token: 后续 API 调用凭证                                         │
│  └── user_info: 用户基本信息                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 代码实现对照

对应 `app/services/account_service.py` 中的 `verify_third_party_login` 方法：

```python
async def verify_third_party_login(self, id_token: str, device_id: str):
    """
    服务端认证后处理流程
    """
    # Step 1: 验证 Firebase ID Token
    decoded_token, error_type = await firebase_service.verify_id_token(id_token)
    if not decoded_token:
        return ErrorCode.FIREBASE_TOKEN_INVALID, "无效的登录凭证", None

    # Step 2: 提取用户信息
    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    name = decoded_token.get("name")
    picture = decoded_token.get("picture")
    provider = decoded_token.get("firebase", {}).get("sign_in_provider")

    # Step 3: 用户管理 - 查询或创建用户
    user = await self._get_or_create_user(
        firebase_uid=firebase_uid,
        email=email,
        user_name=name,
        avatar=picture,
        login_provider=provider,
    )

    # Step 4: 设备管理
    await self._update_device(user.user_id, device_id)

    # Step 5: 会话管理 - 创建 Custom Token 和会话
    custom_token = await firebase_service.create_custom_token(user.user_id, {...})
    await self._create_session(user.user_id, device_id, custom_token)

    # Step 6: 返回响应
    return ErrorCode.SUCCESS, "成功", LoginData(...)
```

---

## 五、Token 策略设计

### 5.1 Token 类型说明

| Token 类型 | 签发方 | 有效期 | 用途 |
|-----------|--------|--------|------|
| **Google/Apple ID Token** | Google/Apple | ~1小时 | 第三方登录凭证，仅用于换取 Firebase Token |
| **Firebase ID Token** | Firebase | 1小时 | 服务端验证用户身份 |
| **Firebase Refresh Token** | Firebase | 长期 | 刷新 ID Token，撤销后用户需重新登录 |
| **Custom Token** | 服务端 | 自定义(7天) | 后续 API 调用的身份凭证 |

### 5.2 Token 生命周期

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Token 生命周期                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  登录时:                                                                 │
│  ┌────────────┐    ┌─────────────────┐    ┌──────────────┐              │
│  │ 原始 Token │───>│ Firebase ID Token│───>│ Custom Token │              │
│  │ (一次性)   │    │ (1小时有效)      │    │ (7天有效)    │              │
│  └────────────┘    └─────────────────┘    └──────────────┘              │
│                                                                         │
│  正常使用:                                                               │
│  ┌──────────────┐    ┌────────────┐                                     │
│  │ Custom Token │───>│ 访问业务API │                                     │
│  └──────────────┘    └────────────┘                                     │
│                                                                         │
│  Token 过期:                                                             │
│  ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐        │
│  │ Firebase Refresh │───>│ 新 Firebase ID  │───>│ 新 Custom    │        │
│  │ Token            │    │ Token           │    │ Token        │        │
│  └──────────────────┘    └─────────────────┘    └──────────────┘        │
│                                                                         │
│  登出时:                                                                 │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ 1. 撤销 Firebase Refresh Token (核心安全措施)                    │     │
│  │ 2. 删除 Redis 会话缓存                                          │     │
│  │ 3. 数据库会话标记为无效                                          │     │
│  │ 4. 更新设备状态为非活跃                                          │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Token 刷新策略

```python
# 客户端 Token 刷新逻辑
class TokenManager:
    async def get_valid_token(self):
        """获取有效的 Token"""

        # 1. 检查 Custom Token 是否即将过期
        if self.is_token_expiring_soon(self.custom_token):
            # 2. 使用 Firebase SDK 刷新 ID Token
            firebase_id_token = await self.refresh_firebase_token()

            # 3. 调用服务端刷新接口
            new_custom_token = await self.refresh_custom_token(firebase_id_token)

            self.custom_token = new_custom_token

        return self.custom_token
```

---

## 六、安全考虑

### 6.1 安全威胁与防护

| 威胁 | 防护措施 |
|------|---------|
| **Token 泄露** | 1. HTTPS 传输加密<br>2. Token 短期有效<br>3. 支持 Token 撤销 |
| **重放攻击** | 1. Token 包含时间戳<br>2. 服务端验证过期时间 |
| **伪造 Token** | 1. Firebase 签名验证<br>2. 服务端二次验证 |
| **会话劫持** | 1. 设备 ID 绑定<br>2. 异常登录检测 |
| **跨设备攻击** | 1. 验证码与设备绑定<br>2. 多设备会话管理 |

### 6.2 登出安全

```
登出时的安全措施：

┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  1. 撤销 Firebase Refresh Token                                     │
│     ├── 调用 auth.revoke_refresh_tokens(uid)                        │
│     ├── 所有现有会话被终止                                           │
│     └── 无法从现有 Refresh Token 获取新 ID Token                     │
│                                                                     │
│  2. 删除服务端会话                                                   │
│     ├── 删除 Redis 会话缓存                                         │
│     └── 数据库会话标记为无效                                         │
│                                                                     │
│  3. 验证时检查撤销状态                                               │
│     └── verify_id_token(check_revoked=True)                        │
│         可以立即检测已撤销的 Token                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 安全配置清单

```yaml
# Firebase 安全配置
firebase:
  # 必须配置服务账号密钥
  credentials_path: "/path/to/service-account.json"
  project_id: "your-project-id"

# Token 配置
token:
  # Custom Token 有效期
  custom_token_ttl: 604800  # 7天 (秒)
  # 会话有效期
  session_ttl: 604800  # 7天 (秒)

# 安全配置
security:
  # 是否检查 Token 撤销状态
  check_token_revoked: true
  # 是否绑定设备
  bind_device: true
```

---

## 七、错误处理

### 7.1 错误码定义

| 错误码 | 错误类型 | 说明 | 客户端处理 |
|--------|---------|------|-----------|
| 2001 | FIREBASE_TOKEN_INVALID | Token 无效 | 重新登录 |
| 2002 | FIREBASE_TOKEN_EXPIRED | Token 已过期 | 刷新 Token 或重新登录 |
| 2003 | FIREBASE_TOKEN_REVOKED | Token 已撤销 | 重新登录 |
| 2004 | FIREBASE_USER_DISABLED | 用户已禁用 | 显示禁用提示 |
| 2005 | FIREBASE_SERVICE_ERROR | Firebase 服务错误 | 稍后重试 |

### 7.2 错误处理流程

```python
# 服务端错误处理
async def verify_id_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        return decoded_token, ""

    except auth.InvalidIdTokenError:
        # Token 格式错误或签名无效
        return None, "invalid"

    except auth.ExpiredIdTokenError:
        # Token 已过期，客户端需要刷新
        return None, "expired"

    except auth.RevokedIdTokenError:
        # Token 已被撤销（用户已登出）
        return None, "revoked"

    except auth.UserDisabledError:
        # 用户账户已被禁用
        return None, "disabled"

    except Exception:
        # 其他错误
        return None, "error"
```

---

## 八、监控与审计

### 8.1 日志记录

```python
# 关键操作日志
logger.info(f"登录成功: user_id={user_id}, provider={provider}, device={device_id}")
logger.info(f"登出成功: user_id={user_id}, device={device_id}")
logger.warning(f"Token验证失败: error={error_type}, token_prefix={token[:20]}...")
logger.warning(f"异常登录检测: user_id={user_id}, new_device={device_id}")
```

### 8.2 监控指标

| 指标 | 说明 |
|------|------|
| 登录成功率 | 登录成功次数 / 登录尝试次数 |
| Token 验证失败率 | 验证失败次数 / 验证总次数 |
| 平均登录耗时 | 登录请求的平均响应时间 |
| 活跃会话数 | 当前有效的会话数量 |

---

## 九、流程图汇总

### 9.1 完整认证流程图

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              Firebase 完整认证流程                                  │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│   ┌─────────┐                                                                      │
│   │  开始   │                                                                      │
│   └────┬────┘                                                                      │
│        │                                                                           │
│        ▼                                                                           │
│   ┌─────────────────┐                                                              │
│   │ 用户选择登录方式 │                                                              │
│   └────────┬────────┘                                                              │
│            │                                                                       │
│     ┌──────┴──────┐                                                                │
│     │             │                                                                │
│     ▼             ▼                                                                │
│  ┌──────────┐  ┌──────────┐                                                        │
│  │第三方登录│  │邮箱验证码│                                                        │
│  │Google/App│  │  登录    │                                                        │
│  └────┬─────┘  └────┬─────┘                                                        │
│       │             │                                                              │
│       ▼             ▼                                                              │
│  ┌──────────────┐  ┌──────────────┐                                                │
│  │获取原始Token │  │发送验证码邮件│                                                │
│  └──────┬───────┘  └──────┬───────┘                                                │
│         │                 │                                                        │
│         ▼                 ▼                                                        │
│  ┌──────────────────┐  ┌─────────────┐                                             │
│  │Firebase SDK 转换 │  │用户输入验证码│                                             │
│  │获取 Firebase ID  │  └──────┬──────┘                                             │
│  │Token             │         │                                                    │
│  └────────┬─────────┘         ▼                                                    │
│           │            ┌─────────────┐                                             │
│           │            │服务端验证码 │                                             │
│           │            │校验         │                                             │
│           │            └──────┬──────┘                                             │
│           │                   │                                                    │
│           └───────┬───────────┘                                                    │
│                   │                                                                │
│                   ▼                                                                │
│          ┌────────────────────┐                                                    │
│          │ 服务端验证 Token   │                                                    │
│          │ verify_id_token()  │                                                    │
│          └─────────┬──────────┘                                                    │
│                    │                                                               │
│           ┌────────┴────────┐                                                      │
│           │                 │                                                      │
│           ▼                 ▼                                                      │
│     ┌──────────┐      ┌──────────┐                                                 │
│     │ 验证成功 │      │ 验证失败 │                                                 │
│     └────┬─────┘      └────┬─────┘                                                 │
│          │                 │                                                       │
│          ▼                 ▼                                                       │
│  ┌───────────────┐   ┌───────────────┐                                             │
│  │查询/创建用户  │   │返回错误信息   │                                             │
│  └───────┬───────┘   └───────────────┘                                             │
│          │                                                                         │
│          ▼                                                                         │
│  ┌───────────────┐                                                                 │
│  │更新设备信息   │                                                                 │
│  └───────┬───────┘                                                                 │
│          │                                                                         │
│          ▼                                                                         │
│  ┌───────────────┐                                                                 │
│  │创建Custom Token│                                                                │
│  └───────┬───────┘                                                                 │
│          │                                                                         │
│          ▼                                                                         │
│  ┌───────────────┐                                                                 │
│  │创建会话记录   │                                                                 │
│  │Redis + 数据库 │                                                                 │
│  └───────┬───────┘                                                                 │
│          │                                                                         │
│          ▼                                                                         │
│  ┌───────────────┐                                                                 │
│  │返回 Token 和  │                                                                 │
│  │用户信息       │                                                                 │
│  └───────┬───────┘                                                                 │
│          │                                                                         │
│          ▼                                                                         │
│     ┌─────────┐                                                                    │
│     │  结束   │                                                                    │
│     └─────────┘                                                                    │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 十、附录

### 10.1 相关代码文件

| 文件 | 说明 |
|------|------|
| `app/services/firebase_service.py` | Firebase 服务封装 |
| `app/services/account_service.py` | 账户服务逻辑 |
| `app/api/v1/internal/routers/account.py` | 账户 API 路由 |
| `app/schemas/account.py` | 请求/响应数据结构 |

### 10.2 参考文档

- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [Firebase ID Token 验证](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [Firebase 自定义 Token](https://firebase.google.com/docs/auth/admin/create-custom-tokens)

---

**文档版本**: v1.0
**创建日期**: 2026-01-24
**编写人**: Joiiee Tech Team
