"""文件存储 API 路由（公开，无需认证）

提供简单的文件上传、下载、管理等接口
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.storage.oss_service import FileCategory, OSSService, oss_service
from app.schemas.common import BaseResponse
from app.core.error_codes import ErrorCode
from app.schemas.file import (
    FileInfoData, SignedUrlData, UploadUrlData,
    DeleteData, BatchDeleteData, FileExistsData,
    FileKeyRequest, DownloadRequest, FileListRequest,
    SignedUrlRequest, UploadUrlRequest, BatchDeleteRequest,
    MediaUploadResponse,
)
from typing import Optional, List


router = APIRouter(prefix="/files", tags=["files"])


# ========================= 依赖注入 =========================

def get_oss_service() -> OSSService:
    """获取 OSS 服务实例"""
    return oss_service


# ========================= API 路由 =========================

@router.post("/upload", response_model=BaseResponse[MediaUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    prefix: str = Form(default="uploads"),
    category: Optional[str] = Form(default=None),
    service: OSSService = Depends(get_oss_service)
):
    """
    上传文件（简单版，无 MD5 去重）

    - **file**: 要上传的文件
    - **prefix**: 存储路径前缀，默认 "uploads"
    - **category**: 文件分类
    """
    try:
        _category = None
        if category:
            try:
                _category = FileCategory(category)
            except ValueError:
                return BaseResponse(code=ErrorCode.INVALID_FILE_CATEGORY, data=None)

        result = await service.upload_file(file, prefix=prefix, category=_category)

        import time
        return BaseResponse(
            code=ErrorCode.SUCCESS,
            message="上传成功",
            data=MediaUploadResponse(
                file_id="",
                file_type=0,
                file_name=result.filename,
                file_size=result.size,
                mime_type=result.content_type,
                original_uri=result.key,
                url=result.url,
                download_url=result.url,
                create_time=int(time.time() * 1000),
            )
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=f"Upload failed: {str(e)}", data=None)


@router.post("/upload/batch", response_model=BaseResponse[List[MediaUploadResponse]])
async def upload_files(
    files: List[UploadFile] = File(...),
    prefix: str = Form(default="uploads"),
    service: OSSService = Depends(get_oss_service)
):
    """批量上传文件"""
    import time
    results = []
    for file in files:
        try:
            result = await service.upload_file(file, prefix=prefix)
            results.append(MediaUploadResponse(
                file_id="",
                file_type=0,
                file_name=result.filename,
                file_size=result.size,
                mime_type=result.content_type,
                original_uri=result.key,
                url=result.url,
                download_url=result.url,
                create_time=int(time.time() * 1000),
            ))
        except Exception as e:
            return BaseResponse(
                code=ErrorCode.GENERAL_ERROR,
                message=f"Failed to upload {file.filename}: {str(e)}", data=None
            )
    return BaseResponse(code=ErrorCode.SUCCESS, message="批量上传成功", data=results)


@router.post("/download")
async def download_file(
    request: DownloadRequest,
    service: OSSService = Depends(get_oss_service)
):
    """下载文件"""
    try:
        if not await service.file_exists(request.key):
            raise HTTPException(status_code=404, detail="File not found")

        file_info = await service.get_file_info(request.key)
        content = await service.download_file(request.key)
        _filename = request.filename or request.key.split("/")[-1]
        content_type = file_info.content_type if file_info else "application/octet-stream"

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
    """获取文件信息"""
    try:
        info = await service.get_file_info(request.key)
        if not info:
            return BaseResponse(code=ErrorCode.FILE_NOT_FOUND, data=None)

        return BaseResponse(
            code=ErrorCode.SUCCESS, message="获取成功",
            data=FileInfoData(
                key=info.key, size=info.size,
                content_type=info.content_type,
                last_modified=str(info.last_modified) if info.last_modified else None
            )
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/delete", response_model=BaseResponse[DeleteData])
async def delete_file(
    request: FileKeyRequest,
    service: OSSService = Depends(get_oss_service)
):
    """删除文件"""
    try:
        success = await service.delete_file(request.key)
        return BaseResponse(
            code=ErrorCode.SUCCESS, message="删除成功",
            data=DeleteData(success=success, key=request.key)
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/delete/batch", response_model=BaseResponse[BatchDeleteData])
async def batch_delete_files(
    request: BatchDeleteRequest,
    service: OSSService = Depends(get_oss_service)
):
    """批量删除文件"""
    try:
        results = await service.delete_files(request.keys)
        return BaseResponse(
            code=ErrorCode.SUCCESS, message="批量删除成功",
            data=BatchDeleteData(results=results)
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/list", response_model=BaseResponse[List[FileInfoData]])
async def list_files(
    request: FileListRequest,
    service: OSSService = Depends(get_oss_service)
):
    """列举文件"""
    try:
        files = await service.list_files(prefix=request.prefix, max_keys=request.max_keys, marker=request.marker)
        file_list = [
            FileInfoData(
                key=f.key, size=f.size, content_type=f.content_type,
                last_modified=str(f.last_modified) if f.last_modified else None
            )
            for f in files
        ]
        return BaseResponse(code=ErrorCode.SUCCESS, message="获取成功", data=file_list)
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/signed-url", response_model=BaseResponse[SignedUrlData])
async def get_signed_url(
    request: SignedUrlRequest,
    service: OSSService = Depends(get_oss_service)
):
    """获取签名 URL"""
    try:
        url = service.get_signed_url(
            request.key, expires=request.expires,
            for_download=request.for_download, filename=request.filename
        )
        return BaseResponse(
            code=ErrorCode.SUCCESS, message="获取成功",
            data=SignedUrlData(url=url, expires_in=request.expires or 3600)
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/upload-url", response_model=BaseResponse[UploadUrlData])
async def get_upload_url(
    request: UploadUrlRequest,
    service: OSSService = Depends(get_oss_service)
):
    """获取上传 URL（用于客户端直传）"""
    try:
        _category = None
        if request.category:
            try:
                _category = FileCategory(request.category)
            except ValueError:
                pass

        key = service.generate_upload_key(request.filename, prefix=request.prefix, category=_category)
        upload_url = service.get_upload_url(key, expires=request.expires, content_type=request.content_type)

        return BaseResponse(
            code=ErrorCode.SUCCESS, message="获取成功",
            data=UploadUrlData(key=key, upload_url=upload_url, expires_in=request.expires or 3600)
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)


@router.post("/exists", response_model=BaseResponse[FileExistsData])
async def check_file_exists(
    request: FileKeyRequest,
    service: OSSService = Depends(get_oss_service)
):
    """检查文件是否存在"""
    try:
        exists = await service.file_exists(request.key)
        return BaseResponse(
            code=ErrorCode.SUCCESS, message="检查成功",
            data=FileExistsData(exists=exists, key=request.key)
        )
    except Exception as e:
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=str(e), data=None)
