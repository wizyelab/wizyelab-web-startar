"""
媒体处理服务

负责图片和视频的 OSS 处理：
- 图片：获取元数据、生成多尺寸 URL、生成水印URL
- 视频：获取元数据、生成封面、生成多尺寸封面URL
- MD5：计算文件MD5用于去重
"""

import hashlib
import json
import logging
import base64
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from pathlib import Path

import httpx
from fastapi import UploadFile

from app.core.config import settings
from app.core.snowflake import generate_id_str
from app.models.multimedia import FileType
from app.schemas.file import Image, MultiImage

logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 8192
HTTP_TIMEOUT = 10.0


class ImageSize(str, Enum):
    """图片尺寸枚举"""
    ORIGINAL = "original"
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"
    THUMBNAIL = "thumbnail"


# 尺寸配置
IMAGE_SIZE_CONFIG = {
    ImageSize.LARGE: {"width": 1920, "height": 1080, "quality": 90},
    ImageSize.MEDIUM: {"width": 1280, "height": 720, "quality": 85},
    ImageSize.SMALL: {"width": 640, "height": 360, "quality": 80},
    ImageSize.THUMBNAIL: {"width": 200, "height": 200, "quality": 75},
}

# 水印配置
WATERMARK_CONFIG = {
    "enabled": True,
    "mode": "text",
    "text": "© WizzySpot",
    "text_color": "FFFFFF",
    "text_size": 30,
    "image_path": "watermark/logo.png",
    "position": "se",
    "transparency": 90,
    "margin_x": 10,
    "margin_y": 10,
}


@dataclass
class VideoMetadata:
    """视频元数据"""
    width: int
    height: int
    duration: int
    format: str
    size: int
    bitrate: int


@dataclass
class ImageMetadata:
    """图片元数据"""
    width: int
    height: int
    format: str
    size: int


@dataclass
class ImageProcessResult:
    """图片处理结果"""
    metadata: ImageMetadata
    multi_imgs: MultiImage


@dataclass
class VideoProcessResult:
    """视频处理结果"""
    metadata: Optional[VideoMetadata]
    multi_imgs: MultiImage


