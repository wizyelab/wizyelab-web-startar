"""文件存储 API 路由（内部，需认证）

提供增强版文件上传、下载、管理等接口，支持 MD5 去重和媒体处理
"""

import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.storage.oss_service import FileCategory, OSSService, oss_service
from app.services.multimedia_service import MultimediaService
from app.services.media_processor_service import (
    media_processor_service,
    ImageProcessResult,
    VideoProcessResult,
)
from app.models.multimedia import StorageType, FileType, get_file_type_by_mime, Multimedia

from app.schemas.common import BaseResponse
from app.core.error_codes import ErrorCode
from app.schemas.file import (
    MediaUploadResponse, MultiImage,
    FileInfoData, SignedUrlData, UploadUrlData,
    DeleteData, BatchDeleteData, FileExistsData,
    FileKeyRequest, FileIdRequest, DownloadRequest, FileListRequest,
    SignedUrlRequest, UploadUrlRequest, BatchDeleteRequest
)
from app.infrastructure.database.connection import get_async_db
from app.middleware.request_context import get_user_id
from app.core.logging import setup_logger
from app.core.config import settings
from typing import Optional, List


logger = setup_logger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


# ========================= 依赖注入 =========================

def get_oss_service() -> OSSService:
    """获取 OSS 服务实例"""
    return oss_service


# ========================= API 路由 =========================

