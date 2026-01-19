# =============================================================================
# Wizyelab Web Start - Dockerfile
# 多阶段构建，优化镜像大小
# =============================================================================

# -----------------------------------------------------------------------------
# 阶段 1: 构建阶段
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION=1.7.1
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 导出依赖到 requirements.txt（不包含开发依赖）
RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt

# -----------------------------------------------------------------------------
# 阶段 2: 运行阶段
# -----------------------------------------------------------------------------
FROM python:3.11-slim as runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 创建非 root 用户
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 requirements.txt
COPY --from=builder /app/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup config ./config
COPY --chown=appuser:appgroup main.py .

# 创建日志目录
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/livez || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
