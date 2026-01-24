"""文件存储 API 路由

提供文件上传、下载、管理等接口
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.services.storage.oss_service import FileCategory, OSSService, oss_service

from app.schemas.common import BaseResponse
from app.schemas.file import (
    UploadData, FileInfoData, SignedUrlData, UploadUrlData,
    DeleteData, BatchDeleteData, FileExistsData,
    FileKeyRequest, DownloadRequest, FileListRequest,
    SignedUrlRequest, UploadUrlRequest, BatchDeleteRequest
)
from typing import Optional, List


router = APIRouter(prefix="/files", tags=["files"])

# ========================= 依赖注入 =========================

def get_oss_service() -> OSSService:
    """获取 OSS 服务实例"""
    return oss_service


# ========================= API 路由 =========================

@router.post("/upload", response_model=BaseResponse[UploadData])
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
                return BaseResponse(
                    code=1,
                    message=f"Invalid category: {category}. Valid values: {[c.value for c in FileCategory]}",
                    data=None
                )

        result = await service.upload_file(file, prefix=prefix, category=_category)

        return BaseResponse(
            code=0,
            message="上传成功",
            data=UploadData(
                key=result.key,
                url=result.url,
                filename=result.filename,
                size=result.size,
                content_type=result.content_type
            )
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Upload failed: {str(e)}",
            data=None
        )


@router.post("/upload/batch", response_model=BaseResponse[List[UploadData]])
async def upload_files(
    files: list[UploadFile] = File(...),
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
            results.append(UploadData(
                key=result.key,
                url=result.url,
                filename=result.filename,
                size=result.size,
                content_type=result.content_type
            ))
        except Exception as e:
            return BaseResponse(
                code=1,
                message=f"Failed to upload {file.filename}: {str(e)}",
                data=None
            )
    return BaseResponse(
        code=0,
        message="批量上传成功",
        data=results
    )


@router.post("/download")
async def download_file(
    request: DownloadRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    下载文件

    - **key**: 文件的 OSS key
    - **filename**: 下载时的文件名（可选）
    """
    try:
        # 检查文件是否存在
        if not await service.file_exists(request.key):
            raise HTTPException(status_code=404, detail="File not found")

        # 获取文件信息
        file_info = await service.get_file_info(request.key)

        # 下载文件内容
        content = await service.download_file(request.key)

        # 确定文件名
        _filename = request.filename or request.key.split("/")[-1]

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


@router.post("/info", response_model=BaseResponse[FileInfoData])
async def get_file_info(
    request: FileKeyRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    获取文件信息

    - **key**: 文件的 OSS key
    """
    try:
        info = await service.get_file_info(request.key)
        if not info:
            return BaseResponse(
                code=1,
                message="File not found",
                data=None
            )

        return BaseResponse(
            code=0,
            message="获取成功",
            data=FileInfoData(
                key=info.key,
                size=info.size,
                content_type=info.content_type,
                last_modified=str(info.last_modified) if info.last_modified else None
            )
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Failed to get file info: {str(e)}",
            data=None
        )


@router.post("/delete", response_model=BaseResponse[DeleteData])
async def delete_file(
    request: FileKeyRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    删除文件

    - **key**: 文件的 OSS key
    """
    try:
        success = await service.delete_file(request.key)
        return BaseResponse(
            code=0,
            message="删除成功",
            data=DeleteData(success=success, key=request.key)
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Delete failed: {str(e)}",
            data=None
        )


@router.post("/delete/batch", response_model=BaseResponse[BatchDeleteData])
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
        return BaseResponse(
            code=0,
            message="批量删除成功",
            data=BatchDeleteData(results=results)
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Batch delete failed: {str(e)}",
            data=None
        )


@router.post("/list", response_model=BaseResponse[List[FileInfoData]])
async def list_files(
    request: FileListRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    列举文件

    - **prefix**: 路径前缀过滤
    - **max_keys**: 最大返回数量（最大 1000）
    - **marker**: 起始位置标记（用于分页）
    """
    try:
        files = await service.list_files(prefix=request.prefix, max_keys=request.max_keys, marker=request.marker)
        file_list = [
            FileInfoData(
                key=f.key,
                size=f.size,
                content_type=f.content_type,
                last_modified=str(f.last_modified) if f.last_modified else None
            )
            for f in files
        ]
        return BaseResponse(
            code=0,
            message="获取成功",
            data=file_list
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"List files failed: {str(e)}",
            data=None
        )


@router.post("/signed-url", response_model=BaseResponse[SignedUrlData])
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
        return BaseResponse(
            code=0,
            message="获取成功",
            data=SignedUrlData(url=url, expires_in=request.expires or 3600)
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Failed to generate signed URL: {str(e)}",
            data=None
        )


@router.post("/upload-url", response_model=BaseResponse[UploadUrlData])
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

        return BaseResponse(
            code=0,
            message="获取成功",
            data=UploadUrlData(
                key=key,
                upload_url=upload_url,
                expires_in=request.expires or 3600
            )
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Failed to generate upload URL: {str(e)}",
            data=None
        )


@router.post("/exists", response_model=BaseResponse[FileExistsData])
async def check_file_exists(
    request: FileKeyRequest,
    service: OSSService = Depends(get_oss_service)
):
    """
    检查文件是否存在

    - **key**: 文件的 OSS key
    """
    try:
        exists = await service.file_exists(request.key)
        return BaseResponse(
            code=0,
            message="检查成功",
            data=FileExistsData(exists=exists, key=request.key)
        )
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"Check failed: {str(e)}",
            data=None
        )
