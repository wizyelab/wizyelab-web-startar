"""
多媒体文件服务模块

处理多媒体文件的创建、查询等业务逻辑
"""

from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import setup_logger
from app.models.multimedia import (
    Multimedia,
    FileType,
    StorageType,
    FileStatus,
    get_file_type_by_mime,
    get_file_extension,
    current_timestamp_ms,
)

logger = setup_logger(__name__)


class MultimediaService:
    """多媒体文件服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_multimedia(
        self,
        user_id: str,
        file_name: str,
        mime_type: str,
        file_size: int,
        original_uri: str,
        storage_type: int = StorageType.OSS,
        width: int = 0,
        height: int = 0,
        duration: int = 0,
        multi_imgs: str = "",
        hash_md5: str = "",
        hash_sha256: str = "",
        extra: str = "",
    ) -> Tuple[bool, str, Optional[Multimedia]]:
        """创建多媒体文件记录"""
        try:
            file_type = get_file_type_by_mime(mime_type)
            file_ext = get_file_extension(file_name)

            multimedia = Multimedia(
                user_id=user_id,
                file_type=file_type,
                file_name=file_name,
                file_ext=file_ext,
                mime_type=mime_type,
                file_size=file_size,
                storage_type=storage_type,
                original_uri=original_uri,
                width=width,
                height=height,
                duration=duration,
                multi_imgs=multi_imgs if multi_imgs else None,
                status=FileStatus.SUCCESS,
                hash_md5=hash_md5,
                hash_sha256=hash_sha256,
                extra=extra if extra else None,
            )
            self.db.add(multimedia)
            await self.db.commit()
            await self.db.refresh(multimedia)

            logger.info(f"多媒体文件创建成功: file_id={multimedia.file_id}, user_id={user_id}")
            return True, "success", multimedia

        except Exception as e:
            logger.error(f"创建多媒体文件失败: {e}")
            await self.db.rollback()
            return False, f"Create multimedia failed: {str(e)}", None

    async def get_by_file_id(self, file_id: str) -> Optional[Multimedia]:
        """根据文件ID获取记录"""
        stmt = select(Multimedia).where(Multimedia.file_id == file_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: str,
        file_type: Optional[int] = None,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[int, List[Multimedia]]:
        """根据用户ID获取文件列表"""
        try:
            conditions = [Multimedia.user_id == user_id]
            if file_type is not None:
                conditions.append(Multimedia.file_type == file_type)
            if status is not None:
                conditions.append(Multimedia.status == status)
            else:
                conditions.append(Multimedia.status != FileStatus.DELETED)

            count_stmt = select(func.count()).select_from(Multimedia).where(*conditions)
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar() or 0

            offset = (page - 1) * page_size
            stmt = (
                select(Multimedia)
                .where(*conditions)
                .order_by(Multimedia.create_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            files = result.scalars().all()

            return total, list(files)

        except Exception as e:
            logger.error(f"获取用户文件列表失败: {e}")
            return 0, []

    async def delete_by_file_id(self, file_id: str, user_id: str) -> Tuple[bool, str]:
        """软删除文件（标记为已删除）"""
        try:
            multimedia = await self.get_by_file_id(file_id)
            if not multimedia:
                return False, "File not found"

            if multimedia.user_id != user_id:
                return False, "No permission"

            if multimedia.status == FileStatus.DELETED:
                return False, "File already deleted"

            multimedia.status = FileStatus.DELETED
            multimedia.update_time = current_timestamp_ms()
            await self.db.commit()

            logger.info(f"多媒体文件删除成功: file_id={file_id}, user_id={user_id}")
            return True, "success"

        except Exception as e:
            logger.error(f"删除多媒体文件失败: {e}")
            await self.db.rollback()
            return False, f"Delete failed: {str(e)}"

    async def check_duplicate_by_md5(self, hash_md5: str, user_id: str) -> Optional[Multimedia]:
        """根据 MD5 检查是否存在重复文件（同一用户）"""
        if not hash_md5:
            return None

        try:
            stmt = select(Multimedia).where(
                Multimedia.user_id == user_id,
                Multimedia.hash_md5 == hash_md5,
                Multimedia.status == FileStatus.SUCCESS
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"检查 MD5 去重失败: {e}")
            return None