class MediaProcessorService:
    """媒体处理服务"""

    def __init__(self):
        self.oss_config = settings.oss
        self.base_url = f"https://{self.oss_config.file_host}"
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """获取或创建共享的 HTTP 客户端"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self._http_client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def calculate_md5(self, content: bytes) -> str:
        """计算文件 MD5"""
        return hashlib.md5(content).hexdigest()

    async def calculate_file_md5(self, file: UploadFile) -> str:
        """计算上传文件的 MD5（分块读取，适合大文件）"""
        md5_hash = hashlib.md5()
        while chunk := await file.read(CHUNK_SIZE):
            md5_hash.update(chunk)
        await file.seek(0)
        return md5_hash.hexdigest()

    async def get_image_info(self, oss_key: str) -> Optional[ImageMetadata]:
        """获取图片元数据（调用 OSS image/info API）"""
        try:
            url = f"{self.base_url}/{oss_key}?x-oss-process=image/info"
            client = await self._get_http_client()
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            return ImageMetadata(
                width=int(data.get("ImageWidth", {}).get("value", 0)),
                height=int(data.get("ImageHeight", {}).get("value", 0)),
                format=data.get("Format", {}).get("value", ""),
                size=int(data.get("FileSize", {}).get("value", 0))
            )
        except Exception as e:
            logger.error(f"Failed to get image info for {oss_key}: {e}")
            return None

    async def get_video_info(self, oss_key: str) -> Optional[VideoMetadata]:
        """获取视频元数据（调用 OSS video/info API）"""
        try:
            url = f"{self.base_url}/{oss_key}?x-oss-process=video/info"
            client = await self._get_http_client()
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            streams = data.get("streams", [])
            if not streams:
                return None

            video_stream = None
            for stream in streams:
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                return None

            format_info = data.get("format", {})
            return VideoMetadata(
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                duration=int(float(format_info.get("duration", 0))),
                format=format_info.get("format_name", ""),
                size=int(format_info.get("size", 0)),
                bitrate=int(format_info.get("bit_rate", 0))
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting video info for {oss_key}: status={e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get video info for {oss_key}: {e}")
            return None

    async def get_video_info_from_file(self, file_content: bytes) -> Optional[VideoMetadata]:
        """使用 ffprobe 从文件内容获取视频元数据（降级方案）"""
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', temp_file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                logger.error(f"ffprobe failed: {result.stderr}")
                return None

            data = json.loads(result.stdout)
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break

            if not video_stream:
                return None

            format_info = data.get('format', {})
            return VideoMetadata(
                width=int(video_stream.get('width', 0)),
                height=int(video_stream.get('height', 0)),
                duration=int(float(format_info.get('duration', 0))),
                format=format_info.get('format_name', ''),
                size=int(format_info.get('size', 0)),
                bitrate=int(format_info.get('bit_rate', 0))
            )
        except FileNotFoundError:
            logger.warning("ffprobe not found. Please install ffmpeg.")
            return None
        except subprocess.TimeoutExpired:
            logger.error("ffprobe timeout after 30 seconds")
            return None
        except Exception as e:
            logger.error(f"Failed to get video info from file: {e}")
            return None
        finally:
            if temp_file and Path(temp_file.name).exists():
                try:
                    Path(temp_file.name).unlink()
                except Exception:
                    pass

    def generate_image_uri(self, oss_key: str, size: ImageSize, format: str = "jpg") -> str:
        """生成图片处理 URL"""
        base_uri = f"/{oss_key}"
        if size == ImageSize.ORIGINAL:
            return base_uri

        config = IMAGE_SIZE_CONFIG[size]
        w, h, q = config["width"], config["height"], config["quality"]
        process = f"image/resize,m_lfit,w_{w},h_{h}/quality,q_{q}/format,{format}"
        return f"{base_uri}?x-oss-process={process}"

    def generate_watermarked_url(
        self, oss_key: str, watermark_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成带水印的图片 URL"""
        config = watermark_config or WATERMARK_CONFIG
        if not config.get("enabled", False):
            return f"{self.base_url}/{oss_key}"

        base_url = f"{self.base_url}/{oss_key}"
        mode = config.get("mode", "text")
        position = config.get("position", "se")
        transparency = config.get("transparency", 90)
        margin_x = config.get("margin_x", 10)
        margin_y = config.get("margin_y", 10)

        if mode == "text":
            text = config.get("text", "© WizzySpot")
            text_b64 = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            color = config.get("text_color", "FFFFFF")
            size = config.get("text_size", 30)
            process = (
                f"image/watermark,"
                f"text_{text_b64},"
                f"color_{color},"
                f"size_{size},"
                f"g_{position},"
                f"x_{margin_x},"
                f"y_{margin_y},"
                f"t_{transparency}"
            )
        else:
            image_path = config.get("image_path", "")
            if not image_path:
                return self.generate_watermarked_url(oss_key, {**config, "mode": "text"})
            image_b64 = base64.b64encode(image_path.encode('utf-8')).decode('utf-8')
            process = (
                f"image/watermark,"
                f"image_{image_b64},"
                f"g_{position},"
                f"x_{margin_x},"
                f"y_{margin_y},"
                f"t_{transparency}"
            )

        return f"{base_url}?x-oss-process={process}"

    def _create_image_for_size(self, oss_key: str, size: ImageSize, format: str, file_size: int) -> Image:
        """为指定尺寸创建 Image 对象"""
        config = IMAGE_SIZE_CONFIG[size]
        return Image(
            id=generate_id_str(),
            height=config["height"],
            width=config["width"],
            format=format,
            size=file_size,
            main_url=self.generate_image_uri(oss_key, size),
            back_urls=[]
        )

    async def process_image(self, oss_key: str) -> Optional[ImageProcessResult]:
        """处理图片：获取元数据 + 生成多尺寸 Image 对象"""
        metadata = await self.get_image_info(oss_key)
        if not metadata:
            logger.error(f"Failed to get image metadata for {oss_key}")
            return None

        multi_imgs = MultiImage(
            large=self._create_image_for_size(oss_key, ImageSize.LARGE, metadata.format, metadata.size),
            medium=self._create_image_for_size(oss_key, ImageSize.MEDIUM, metadata.format, metadata.size),
            small=self._create_image_for_size(oss_key, ImageSize.SMALL, metadata.format, metadata.size),
            thumbnail=self._create_image_for_size(oss_key, ImageSize.THUMBNAIL, metadata.format, metadata.size)
        )
        return ImageProcessResult(metadata=metadata, multi_imgs=multi_imgs)

    def generate_video_snapshot_url(
        self, oss_key: str, time_ms: int = 1000,
        width: Optional[int] = None, height: Optional[int] = None, format: str = "jpg"
    ) -> str:
        """生成视频截帧 URL"""
        base_url = f"/{oss_key}"
        params = [f"t_{time_ms}", f"f_{format}", "m_fast"]
        if width:
            params.append(f"w_{width}")
        if height:
            params.append(f"h_{height}")
        process = f"video/snapshot,{','.join(params)}"
        return f"{base_url}?x-oss-process={process}"

    def _create_video_snapshot_for_size(self, oss_key: str, size: ImageSize, snapshot_time_ms: int) -> Image:
        """为指定尺寸创建视频截图 Image 对象"""
        config = IMAGE_SIZE_CONFIG[size]
        return Image(
            id=generate_id_str(),
            height=config["height"],
            width=config["width"],
            format="jpg",
            size=0,
            main_url=self.generate_video_snapshot_url(
                oss_key, snapshot_time_ms,
                width=config["width"], height=config["height"]
            ),
            back_urls=[]
        )

    async def process_video(self, oss_key: str, snapshot_time_ms: int = 1000) -> VideoProcessResult:
        """处理视频：获取元数据 + 生成封面多尺寸 Image 对象"""
        metadata = await self.get_video_info(oss_key)
        if metadata:
            logger.info(f"Video metadata: {metadata.width}x{metadata.height}, duration={metadata.duration}s")
        else:
            logger.warning(f"Failed to get video metadata for {oss_key}")

        multi_imgs = MultiImage(
            large=self._create_video_snapshot_for_size(oss_key, ImageSize.LARGE, snapshot_time_ms),
            medium=self._create_video_snapshot_for_size(oss_key, ImageSize.MEDIUM, snapshot_time_ms),
            small=self._create_video_snapshot_for_size(oss_key, ImageSize.SMALL, snapshot_time_ms),
            thumbnail=self._create_video_snapshot_for_size(oss_key, ImageSize.THUMBNAIL, snapshot_time_ms)
        )
        return VideoProcessResult(metadata=metadata, multi_imgs=multi_imgs)

    def add_host_to_multi_imgs(self, multi_imgs: MultiImage) -> MultiImage:
        """为 MultiImage 中所有图片的 main_url 添加完整的 host 前缀"""
        def add_host(url: str) -> str:
            if url.startswith("http://") or url.startswith("https://"):
                return url
            return f"{self.base_url}/{url.lstrip('/')}"

        for attr in ['large', 'medium', 'small', 'thumbnail']:
            img = getattr(multi_imgs, attr, None)
            if img:
                img.main_url = add_host(img.main_url)

        return multi_imgs

    def build_extra_data(
        self, file_type: int,
        image_result: Optional[ImageProcessResult] = None,
        video_result: Optional[VideoProcessResult] = None
    ) -> str:
        """构建 extra 字段 JSON 数据"""
        extra_data = {}

        if file_type == FileType.IMAGE and image_result:
            extra_data["multi_imgs"] = image_result.multi_imgs.dict()
            extra_data["metadata"] = {
                "width": image_result.metadata.width,
                "height": image_result.metadata.height,
                "format": image_result.metadata.format,
                "size": image_result.metadata.size,
            }
        elif file_type == FileType.VIDEO and video_result:
            extra_data["multi_imgs"] = video_result.multi_imgs.dict()
            if video_result.metadata:
                extra_data["metadata"] = {
                    "width": video_result.metadata.width,
                    "height": video_result.metadata.height,
                    "duration": video_result.metadata.duration,
                    "format": video_result.metadata.format,
                    "size": video_result.metadata.size,
                    "bitrate": video_result.metadata.bitrate,
                }

        return json.dumps(extra_data, ensure_ascii=False)


# 全局服务实例
media_processor_service = MediaProcessorService()
