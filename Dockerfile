# 生产环境Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir uvicorn[standard] gunicorn

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs data static templates

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV LOG_LEVEL=INFO
ENV MAX_MEMORY_MB=2048
ENV MEMORY_WARNING_THRESHOLD_MB=1500

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--max-requests", "1000", "--max-requests-jitter", "100"]