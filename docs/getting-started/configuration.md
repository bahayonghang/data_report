# 配置说明

本文档详细介绍数据分析报告系统的各种配置选项和自定义设置。

## 环境变量配置

### 基础配置文件

系统使用 `.env` 文件进行配置。首先复制示例配置文件：

```bash
cp .env.example .env
```

### 核心配置项

#### 服务器配置
```bash
# 服务器绑定地址
HOST=0.0.0.0

# 服务器端口
PORT=8000

# 工作进程数（生产环境）
WORKERS=4

# 是否启用重载（开发环境）
RELOAD=true
```

#### 数据目录配置
```bash
# 数据文件存储目录
DATA_DIRECTORY=./data

# 临时文件目录
TEMP_DIRECTORY=./temp

# 上传文件目录
UPLOAD_DIRECTORY=./uploads
```

#### 安全配置
```bash
# 最大文件大小（字节）
MAX_FILE_SIZE=1073741824  # 1GB

# 允许的文件扩展名
ALLOWED_EXTENSIONS=.csv,.parquet

# 允许的MIME类型
ALLOWED_MIME_TYPES=text/csv,application/octet-stream

# 是否启用文件类型检查
ENABLE_FILE_TYPE_CHECK=true

# 是否启用路径验证
ENABLE_PATH_VALIDATION=true
```

#### 性能配置
```bash
# 最大内存使用量（MB）
MAX_MEMORY_MB=2048

# 数据处理块大小
CHUNK_SIZE=10000

# 是否启用数据缓存
ENABLE_CACHE=true

# 缓存过期时间（秒）
CACHE_EXPIRE_SECONDS=3600
```

#### 日志配置
```bash
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=./logs/app.log

# 是否启用日志轮转
ENABLE_LOG_ROTATION=true

# 日志文件最大大小（MB）
LOG_MAX_SIZE_MB=100

# 保留的日志文件数量
LOG_BACKUP_COUNT=5
```

#### 分析配置
```bash
# 默认时间列名模式
TIME_COLUMN_PATTERNS=DateTime,tagTime,Date,Time,timestamp

# 是否自动检测时间列
AUTO_DETECT_TIME_COLUMN=true

# 统计分析的置信度
CONFIDENCE_LEVEL=0.95

# ADF检验的最大滞后期
ADF_MAX_LAGS=12
```

#### 可视化配置
```bash
# 默认图表主题
PLOT_THEME=plotly_white

# 图表默认宽度
PLOT_WIDTH=800

# 图表默认高度
PLOT_HEIGHT=600

# 是否启用图表交互
ENABLE_PLOT_INTERACTION=true

# 图表颜色方案
COLOR_PALETTE=viridis
```

## 应用配置

### FastAPI 配置

在 `main.py` 中可以自定义 FastAPI 应用配置：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="数据分析报告系统",
    description="Web-based automated data analysis and reporting tool",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 数据处理配置

#### Polars 配置
```python
import polars as pl

# 设置 Polars 配置
pl.Config.set_tbl_rows(20)  # 显示行数
pl.Config.set_tbl_cols(10)  # 显示列数
pl.Config.set_tbl_width_chars(120)  # 表格宽度
```

#### 内存管理配置
```python
# 在 src/reporter/memory_manager.py 中配置
MEMORY_CONFIG = {
    "max_memory_mb": 2048,
    "chunk_size": 10000,
    "enable_gc": True,
    "gc_threshold": 0.8
}
```

### 安全配置

#### 文件安全配置
```python
# 在 src/reporter/security.py 中配置
SECURITY_CONFIG = {
    "max_file_size": 1024 * 1024 * 1024,  # 1GB
    "allowed_extensions": [".csv", ".parquet"],
    "blocked_paths": ["..", "~", "/etc", "/var"],
    "enable_virus_scan": False,  # 需要额外配置
    "quarantine_suspicious_files": True
}
```

## 部署配置

### Docker 配置

#### Dockerfile 环境变量
```dockerfile
# 设置默认环境变量
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=4
ENV DATA_DIRECTORY=/app/data
ENV LOG_LEVEL=INFO
```

#### docker-compose.yml 配置
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DATA_DIRECTORY=/app/data
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 文件上传大小限制
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
    
    # 静态文件缓存
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Systemd 服务配置

```ini
[Unit]
Description=Data Report Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/data-report
Environment=PATH=/opt/data-report/venv/bin
ExecStart=/opt/data-report/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# 环境变量文件
EnvironmentFile=/opt/data-report/.env

# 安全配置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/data-report/data /opt/data-report/logs

[Install]
WantedBy=multi-user.target
```

## 监控配置

### Prometheus 配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'data-report'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### 日志配置

```python
# src/reporter/logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 1073741824,  # 1GB
            "backupCount": 5
        }
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        },
        "app": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

## 配置验证

### 配置检查脚本

```python
#!/usr/bin/env python3
# scripts/check_config.py

import os
import sys
from pathlib import Path

def check_config():
    """检查配置是否正确"""
    errors = []
    
    # 检查必需的环境变量
    required_vars = ['DATA_DIRECTORY', 'LOG_LEVEL']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # 检查目录是否存在
    data_dir = Path(os.getenv('DATA_DIRECTORY', './data'))
    if not data_dir.exists():
        errors.append(f"Data directory does not exist: {data_dir}")
    
    # 检查文件大小限制
    max_size = os.getenv('MAX_FILE_SIZE', '104857600')
    try:
        max_size_int = int(max_size)
        if max_size_int <= 0:
            errors.append("MAX_FILE_SIZE must be positive")
    except ValueError:
        errors.append("MAX_FILE_SIZE must be a valid integer")
    
    if errors:
        print("Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Configuration is valid!")

if __name__ == "__main__":
    check_config()
```

## 配置最佳实践

### 开发环境
```bash
# .env.development
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=DEBUG
ENABLE_CACHE=false
MAX_FILE_SIZE=10485760  # 10MB
```

### 测试环境
```bash
# .env.testing
HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=INFO
ENABLE_CACHE=true
MAX_FILE_SIZE=52428800  # 50MB
```

### 生产环境
```bash
# .env.production
HOST=0.0.0.0
PORT=8000
WORKERS=4
RELOAD=false
LOG_LEVEL=WARNING
ENABLE_CACHE=true
MAX_FILE_SIZE=104857600  # 100MB
ENABLE_FILE_TYPE_CHECK=true
ENABLE_PATH_VALIDATION=true
```

## 故障排除

### 常见配置问题

1. **端口被占用**
   ```bash
   # 检查端口使用情况
   netstat -tulpn | grep :8000
   
   # 修改端口配置
   PORT=8080
   ```

2. **权限问题**
   ```bash
   # 确保数据目录有正确权限
   chmod 755 data/
   chown -R www-data:www-data data/
   ```

3. **内存不足**
   ```bash
   # 减少内存使用
   MAX_MEMORY_MB=1024
   CHUNK_SIZE=5000
   ```

### 配置调试

```python
# 添加到 main.py 开头用于调试
import os
print("Current configuration:")
for key, value in os.environ.items():
    if key.startswith(('HOST', 'PORT', 'DATA_', 'LOG_', 'MAX_')):
        print(f"  {key}={value}")
```

## 下一步

- 查看[架构设计](../architecture/overview.md)了解系统架构
- 阅读[部署指南](../deployment/deployment.md)了解生产部署
- 参考[故障排除](../deployment/troubleshooting.md)解决常见问题