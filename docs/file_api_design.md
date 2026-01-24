# File接口设计文档

## 一、上传文件

**URI**: `POST /joiiee/api/v1/public/files/upload`

**功能描述**: 上传单个文件到OSS存储

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| file | File | 必填 | 要上传的文件 | - | multipart/form-data格式 |
| prefix | string | 选填 | 存储路径前缀 | "uploads" | |
| category | string | 选填 | 文件分类 | null | images/videos/audios/documents/others，不指定则自动检测 |

---

### 请求示例

```
POST /joiiee/api/v1/public/files/upload
Content-Type: multipart/form-data

file: (binary)
prefix: uploads
category: images
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "上传成功" | |
| data | UploadData | 数据 | null | |

---

### UploadData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| key | string | 文件OSS key | "" | 文件在OSS中的唯一标识 |
| url | string | 文件访问URL | "" | |
| filename | string | 文件名 | "" | |
| size | int | 文件大小 | 0 | 单位：字节 |
| content_type | string | 内容类型 | "" | MIME类型 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "上传成功",
    "data": {
        "key": "uploads/images/2026/01/23/abc123.jpg",
        "url": "https://oss.example.com/uploads/images/2026/01/23/abc123.jpg",
        "filename": "photo.jpg",
        "size": 102400,
        "content_type": "image/jpeg"
    }
}
```

---

## 二、批量上传文件

**URI**: `POST /joiiee/api/v1/public/files/upload/batch`

