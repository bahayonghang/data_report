# Docker 部署指南

本文档详细说明如何使用Docker部署数据分析报告系统。

## 概述

Docker部署提供了以下优势：

- **环境一致性**: 确保开发、测试和生产环境的一致性
- **快速部署**: 简化部署流程，减少配置错误
- **资源隔离**: 提供良好的资源隔离和安全性
- **扩展性**: 支持水平扩展和负载均衡
- **版本管理**: 便于版本回滚和更新

## 前置要求

### 系统要求

- **CPU**: 2核心以上
- **内存**: 4GB以上（推荐8GB）
- **存储**: 20GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求

- **Docker**: 20.10.0 或更高版本
- **Docker Compose**: 2.0.0 或更高版本
- **Git**: 用于克隆项目代码

### 安装Docker

#### Windows

1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 运行安装程序并按照提示完成安装
3. 启动Docker Desktop
4. 验证安装：

```powershell
docker --version
docker-compose --version
```

#### macOS

1. 下载 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 拖拽到Applications文件夹
3. 启动Docker Desktop
4. 验证安装：

```bash
docker --version
docker-compose --version
```

#### Linux (Ubuntu)

```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置稳定版仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组（可选）
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker compose version
```

## 项目结构

```
data_report/
├── Dockerfile              # 主应用Dockerfile
├── docker-compose.yml      # 开发环境配置
├── docker-compose.prod.yml # 生产环境配置
├── .dockerignore           # Docker忽略文件
├── docker/                 # Docker相关文件
│   ├── nginx/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   ├── postgres/
│   │   └── init.sql
│   └── scripts/
│       ├── entrypoint.sh
│       └── wait-for-it.sh
├── src/                    # 应用源码
└── docs/                   # 文档
```

## Dockerfile

### 主应用Dockerfile

```dockerfile
# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 创建应用用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装Python依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY src/ ./src/
COPY docker/scripts/entrypoint.sh ./

# 设置权限
RUN chmod +x entrypoint.sh && \
    chown -R appuser:appuser /app

# 创建数据目录
RUN mkdir -p /app/data /app/uploads /app/logs && \
    chown -R appuser:appuser /app/data /app/uploads /app/logs

# 切换到应用用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 多阶段构建（生产优化）

```dockerfile
# 构建阶段
FROM python:3.11-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 运行阶段
FROM python:3.11-slim as runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser \
    && useradd -r -g appuser appuser

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY src/ ./src/
COPY docker/scripts/entrypoint.sh ./

RUN chmod +x entrypoint.sh && \
    mkdir -p /app/data /app/uploads /app/logs && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose配置

### 开发环境 (docker-compose.yml)

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - RELOAD=true
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/data_report
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./src:/app/src
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=data_report
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped

  nginx:
    build:
      context: ./docker/nginx
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
    depends_on:
      - app
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### 生产环境 (docker-compose.prod.yml)

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - WORKERS=4
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - app_data:/app/data
      - app_uploads:/app/uploads
      - app_logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped

  nginx:
    build:
      context: ./docker/nginx
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - app_static:/var/www/static
    depends_on:
      - app
    networks:
      - app-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  app_data:
  app_uploads:
  app_logs:
  app_static:
  prometheus_data:
  grafana_data:

networks:
  app-network:
    driver: bridge
```

## 启动脚本

### entrypoint.sh

```bash
#!/bin/bash
set -e

# 等待数据库就绪
if [ "$DATABASE_URL" ]; then
    echo "等待数据库连接..."
    python -c "
import time
import psycopg2
from urllib.parse import urlparse

url = urlparse('$DATABASE_URL')
while True:
    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )
        conn.close()
        print('数据库连接成功')
        break
    except psycopg2.OperationalError:
        print('等待数据库...')
        time.sleep(1)
"
fi

# 运行数据库迁移（如果需要）
if [ "$ENVIRONMENT" = "production" ]; then
    echo "运行数据库迁移..."
    python -m alembic upgrade head