@router.post("/upload", response_model=BaseResponse[MediaUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    prefix: str = Form(default="wizzy/user/"),
    category: Optional[str] = Form(default=None),
    service: OSSService = Depends(get_oss_service),
    db: AsyncSession = Depends(get_async_db),
):
    """
    上传文件（支持图片处理、视频封面、MD5 去重）

    - **file**: 要上传的文件
    - **prefix**: 存储路径前缀，默认 "wizzy/user/"
    - **category**: 文件分类 (images/videos/audios/documents/others)
    """
    try:
        user_id = get_user_id()
        media_processor = media_processor_service

        # 1. 计算 MD5
        hash_md5 = await media_processor.calculate_file_md5(file)

        # 2. 检查 MD5 去重
        multimedia_service = MultimediaService(db)
        existing = await multimedia_service.check_duplicate_by_md5(hash_md5, user_id)

        if existing:
            logger.info(f"File already exists (MD5: {hash_md5}), returning existing record")
            return BaseResponse(
                code=ErrorCode.SUCCESS,
                message="文件已存在（秒传）",
                data=_build_upload_response(existing, is_duplicate=True)
            )

        # 3. 解析分类
        _category = None
        if category:
            try:
                _category = FileCategory(category)
            except ValueError:
                return BaseResponse(code=ErrorCode.INVALID_FILE_CATEGORY, data=None)

        # 4. 上传到 OSS
        result = await service.upload_file(file, prefix=prefix, category=_category)

        # 5. 处理图片/视频
        image_result = None
        video_result = None
        width, height, duration = 0, 0, 0
        multi_imgs_json = ""
        extra_data = ""

        file_type = get_file_type_by_mime(result.content_type)

        if file_type == FileType.IMAGE:
            image_result = await media_processor.process_image(result.key)
            if image_result:
                width = image_result.metadata.width
                height = image_result.metadata.height
                multi_imgs_json = json.dumps(image_result.multi_imgs.dict(), ensure_ascii=False)
                extra_data = media_processor.build_extra_data(file_type, image_result=image_result)

        elif file_type == FileType.VIDEO:
            video_result = await media_processor.process_video(result.key)
            if video_result:
                if video_result.metadata:
                    width = video_result.metadata.width
                    height = video_result.metadata.height
                    duration = video_result.metadata.duration
                else:
                    logger.warning(f"OSS video/info not available, trying ffprobe for {result.key}")
                    await file.seek(0)
                    file_content = await file.read()
                    fallback_metadata = await media_processor.get_video_info_from_file(file_content)
                    if fallback_metadata:
                        width = fallback_metadata.width
                        height = fallback_metadata.height
                        duration = fallback_metadata.duration

                multi_imgs_json = json.dumps(video_result.multi_imgs.dict(), ensure_ascii=False)
                extra_data = media_processor.build_extra_data(file_type, video_result=video_result)

        # 6. 写入 multimedia 表
        success, message, multimedia = await multimedia_service.create_multimedia(
            user_id=user_id,
            file_name=result.filename,
            mime_type=result.content_type,
            file_size=result.size,
            original_uri=result.key,
            storage_type=StorageType.OSS,
            width=width, height=height, duration=duration,
            multi_imgs=multi_imgs_json,
            hash_md5=hash_md5,
            extra=extra_data,
        )

        if not success or not multimedia:
            logger.error(f"Failed to save multimedia record: {message}")
            return BaseResponse(code=ErrorCode.FILE_RECORD_SAVE_FAILED, data=None)

        return BaseResponse(
            code=ErrorCode.SUCCESS,
            message="上传成功",
            data=_build_upload_response(multimedia, result.url, is_duplicate=False)
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=f"Upload failed: {str(e)}", data=None)


@router.post("/upload/batch", response_model=BaseResponse[List[MediaUploadResponse]])
async def upload_files(
    files: list[UploadFile] = File(...),
    prefix: str = Form(default="wizzy/user/"),
    category: Optional[str] = Form(default=None),
    service: OSSService = Depends(get_oss_service),
    db: AsyncSession = Depends(get_async_db),
):
    """批量上传文件（支持图片处理、视频封面、MD5 去重）"""
    user_id = get_user_id()
    multimedia_service = MultimediaService(db)
    media_processor = media_processor_service
    results = []

    _category = None
    if category:
        try:
            _category = FileCategory(category)
        except ValueError:
            return BaseResponse(code=ErrorCode.INVALID_FILE_CATEGORY, data=None)

    for file in files:
        try:
            hash_md5 = await media_processor.calculate_file_md5(file)
            existing = await multimedia_service.check_duplicate_by_md5(hash_md5, user_id)

            if existing:
                results.append(_build_upload_response(existing, is_duplicate=True))
                continue

            result = await service.upload_file(file, prefix=prefix, category=_category)

            image_result = None
            video_result = None
            width, height, duration = 0, 0, 0
            multi_imgs_json = ""
            extra_data = ""
            file_type = get_file_type_by_mime(result.content_type)

            if file_type == FileType.IMAGE:
                image_result = await media_processor.process_image(result.key)
                if image_result:
                    width = image_result.metadata.width
                    height = image_result.metadata.height
                    multi_imgs_json = json.dumps(image_result.multi_imgs.dict(), ensure_ascii=False)
                    extra_data = media_processor.build_extra_data(file_type, image_result=image_result)
            elif file_type == FileType.VIDEO:
                video_result = await media_processor.process_video(result.key)
                if video_result:
                    if video_result.metadata:
                        width = video_result.metadata.width
                        height = video_result.metadata.height
                        duration = video_result.metadata.duration
                    multi_imgs_json = json.dumps(video_result.multi_imgs.dict(), ensure_ascii=False)
                    extra_data = media_processor.build_extra_data(file_type, video_result=video_result)

            success, message, multimedia = await multimedia_service.create_multimedia(
                user_id=user_id, file_name=result.filename, mime_type=result.content_type,
                file_size=result.size, original_uri=result.key, storage_type=StorageType.OSS,
                width=width, height=height, duration=duration,
                multi_imgs=multi_imgs_json, hash_md5=hash_md5, extra=extra_data,
            )

            if not success or not multimedia:
                return BaseResponse(
                    code=ErrorCode.GENERAL_ERROR,
                    message=f"Failed to save record for {file.filename}: {message}", data=None
                )

            results.append(_build_upload_response(multimedia, result.url, is_duplicate=False))

        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            return BaseResponse(
                code=ErrorCode.GENERAL_ERROR,
                message=f"Failed to upload {file.filename}: {str(e)}", data=None
            )

    return BaseResponse(code=0, message="批量上传成功", data=results)


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
        return BaseResponse(code=ErrorCode.GENERAL_ERROR, message=f"Failed: {str(e)}", data=None)


@router.post("/multimedia/info", response_model=BaseResponse[MediaUploadResponse])
async def get_multimedia_info(
    request: FileIdRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """获取多媒体文件完整信息（从数据库）"""
    try:
        multimedia_service = MultimediaService(db)
        multimedia = await multimedia_service.get_by_file_id(request.file_id)

        if not multimedia:
            return BaseResponse(code=ErrorCode.FILE_NOT_FOUND, data=None)

        return BaseResponse(
            code=ErrorCode.SUCCESS, message="获取成功",
            data=_build_upload_response(multimedia, is_duplicate=False)
        )
    except Exception as e:
        logger.error(f"Failed to get multimedia info: {e}")
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


def _build_upload_response(
    multimedia: Multimedia,
    original_url: str = "",
    is_duplicate: bool = False
) -> MediaUploadResponse:
    """构建上传响应"""
    multi_imgs_data = None

    if multimedia.multi_imgs:
        try:
            multi_imgs_dict = json.loads(multimedia.multi_imgs)
            multi_imgs_data = MultiImage(**multi_imgs_dict)
            multi_imgs_data = media_processor_service.add_host_to_multi_imgs(multi_imgs_data)
        except Exception as e:
            logger.error(f"Failed to parse multi_imgs field: {e}")

    download_url = ""
    if multimedia.file_type == FileType.IMAGE:
        download_url = media_processor_service.generate_watermarked_url(multimedia.original_uri)
    elif multimedia.file_type == FileType.VIDEO:
        download_url = original_url or f"https://{settings.oss.file_host}/{multimedia.original_uri}"
    else:
        download_url = original_url or f"https://{settings.oss.file_host}/{multimedia.original_uri}"

    return MediaUploadResponse(
        file_id=multimedia.file_id,
        file_type=multimedia.file_type,
        file_name=multimedia.file_name,
        file_ext=multimedia.file_ext,
        file_size=multimedia.file_size,
        mime_type=multimedia.mime_type,
        original_uri=multimedia.original_uri,
        url=original_url or f"https://{settings.oss.file_host}/{multimedia.original_uri}",
        download_url=download_url,
        width=multimedia.width,
        height=multimedia.height,
        duration=multimedia.duration,
        multi_imgs=multi_imgs_data,
        hash_md5=multimedia.hash_md5,
        is_duplicate=is_duplicate,
        create_time=multimedia.create_time,
    )