**功能描述**: 批量上传多个文件到OSS存储

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| files | File[] | 必填 | 要上传的文件列表 | - | multipart/form-data格式 |
| prefix | string | 选填 | 存储路径前缀 | "uploads" | |

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "批量上传成功" | |
| data | UploadData[] | 数据 | null | 上传结果列表 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "批量上传成功",
    "data": [
        {
            "key": "uploads/images/2026/01/23/abc123.jpg",
            "url": "https://oss.example.com/uploads/images/2026/01/23/abc123.jpg",
            "filename": "photo1.jpg",
            "size": 102400,
            "content_type": "image/jpeg"
        },
        {
            "key": "uploads/images/2026/01/23/def456.png",
            "url": "https://oss.example.com/uploads/images/2026/01/23/def456.png",
            "filename": "photo2.png",
            "size": 204800,
            "content_type": "image/png"
        }
    ]
}
```

---

## 三、下载文件

**URI**: `POST /joiiee/api/v1/public/files/download`

**功能描述**: 下载指定文件

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| key | string | 必填 | 文件的OSS key | - | |
| filename | string | 选填 | 下载时的文件名 | null | |

---

### 请求示例

```json
{
    "key": "uploads/images/2026/01/23/abc123.jpg",
    "filename": "my_photo.jpg"
}
```

---

### 返回

返回文件流（StreamingResponse），响应头包含：

| Header | 含义 |
|--------|------|
| Content-Type | 文件MIME类型 |
| Content-Disposition | attachment; filename={filename} |
| Content-Length | 文件大小 |

---

## 四、获取文件信息

**URI**: `POST /joiiee/api/v1/public/files/info`

**功能描述**: 获取指定文件的元信息

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| key | string | 必填 | 文件的OSS key | - | |

---

### 请求示例

```json
{
    "key": "uploads/images/2026/01/23/abc123.jpg"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "获取成功" | |
| data | FileInfoData | 数据 | null | |

---

### FileInfoData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| key | string | 文件OSS key | "" | |
| size | int | 文件大小 | 0 | 单位：字节 |
| content_type | string | 内容类型 | null | MIME类型 |
| last_modified | string | 最后修改时间 | null | ISO8601格式 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "key": "uploads/images/2026/01/23/abc123.jpg",
        "size": 102400,
        "content_type": "image/jpeg",
        "last_modified": "2026-01-23T10:30:00Z"
    }
}
```

---

## 五、删除文件

**URI**: `POST /joiiee/api/v1/public/files/delete`

**功能描述**: 删除指定文件

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| key | string | 必填 | 文件的OSS key | - | |

---

### 请求示例

```json
{
    "key": "uploads/images/2026/01/23/abc123.jpg"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "删除成功" | |
| data | DeleteData | 数据 | null | |

---

### DeleteData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| success | bool | 是否成功 | false | |
| key | string | 文件OSS key | "" | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "删除成功",
    "data": {
        "success": true,
        "key": "uploads/images/2026/01/23/abc123.jpg"
    }
}
```

---

## 六、批量删除文件

**URI**: `POST /joiiee/api/v1/public/files/delete/batch`

**功能描述**: 批量删除多个文件

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| keys | string[] | 必填 | 文件key列表 | - | |

---

### 请求示例

```json
{
    "keys": [
        "uploads/images/2026/01/23/abc123.jpg",
        "uploads/images/2026/01/23/def456.png"
    ]
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "批量删除成功" | |
| data | BatchDeleteData | 数据 | null | |

---

### BatchDeleteData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| results | dict | 删除结果 | {} | key: 文件key, value: 是否成功 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "批量删除成功",
    "data": {
        "results": {
            "uploads/images/2026/01/23/abc123.jpg": true,
            "uploads/images/2026/01/23/def456.png": true
        }
    }
}
```

---

## 七、列举文件

**URI**: `POST /joiiee/api/v1/public/files/list`

**功能描述**: 列举OSS中的文件

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| prefix | string | 选填 | 路径前缀过滤 | "" | |
| max_keys | int | 选填 | 最大返回数量 | 100 | 最大1000 |
| marker | string | 选填 | 起始位置标记 | "" | 用于分页 |

---

### 请求示例

```json
{
    "prefix": "uploads/images",
    "max_keys": 50,
    "marker": ""
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "获取成功" | |
| data | FileInfoData[] | 数据 | null | 文件信息列表 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "获取成功",
    "data": [
        {
            "key": "uploads/images/2026/01/23/abc123.jpg",
            "size": 102400,
            "content_type": "image/jpeg",
            "last_modified": "2026-01-23T10:30:00Z"
        },
        {
            "key": "uploads/images/2026/01/23/def456.png",
            "size": 204800,
            "content_type": "image/png",
            "last_modified": "2026-01-23T11:00:00Z"
        }
    ]
}
```

---

## 八、获取签名URL

**URI**: `POST /joiiee/api/v1/public/files/signed-url`

**功能描述**: 获取签名URL，用于临时访问私有文件

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| key | string | 必填 | 文件的OSS key | - | |
| expires | int | 选填 | 过期时间（秒） | 3600 | |
| for_download | bool | 选填 | 是否用于下载 | false | 设置Content-Disposition |
| filename | string | 选填 | 下载时的文件名 | null | |

---

### 请求示例

```json
{
    "key": "uploads/images/2026/01/23/abc123.jpg",
    "expires": 7200,
    "for_download": true,
    "filename": "my_photo.jpg"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "获取成功" | |
| data | SignedUrlData | 数据 | null | |

---

### SignedUrlData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| url | string | 签名URL | "" | |
| expires_in | int | 过期时间 | 3600 | 单位：秒 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "url": "https://oss.example.com/uploads/images/2026/01/23/abc123.jpg?OSSAccessKeyId=xxx&Expires=xxx&Signature=xxx",
        "expires_in": 7200
    }
}
```

---

## 九、获取上传URL

**URI**: `POST /joiiee/api/v1/public/files/upload-url`

**功能描述**: 获取上传URL，用于客户端直传OSS

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| filename | string | 必填 | 文件名 | - | |
| prefix | string | 选填 | 存储路径前缀 | "uploads" | |
| category | string | 选填 | 文件分类 | null | images/videos/audios/documents/others |
| content_type | string | 选填 | 内容类型 | null | MIME类型 |
| expires | int | 选填 | 过期时间（秒） | 3600 | |

---

### 请求示例

```json
{
    "filename": "photo.jpg",
    "prefix": "uploads",
    "category": "images",
    "content_type": "image/jpeg",
    "expires": 3600
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "获取成功" | |
| data | UploadUrlData | 数据 | null | |

---

### UploadUrlData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| key | string | 文件OSS key | "" | 上传后文件的key |
| upload_url | string | 上传URL | "" | 客户端直传使用 |
| expires_in | int | 过期时间 | 3600 | 单位：秒 |

---

### 返回示例

```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "key": "uploads/images/2026/01/23/abc123.jpg",
        "upload_url": "https://oss.example.com/uploads/images/2026/01/23/abc123.jpg?OSSAccessKeyId=xxx&Expires=xxx&Signature=xxx",
        "expires_in": 3600
    }
}
```

---

## 十、检查文件是否存在

**URI**: `POST /joiiee/api/v1/public/files/exists`

**功能描述**: 检查指定文件是否存在

---

### 请求参数

| 字段 | 类型 | 是否必填 | 含义 | 默认值 | 备注 |
|------|------|----------|------|--------|------|
| key | string | 必填 | 文件的OSS key | - | |

---

### 请求示例

```json
{
    "key": "uploads/images/2026/01/23/abc123.jpg"
}
```

---

### 返回

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| code | int | 状态码 | 0 | 0: 正常, 1: 异常 |
| message | string | 返回信息 | "检查成功" | |
| data | FileExistsData | 数据 | null | |

---

### FileExistsData

| 字段 | 类型 | 含义 | 默认值 | 备注 |
|------|------|------|--------|------|
| exists | bool | 是否存在 | false | |
| key | string | 文件OSS key | "" | |

---

### 返回示例

```json
{
    "code": 0,
    "message": "检查成功",
    "data": {
        "exists": true,
        "key": "uploads/images/2026/01/23/abc123.jpg"
    }
}
```

---

## 十一、错误码定义

| 错误码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 操作失败 |

---

## 十二、文件分类说明

| 分类 | 值 | 说明 |
|------|-----|------|
| 图片 | images | jpg, jpeg, png, gif, webp, svg等 |
| 视频 | videos | mp4, avi, mov, wmv, flv等 |
| 音频 | audios | mp3, wav, flac, aac等 |
| 文档 | documents | pdf, doc, docx, xls, xlsx, ppt, pptx等 |
| 其他 | others | 未分类文件 |

---

## 十三、接口依赖

### 外部服务依赖

| 服务 | 用途 | 说明 |
|------|------|------|
| 阿里云OSS | 文件存储 | 文件上传、下载、管理 |

---

**文档版本**: v1.0
**更新日期**: 2026-01-23
**编写人**: Joiiee Tech Team
