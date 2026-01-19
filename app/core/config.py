"""应用配置模块 - 支持多环境配置和环境变量覆盖"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


env = load_dotenv()
# 支持的环境列表
VALID_ENVIRONMENTS = ("dev", "staging", "prod")


class ServerConfig(BaseSettings):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    workers: int = 1
    log_level: str = "info"


class AppConfig(BaseSettings):
    """应用配置"""
    name: str = "wizyelab-web-start"
    version: str = "0.1.0"
    debug: bool = True
    api_prefix: str = "/api"
    secret_key: str = "your-super-secret-key-change-in-production"
    access_token_expire_minutes: int = 60


class DatabaseConfig(BaseSettings):
    """数据库配置 - PolarDB/MySQL"""
    host: str = "pc-uf6q6w8i03g6g21v6.rwlb.rds.aliyuncs.com"
    port: int = 3306
    user: str = "wizyelab_root"
    password: str = "Wizyelab@test"
    database: str = "wizyelab"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False

    @property
    def url(self) -> str:
        """同步数据库连接 URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """异步数据库连接 URL"""
        return f"mysql+aiomysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseSettings):
    """Redis 配置 - Tair"""
    host: str = "redis-wizyelab-test1.redis.rds.aliyuncs.com"
    port: int = 6379
    username: str = "r-uf6hmr2rljwc1cvovw"
    password: str = "Wizyelab@test"
    db: int = 0
    max_connections: int = 50
    decode_responses: bool = True
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    @property
    def url(self) -> str:
        """Redis 连接 URL"""
        return f"redis://{self.username}:{self.password}@{self.host}:{self.port}/{self.db}"


class LLMConfig(BaseSettings):
    """LLM 配置"""
    provider: str = "openai"
    api_key: str = ""
    api_base: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    request_timeout: int = 60
    langsmith_api_key: str = ""
    langsmith_project: str = "wizyelab-agent"
    langsmith_tracing: bool = False


class AgentConfig(BaseSettings):
    """Agent 配置"""
    max_iterations: int = 10
    early_stopping_method: str = "generate"
    verbose: bool = True
    memory_type: str = "buffer"
    memory_k: int = 5


class LoggingConfig(BaseSettings):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = True
    log_to_file: bool = False
    log_file_path: str = "logs/app.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5


class PrometheusConfig(BaseSettings):
    """Prometheus 监控配置"""
    enabled: bool = True
    endpoint: str = "/metrics"


class TracingConfig(BaseSettings):
    """分布式追踪配置"""
    enabled: bool = False
    service_name: str = "wizyelab-web-start"
    otlp_endpoint: str = "http://localhost:4317"
    sample_rate: float = 1.0


class HealthCheckConfig(BaseSettings):
    """健康检查配置"""
    enabled: bool = True
    endpoint: str = "/health"
    include_details: bool = True


class MonitoringConfig(BaseSettings):
    """监控配置"""
    prometheus: PrometheusConfig = Field(default_factory=PrometheusConfig)
    tracing: TracingConfig = Field(default_factory=TracingConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)


class RateLimitConfig(BaseSettings):
    """限流配置"""
    enabled: bool = True
    default_limit: int = 60
    default_window: int = 60
    api_limits: Dict[str, int] = Field(default_factory=lambda: {
        "chat": 30,
        "open": 100,
        "internal": 200
    })


class LocalCacheConfig(BaseSettings):
    """本地缓存配置"""
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 300


class RedisCacheConfig(BaseSettings):
    """Redis 缓存配置"""
    enabled: bool = True
    prefix: str = "wizyelab:cache:"
    default_ttl: int = 3600


class CacheConfig(BaseSettings):
    """缓存配置"""
    local: LocalCacheConfig = Field(default_factory=LocalCacheConfig)
    redis: RedisCacheConfig = Field(default_factory=RedisCacheConfig)


class CORSConfig(BaseSettings):
    """CORS 配置"""
    allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])


class OSSUploadConfig(BaseSettings):
    """OSS 上传配置"""
    multipart_threshold: int = 10485760  # 10MB，超过此大小使用分片上传
    part_size: int = 10485760  # 10MB
    num_threads: int = 4


class OSSDownloadConfig(BaseSettings):
    """OSS 下载配置"""
    multipart_threshold: int = 10485760  # 10MB
    part_size: int = 10485760  # 10MB
    num_threads: int = 4


