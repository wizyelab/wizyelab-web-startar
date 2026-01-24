"""
雪花算法 ID 生成器

生成 64 位分布式唯一 ID，结构如下：
┌─────────────────────────────────────────────────────────────────────┐
│  1 bit  │     41 bits      │  5 bits  │  5 bits  │    12 bits     │
│  符号位  │     时间戳        │数据中心ID │ 机器ID   │    序列号       │
│    0    │   毫秒级时间戳     │  0-31    │  0-31   │    0-4095      │
└─────────────────────────────────────────────────────────────────────┘

特点：
- 趋势递增，有利于数据库索引
- 支持分布式环境，通过 datacenter_id 和 worker_id 区分
- 每毫秒可生成 4096 个 ID
- 生成的 ID 是 18-19 位数字
"""

import time
import threading
from typing import Optional

from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


class SnowflakeGenerator:
    """
    雪花算法 ID 生成器

    线程安全的单例模式实现
    """

    _instance: Optional['SnowflakeGenerator'] = None
    _lock = threading.Lock()

    # 起始时间戳 (2024-01-01 00:00:00 UTC)
    EPOCH = 1704067200000

    # 各部分位数
    WORKER_ID_BITS = 5
    DATACENTER_ID_BITS = 5
    SEQUENCE_BITS = 12

    # 最大值
    MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1  # 31
    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1  # 31
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095

    # 位移量
    WORKER_ID_SHIFT = SEQUENCE_BITS  # 12
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS  # 17
    TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS  # 22

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 从配置读取，默认值为 1
        self.worker_id = getattr(settings, 'snowflake_worker_id', 1)
        self.datacenter_id = getattr(settings, 'snowflake_datacenter_id', 1)

        # 验证参数
        if self.worker_id < 0 or self.worker_id > self.MAX_WORKER_ID:
            raise ValueError(f"worker_id 必须在 0-{self.MAX_WORKER_ID} 之间")
        if self.datacenter_id < 0 or self.datacenter_id > self.MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id 必须在 0-{self.MAX_DATACENTER_ID} 之间")

        self.sequence = 0
        self.last_timestamp = -1
        self._gen_lock = threading.Lock()
        self._initialized = True

        logger.info(
            f"SnowflakeGenerator 初始化: "
            f"datacenter_id={self.datacenter_id}, worker_id={self.worker_id}"
        )

    def _current_millis(self) -> int:
        """获取当前毫秒时间戳"""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """等待到下一毫秒"""
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp

    def generate(self) -> int:
        """
        生成下一个 ID

        Returns:
            64 位整数 ID
        """
        with self._gen_lock:
            timestamp = self._current_millis()

            # 时钟回拨检查
            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    f"时钟回拨，拒绝生成 ID。"
                    f"回拨时间: {self.last_timestamp - timestamp}ms"
                )

            # 同一毫秒内
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                # 序列号溢出，等待下一毫秒
                if self.sequence == 0:
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                # 新的毫秒，序列号重置
                self.sequence = 0

            self.last_timestamp = timestamp

            # 组装 ID
            snowflake_id = (
                ((timestamp - self.EPOCH) << self.TIMESTAMP_SHIFT) |
                (self.datacenter_id << self.DATACENTER_ID_SHIFT) |
                (self.worker_id << self.WORKER_ID_SHIFT) |
                self.sequence
            )

            return snowflake_id

    def generate_str(self) -> str:
        """
        生成下一个 ID（字符串格式）

        Returns:
            ID 字符串
        """
        return str(self.generate())

    @staticmethod
    def parse(snowflake_id: int) -> dict:
        """
        解析雪花 ID

        Args:
            snowflake_id: 雪花 ID

        Returns:
            解析后的字典，包含 timestamp, datacenter_id, worker_id, sequence
        """
        sequence = snowflake_id & SnowflakeGenerator.MAX_SEQUENCE
        worker_id = (snowflake_id >> SnowflakeGenerator.WORKER_ID_SHIFT) & SnowflakeGenerator.MAX_WORKER_ID
        datacenter_id = (snowflake_id >> SnowflakeGenerator.DATACENTER_ID_SHIFT) & SnowflakeGenerator.MAX_DATACENTER_ID
        timestamp = (snowflake_id >> SnowflakeGenerator.TIMESTAMP_SHIFT) + SnowflakeGenerator.EPOCH

        return {
            "timestamp": timestamp,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000)),
            "datacenter_id": datacenter_id,
            "worker_id": worker_id,
            "sequence": sequence,
        }


# 全局实例
snowflake = SnowflakeGenerator()


def generate_id() -> int:
    """生成雪花 ID（整数）"""
    return snowflake.generate()


def generate_id_str() -> str:
    """生成雪花 ID（字符串）"""
    return snowflake.generate_str()