fi

# 创建必要的目录
mkdir -p /app/data /app/uploads /app/logs

# 启动应用
echo "启动应用..."
exec "$@"
```

### wait-for-it.sh

```bash
#!/usr/bin/env bash
# wait-for-it.sh: 等待服务可用的脚本

USAGE="Usage: $0 host:port [-s] [-t timeout] [-- command args]"
HOST=""
PORT=""
TIMEOUT=15
STRICT=0
CHILD=0
QUIET=0

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        *:* )
        hostport=(${1//:/ })
        HOST=${hostport[0]}
        PORT=${hostport[1]}
        shift 1
        ;;
        -s | --strict)
        STRICT=1
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -t)
        TIMEOUT="$2"
        if [[ $TIMEOUT == "" ]]; then break; fi
        shift 2
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        CLI=("$@")
        break
        ;;
        --help)
        echo $USAGE
        exit 0
        ;;
        *)
        echo "Unknown argument: $1"
        echo $USAGE
        exit 1
        ;;
    esac
done

if [[ "$HOST" == "" || "$PORT" == "" ]]; then
    echo "Error: you need to provide a host and port to test."
    echo $USAGE
    exit 1
fi

# 等待服务可用
wait_for() {
    if [[ $TIMEOUT -gt 0 ]]; then
        echo "Waiting $TIMEOUT seconds for $HOST:$PORT"
    else
        echo "Waiting for $HOST:$PORT without a timeout"
    fi
    
    start_ts=$(date +%s)
    while :
    do
        if [[ $TIMEOUT -gt 0 ]]; then
            result=$(timeout $TIMEOUT bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null)
        else
            result=$(bash -c "</dev/tcp/$HOST/$PORT" 2>/dev/null)
        fi
        
        if [[ $? -eq 0 ]]; then
            end_ts=$(date +%s)
            echo "$HOST:$PORT is available after $((end_ts - start_ts)) seconds"
            break
        fi
        sleep 1
    done
    return 0
}

wait_for

# 执行命令
if [[ $CLI != "" ]]; then
    exec "${CLI[@]}"
fi
```

## 部署步骤

### 1. 准备环境

```bash
# 克隆项目
git clone https://github.com/your-username/data_report.git
cd data_report

# 创建环境配置文件
cp .env.example .env.prod

# 编辑生产环境配置
nano .env.prod
```

### 2. 配置环境变量

```env
# .env.prod
ENVIRONMENT=production
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://username:password@postgres:5432/data_report
POSTGRES_DB=data_report
POSTGRES_USER=username
POSTGRES_PASSWORD=secure_password

# Redis配置
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 应用配置
WORKERS=4
MAX_FILE_SIZE=104857600
MAX_MEMORY_USAGE=2147483648

# 监控配置
GRAFANA_PASSWORD=admin_password
```

### 3. 开发环境部署

```bash
# 构建并启动服务
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 生产环境部署

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f app

# 扩展应用实例
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

## 常用命令

### 容器管理

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 进入容器
docker exec -it data_report_app_1 bash

# 查看容器日志
docker logs data_report_app_1

# 重启容器
docker restart data_report_app_1

# 停止容器
docker stop data_report_app_1

# 删除容器
docker rm data_report_app_1
```

### 镜像管理

```bash
# 查看镜像
docker images

# 构建镜像
docker build -t data_report:latest .

# 删除镜像
docker rmi data_report:latest

# 清理未使用的镜像
docker image prune

# 清理所有未使用的资源
docker system prune -a
```

### 数据管理

```bash
# 查看数据卷
docker volume ls

# 备份数据卷
docker run --rm -v data_report_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v data_report_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data

# 删除数据卷
docker volume rm data_report_postgres_data
```

## 监控和日志

### 健康检查

```bash
# 检查应用健康状态
curl http://localhost:8000/health

# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' data_report_app_1
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f app

# 查看最近的日志
docker-compose logs --tail=100 app

# 查看特定时间的日志
docker-compose logs --since="2024-01-15T10:00:00" app
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看特定容器的资源使用
docker stats data_report_app_1

# 查看容器进程
docker top data_report_app_1
```

## 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看详细错误信息
docker-compose logs app

# 检查配置文件
docker-compose config

# 重新构建镜像
docker-compose build --no-cache app
```

#### 2. 数据库连接失败

```bash
# 检查数据库容器状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 测试数据库连接
docker exec -it data_report_postgres_1 psql -U postgres -d data_report
```

#### 3. 端口冲突

```bash
# 查看端口使用情况
netstat -tulpn | grep :8000

# 修改端口映射
# 在docker-compose.yml中修改ports配置
ports:
  - "8001:8000"  # 使用8001端口
```

#### 4. 磁盘空间不足

```bash
# 清理Docker资源
docker system prune -a

# 清理未使用的数据卷
docker volume prune

# 查看磁盘使用情况
docker system df
```

### 调试技巧

```bash
# 进入容器调试
docker exec -it data_report_app_1 bash

# 查看环境变量
docker exec data_report_app_1 env

# 查看文件系统
docker exec data_report_app_1 ls -la /app

# 运行临时容器进行调试
docker run --rm -it --entrypoint bash data_report:latest
```

## 安全最佳实践

### 1. 镜像安全

- 使用官方基础镜像
- 定期更新基础镜像
- 扫描镜像漏洞
- 使用多阶段构建减少攻击面

### 2. 容器安全

- 以非root用户运行
- 限制容器权限
- 使用只读文件系统
- 设置资源限制

### 3. 网络安全

- 使用自定义网络
- 限制端口暴露
- 配置防火墙规则
- 使用TLS加密

### 4. 数据安全

- 加密敏感数据
- 定期备份数据
- 使用密钥管理服务
- 限制数据访问权限

## 性能优化

### 1. 镜像优化

```dockerfile
# 使用.dockerignore减少构建上下文
# .dockerignore
.git
.pytest_cache
__pycache__
*.pyc
.coverage
htmlcov
node_modules
.env
README.md
```

### 2. 容器优化

```yaml
# 设置资源限制
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 3. 网络优化

```yaml
# 使用host网络模式（仅限Linux）
network_mode: host

# 或者优化bridge网络
networks:
  app-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-app
```

## 备份和恢复

### 数据库备份

```bash
# 创建备份脚本
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建数据库备份
docker exec data_report_postgres_1 pg_dump -U postgres data_report > "$BACKUP_DIR/db_backup_$DATE.sql"

# 压缩备份文件
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

### 应用数据备份

```bash
# 备份上传文件
tar czf uploads_backup_$(date +%Y%m%d).tar.gz -C /var/lib/docker/volumes/data_report_app_uploads/_data .

# 备份应用数据
tar czf data_backup_$(date +%Y%m%d).tar.gz -C /var/lib/docker/volumes/data_report_app_data/_data .
```

### 自动化备份

```bash
# 添加到crontab
# 每天凌晨2点执行备份
0 2 * * * /path/to/backup_script.sh

# 每周日凌晨3点执行完整备份
0 3 * * 0 /path/to/full_backup_script.sh
```

## 更新和回滚

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build app

# 滚动更新（零停机）
docker-compose up -d --no-deps app

# 验证更新
curl http://localhost:8000/health
```

### 版本回滚

```bash
# 回滚到指定版本
git checkout v1.0.0

# 重新构建和部署
docker-compose build app
docker-compose up -d --no-deps app
```

## 下一步

- [生产部署](production.md) - 了解生产环境部署的详细配置
- [监控指南](monitoring.md) - 学习如何监控应用性能
- [安全指南](security.md) - 了解安全最佳实践
- [故障排除](troubleshooting.md) - 常见问题的解决方案