"""文件存储 API 路由

提供文件上传、下载、管理等接口
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.services.storage.oss_service import FileCategory, OSSService, oss_service

from app.schemas.file import *


router = APIRouter(prefix="/files", tags=["files"])

# ========================= 依赖注入 =========================

def get_oss_service() -> OSSService:
    """获取 OSS 服务实例"""
    return oss_service


# ========================= API 路由 =========================

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    prefix: str = Form(default="uploads"),
    category: Optional[str] = Form(default=None),
    service: OSSService = Depends(get_oss_service)
):
    """
    上传文件

    - **file**: 要上传的文件
    - **prefix**: 存储路径前缀，默认 "uploads"
    - **category**: 文件分类 (images/videos/audios/documents/others)，不指定则自动检测
    """
    try:
        # 解析分类
        _category = None
        if category:
            try:
                _category = FileCategory(category)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {category}. Valid values: {[c.value for c in FileCategory]}"
                )

        result = await service.upload_file(file, prefix=prefix, category=_category)

        return UploadResponse(
            key=result.key,
            url=result.url,
            filename=result.filename,
            size=result.size,
            content_type=result.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/batch", response_model=List[UploadResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    prefix: str = Form(default="uploads"),
    service: OSSService = Depends(get_oss_service)
):
    """
    批量上传文件

    - **files**: 要上传的文件列表
    - **prefix**: 存储路径前缀
    """
    results = []
    for file in files:
        try:
            result = await service.upload_file(file, prefix=prefix)
            results.append(UploadResponse(
                key=result.key,
                url=result.url,
                filename=result.filename,
                size=result.size,
                content_type=result.content_type
            ))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    return results


@router.get("/download/{key:path}")
async def download_file(
    key: str,
    filename: Optional[str] = Query(default=None, description="下载时的文件名"),
    service: OSSService = Depends(get_oss_service)
):
    """
    下载文件

    - **key**: 文件的 OSS key
    - **filename**: 下载时的文件名（可选）
    """
    try:
        # 检查文件是否存在
        if not await service.file_exists(key):
            raise HTTPException(status_code=404, detail="File not found")

        # 获取文件信息
        file_info = await service.get_file_info(key)

        # 下载文件内容
        content = await service.download_file(key)

        # 确定文件名
        _filename = filename or key.split("/")[-1]

        # 确定内容类型
        content_type = file_info.content_type if file_info else "application/octet-stream"

        # 返回流式响应
        return StreamingResponse(
            iter([content]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={_filename}",
                "Content-Length": str(len(content))
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/info/{key:path}", response_model=FileInfoResponse)
async def get_file_info(
    key: str,
    service: OSSService = Depends(get_oss_service)
):
    """
    获取文件信息

    - **key**: 文件的 OSS key
    """
    try:
        info = await service.get_file_info(key)
        if not info:
            raise HTTPException(status_code=404, detail="File not found")

        return FileInfoResponse(
            key=info.key,
            size=info.size,
            content_type=info.content_type,
            last_modified=str(info.last_modified) if info.last_modified else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@router.delete("/{key:path}", response_model=DeleteResponse)
async def delete_file(
    key: str,
    service: OSSService = Depends(get_oss_service)
):
    """
    删除文件

    - **key**: 文件的 OSS key
    """
    try:
        success = await service.delete_file(key)
        return DeleteResponse(success=success, key=key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.post("/delete/batch", response_model=BatchDeleteResponse)
async def batch_delete_files(
    request: BatchDeleteRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    批量删除文件

    - **keys**: 文件 key 列表
    """
    try:
        results = await service.delete_files(request.keys)
        return BatchDeleteResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.get("/list", response_model=List[FileInfoResponse])
async def list_files(
    prefix: str = Query(default="", description="路径前缀过滤"),
    max_keys: int = Query(default=100, le=1000, description="最大返回数量"),
    marker: str = Query(default="", description="起始位置标记"),
    service: OSSService = Depends(get_oss_service)
):
    """
    列举文件

    - **prefix**: 路径前缀过滤
    - **max_keys**: 最大返回数量（最大 1000）
    - **marker**: 起始位置标记（用于分页）
    """
    try:
        files = await service.list_files(prefix=prefix, max_keys=max_keys, marker=marker)
        return [
            FileInfoResponse(
                key=f.key,
                size=f.size,
                content_type=f.content_type,
                last_modified=str(f.last_modified) if f.last_modified else None
            )
            for f in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List files failed: {str(e)}")


@router.post("/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    request: SignedUrlRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    获取签名 URL（用于临时访问私有文件）

    - **key**: 文件的 OSS key
    - **expires**: 过期时间（秒），默认 3600
    - **for_download**: 是否用于下载（设置 Content-Disposition）
    - **filename**: 下载时的文件名
    """
    try:
        url = service.get_signed_url(
            request.key,
            expires=request.expires,
            for_download=request.for_download,
            filename=request.filename
        )
        return SignedUrlResponse(url=url, expires_in=request.expires or 3600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {str(e)}")


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    获取上传 URL（用于客户端直传）

    客户端可以使用返回的 URL 直接向 OSS 上传文件，无需经过服务器。

    - **filename**: 文件名
    - **prefix**: 存储路径前缀
    - **category**: 文件分类
    - **content_type**: 内容类型
    - **expires**: 过期时间（秒）
    """
    try:
        # 解析分类
        _category = None
        if request.category:
            try:
                _category = FileCategory(request.category)
            except ValueError:
                pass

        # 生成 key
        key = service.generate_upload_key(
            request.filename,
            prefix=request.prefix,
            category=_category
        )

        # 生成上传 URL
        upload_url = service.get_upload_url(
            key,
            expires=request.expires,
            content_type=request.content_type
        )

        return UploadUrlResponse(
            key=key,
            upload_url=upload_url,
            expires_in=request.expires or 3600
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@router.get("/exists/{key:path}")
async def check_file_exists(
    key: str,
    service: OSSService = Depends(get_oss_service)
):
    """
    检查文件是否存在

    - **key**: 文件的 OSS key
    """
    try:
        exists = await service.file_exists(key)
        return {"exists": exists, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")