class OSSConfig(BaseSettings):
    """阿里云 OSS 配置"""
    access_key_id: str = ""
    access_key_secret: str = ""
    endpoint: str = "oss-cn-hangzhou.aliyuncs.com"
    bucket_name: str = ""
    internal_endpoint: str = ""  # 内网 endpoint
    use_https: bool = True
    connect_timeout: int = 30
    upload: OSSUploadConfig = Field(default_factory=OSSUploadConfig)
    download: OSSDownloadConfig = Field(default_factory=OSSDownloadConfig)
    url_expire_seconds: int = 3600  # 签名 URL 过期时间


class Settings(BaseSettings):
    """应用配置类，支持多环境配置和环境变量覆盖"""

    # 当前环境
    environment: str = "dev"

    # 服务器配置
    server: ServerConfig = Field(default_factory=ServerConfig)

    # 应用配置
    app: AppConfig = Field(default_factory=AppConfig)

    # 数据库配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # Redis 配置
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # LLM 配置
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Agent 配置
    agent: AgentConfig = Field(default_factory=AgentConfig)

    # 日志配置
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # 监控配置
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # 限流配置
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    # 缓存配置
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # CORS 配置
    cors: CORSConfig = Field(default_factory=CORSConfig)

    # OSS 配置
    oss: OSSConfig = Field(default_factory=OSSConfig)

    # 兼容旧的属性访问方式
    @property
    def server_host(self) -> str:
        return self.server.host

    @property
    def server_port(self) -> int:
        return self.server.port

    @property
    def server_reload(self) -> bool:
        return self.server.reload

    @property
    def server_workers(self) -> int:
        return self.server.workers

    @property
    def server_log_level(self) -> str:
        return self.server.log_level

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def app_version(self) -> str:
        return self.app.version

    @property
    def app_debug(self) -> bool:
        return self.app.debug

    @property
    def app_api_prefix(self) -> str:
        return self.app.api_prefix

    @property
    def database_url(self) -> str:
        return self.database.url

    @property
    def database_async_url(self) -> str:
        return self.database.async_url

    @property
    def redis_url(self) -> str:
        return self.redis.url

    @property
    def logging_level(self) -> str:
        return self.logging.level

    @property
    def logging_format(self) -> str:
        return self.logging.format

    @property
    def is_dev(self) -> bool:
        """是否为开发环境"""
        return self.environment == "dev"

    @property
    def is_staging(self) -> bool:
        """是否为预上线环境"""
        return self.environment == "staging"

    @property
    def is_prod(self) -> bool:
        """是否为生产环境"""
        return self.environment == "prod"

    @classmethod
    def get_environment(cls) -> str:
        """
        获取当前运行环境

        优先级: WIZYELAB_ENV > ENV > 默认值 "dev"

        Returns:
            环境名称: dev, staging, prod
        """
        env = os.environ.get("WIZYELAB_ENV") or os.environ.get("ENV") or "dev"
        env = env.lower()
        if env not in VALID_ENVIRONMENTS:
            print(f"Warning: Invalid environment '{env}', falling back to 'dev'")
            env = "dev"
        return env

    @classmethod
    def load_from_yaml(cls, env: str = None) -> "Settings":
        """
        从 YAML 文件加载配置，支持多环境配置

        加载顺序:
        1. base.yaml (基础配置)
        2. {env}.yaml (环境特定配置，覆盖 base)
        3. 环境变量覆盖 (${VAR_NAME} 占位符替换)
        4. WIZYELAB_* 环境变量覆盖

        Args:
            env: 环境名称 (dev/staging/prod)，默认从环境变量读取

        Returns:
            Settings 实例
        """
        if env is None:
            env = cls.get_environment()

        # 获取项目根目录
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        config_dir = project_root / "configs"

        # 加载基础配置
        base_config = {}
        base_yaml_path = config_dir / "base.yaml"
        if base_yaml_path.exists():
            with open(base_yaml_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}

        # 加载环境特定配置
        env_config = {}
        env_yaml_path = config_dir / f"{env}.yaml"
        if env_yaml_path.exists():
            with open(env_yaml_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}

        # 深度合并配置 (env 覆盖 base)
        yaml_config = cls._deep_merge(base_config, env_config)

        # 替换环境变量占位符 ${VAR_NAME}
        yaml_config = cls._substitute_env_vars(yaml_config)

        # 构建配置对象
        config_dict = cls._build_config_dict(yaml_config)
        config_dict["environment"] = env

        # 应用环境变量覆盖
        config_dict = cls._apply_env_overrides(config_dict, yaml_config)

        return cls(**config_dict)

    @classmethod
    def _deep_merge(cls, base: Dict, override: Dict) -> Dict:
        """
        深度合并两个字典，override 覆盖 base

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @classmethod
    def _substitute_env_vars(cls, config: Any) -> Any:
        """
        递归替换配置中的环境变量占位符 ${VAR_NAME}

        Args:
            config: 配置值 (可以是 dict, list, str 等)

        Returns:
            替换后的配置
        """
        if isinstance(config, dict):
            return {k: cls._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [cls._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, config)
            result = config
            for var_name in matches:
                env_value = os.environ.get(var_name, "")
                result = result.replace(f"${{{var_name}}}", env_value)
            return result
        else:
            return config

    @classmethod
    def _build_config_dict(cls, yaml_config: Dict) -> Dict:
        """
        从 YAML 配置构建配置字典

        Args:
            yaml_config: YAML 配置

        Returns:
            配置字典
        """
        config_dict = {}

        # 服务器配置
        if "server" in yaml_config:
            config_dict["server"] = ServerConfig(**yaml_config["server"])

        # 应用配置
        if "app" in yaml_config:
            config_dict["app"] = AppConfig(**yaml_config["app"])

        # 数据库配置
        if "database" in yaml_config:
            config_dict["database"] = DatabaseConfig(**yaml_config["database"])

        # Redis 配置
        if "redis" in yaml_config:
            config_dict["redis"] = RedisConfig(**yaml_config["redis"])

        # LLM 配置
        if "llm" in yaml_config:
            config_dict["llm"] = LLMConfig(**yaml_config["llm"])

        # Agent 配置
        if "agent" in yaml_config:
            config_dict["agent"] = AgentConfig(**yaml_config["agent"])

        # 日志配置
        if "logging" in yaml_config:
            config_dict["logging"] = LoggingConfig(**yaml_config["logging"])

        # 监控配置
        if "monitoring" in yaml_config:
            monitoring_data = yaml_config["monitoring"]
            monitoring_config = MonitoringConfig(
                prometheus=PrometheusConfig(**monitoring_data.get("prometheus", {})),
                tracing=TracingConfig(**monitoring_data.get("tracing", {})),
                health_check=HealthCheckConfig(**monitoring_data.get("health_check", {}))
            )
            config_dict["monitoring"] = monitoring_config

        # 限流配置
        if "rate_limit" in yaml_config:
            config_dict["rate_limit"] = RateLimitConfig(**yaml_config["rate_limit"])

        # 缓存配置
        if "cache" in yaml_config:
            cache_data = yaml_config["cache"]
            cache_config = CacheConfig(
                local=LocalCacheConfig(**cache_data.get("local", {})),
                redis=RedisCacheConfig(**cache_data.get("redis", {}))
            )
            config_dict["cache"] = cache_config

        # CORS 配置
        if "cors" in yaml_config:
            config_dict["cors"] = CORSConfig(**yaml_config["cors"])

        # OSS 配置
        if "oss" in yaml_config:
            oss_data = yaml_config["oss"]
            oss_config = OSSConfig(
                access_key_id=oss_data.get("access_key_id", ""),
                access_key_secret=oss_data.get("access_key_secret", ""),
                endpoint=oss_data.get("endpoint", "oss-cn-hangzhou.aliyuncs.com"),
                bucket_name=oss_data.get("bucket_name", ""),
                internal_endpoint=oss_data.get("internal_endpoint", ""),
                use_https=oss_data.get("use_https", True),
                connect_timeout=oss_data.get("connect_timeout", 30),
                upload=OSSUploadConfig(**oss_data.get("upload", {})),
                download=OSSDownloadConfig(**oss_data.get("download", {})),
                url_expire_seconds=oss_data.get("url_expire_seconds", 3600)
            )
            config_dict["oss"] = oss_config

        return config_dict

    @classmethod
    def _apply_env_overrides(cls, config_dict: Dict, yaml_config: Dict) -> Dict:
        """
        应用环境变量覆盖

        环境变量格式: WIZYELAB_SECTION_KEY=value
        例如: WIZYELAB_DATABASE_HOST=localhost
        """
        env_prefix = "WIZYELAB_"

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                parts = key[len(env_prefix):].lower().split("_")
                if len(parts) >= 2:
                    section = parts[0]
                    field = "_".join(parts[1:])

                    # 解析值
                    parsed_value = cls._parse_env_value(value)

                    # 更新配置
                    if section in config_dict and hasattr(config_dict[section], field):
                        setattr(config_dict[section], field, parsed_value)

        return config_dict

    @staticmethod
    def _parse_env_value(value: str) -> Any:
        """
        解析环境变量值，支持布尔值和数字

        Args:
            value: 环境变量值

        Returns:
            解析后的值
        """
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        elif value.lower() in ("false", "0", "no", "off"):
            return False
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value


# 全局配置实例
settings = Settings.load_from_yaml()
