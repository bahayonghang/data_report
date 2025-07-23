# 部署指南

本文档提供数据分析报告系统的完整部署指南，涵盖开发、测试和生产环境的部署方案。

## 部署概览

数据分析报告系统支持多种部署方式，以满足不同的使用场景和需求：

```mermaid
graph TB
    subgraph Development["开发环境"]
        A["本地开发"]
        B["热重载"]
        C["调试模式"]
    end
    
    subgraph Testing["测试环境"]
        D["集成测试"]
        E["性能测试"]
        F["安全测试"]
    end
    
    subgraph Production["生产环境"]
        G["Docker部署"]
        H["Kubernetes部署"]
        I["云平台部署"]
    end
    
    A --> D
    B --> E
    C --> F
    D --> G
    E --> H
    F --> I
```

## 系统要求

### 最低系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Linux/Windows/macOS | Ubuntu 20.04+ / CentOS 8+ |
| **CPU** | 2核心 | 4核心+ |
| **内存** | 4GB RAM | 8GB+ RAM |
| **存储** | 10GB 可用空间 | 50GB+ SSD |
| **网络** | 100Mbps | 1Gbps+ |
| **Python** | 3.11+ | 3.11+ |

### 软件依赖

- **Python 3.11+**: 核心运行环境
- **uv**: 包管理器
- **Docker** (可选): 容器化部署
- **Nginx** (可选): 反向代理
- **Systemd** (Linux): 服务管理

## 部署方式

### 1. 直接部署

#### 步骤1: 环境准备

```bash
# 安装Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 创建系统用户
sudo useradd -r -s /bin/false datareport
sudo mkdir -p /opt/data-report
sudo chown datareport:datareport /opt/data-report
```

#### 步骤2: 应用部署

```bash
# 切换到部署目录
cd /opt/data-report

# 克隆项目
sudo -u datareport git clone https://github.com/your-org/data-report.git .

# 安装依赖
sudo -u datareport uv sync --frozen

# 配置环境变量
sudo -u datareport cp .env.example .env
sudo -u datareport nano .env
```

#### 步骤3: 系统服务配置

创建systemd服务文件：

```ini
# /etc/systemd/system/data-report.service
[Unit]
Description=Data Analysis Report System
After=network.target

[Service]
Type=exec
User=datareport
Group=datareport
WorkingDirectory=/opt/data-report
Environment=PATH=/opt/data-report/.venv/bin
ExecStart=/opt/data-report/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable data-report
sudo systemctl start data-report

# 检查服务状态
sudo systemctl status data-report
```

### 2. Docker部署

#### 单容器部署

```bash
# 构建镜像
docker build -t data-report:latest .

# 运行容器
docker run -d \
  --name data-report \
  -p 8000:8000 \
  -v /path/to/data:/app/data \
  -v /path/to/config:/app/config \
  --env-file .env \
  data-report:latest
```

#### Docker Compose部署

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

volumes:
  prometheus_data:
```

启动服务：

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f app
```

### 3. Kubernetes部署

#### 命名空间配置

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: data-report
  labels:
    name: data-report
```

#### 配置映射

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-report-config
  namespace: data-report
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  MAX_FILE_SIZE: "100MB"
  ALLOWED_EXTENSIONS: "csv,parquet"
```

#### 密钥配置

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: data-report-secret
  namespace: data-report
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  DATABASE_URL: <base64-encoded-db-url>
```

#### 部署配置

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-report
  namespace: data-report
  labels:
    app: data-report
spec:
  replicas: 3
  selector:
    matchLabels:
      app: data-report
  template:
    metadata:
      labels:
        app: data-report
    spec:
      containers:
      - name: data-report
        image: data-report:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: data-report-config
        - secretRef:
            name: data-report-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: data-report-pvc
      - name: logs-volume
        emptyDir: {}
```

#### 服务配置

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: data-report-service
  namespace: data-report
spec:
  selector:
    app: data-report
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress配置

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: data-report-ingress
  namespace: data-report
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: 100m
spec:
  tls:
  - hosts:
    - data-report.example.com
    secretName: data-report-tls
  rules:
  - host: data-report.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: data-report-service
            port:
              number: 80
```

部署到Kubernetes：

```bash
# 应用所有配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n data-report
kubectl get services -n data-report
kubectl get ingress -n data-report

# 查看日志
kubectl logs -f deployment/data-report -n data-report
```

## 反向代理配置

### Nginx配置

```nginx
# /etc/nginx/sites-available/data-report
server {
    listen 80;
    server_name data-report.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name data-report.example.com;

    # SSL配置
    ssl_certificate /etc/ssl/certs/data-report.crt;
    ssl_certificate_key /etc/ssl/private/data-report.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 文件上传大小限制
    client_max_body_size 100M;

    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件缓存
    location /static/ {
        alias /opt/data-report/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

启用站点：

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/data-report /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx
```

## 环境配置

### 生产环境配置

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=4

# 安全配置
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=data-report.example.com
CORS_ORIGINS=https://data-report.example.com

# 文件配置
DATA_DIR=/app/data
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=100MB
ALLOWED_EXTENSIONS=csv,parquet

# 数据库配置（如果使用）
DATABASE_URL=postgresql://user:password@localhost:5432/datareport

# 缓存配置
REDIS_URL=redis://localhost:6379/0

# 监控配置
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# 日志配置
LOG_FILE=/app/logs/app.log
LOG_ROTATION=daily
LOG_RETENTION=30
```

### 安全配置

```bash
# 设置文件权限
sudo chown -R datareport:datareport /opt/data-report
sudo chmod -R 755 /opt/data-report
sudo chmod 600 /opt/data-report/.env

# 配置防火墙
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 监控和日志

### Prometheus监控

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'data-report'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 日志配置

```python
# logging.conf
[loggers]
keys=root,app

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_app]
level=INFO
handlers=fileHandler,rotatingFileHandler
qualname=app
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=detailedFormatter
args=('/app/logs/app.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('/app/logs/app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s
```

## 备份和恢复

### 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/data-report"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="data-report-backup-$DATE.tar.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用数据
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    /opt/data-report/data \
    /opt/data-report/config \
    /opt/data-report/.env

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "data-report-backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/$BACKUP_FILE"
```

### 自动备份

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/data-report/scripts/backup.sh
```

## 性能优化

### 应用优化

1. **工作进程数量**
   ```bash
   # 根据CPU核心数设置
   WORKERS=$(nproc)
   uvicorn src.main:app --workers $WORKERS
   ```

2. **内存优化**
   ```python
   # 配置Polars内存使用
   import polars as pl
   pl.Config.set_streaming_chunk_size(1000)
   ```

3. **缓存配置**
   ```python
   # 启用结果缓存
   CACHE_ENABLED=true
   CACHE_TTL=3600
   ```

### 系统优化

```bash
# 调整系统参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog=65535' >> /etc/sysctl.conf
sysctl -p

# 调整文件描述符限制
echo '* soft nofile 65535' >> /etc/security/limits.conf
echo '* hard nofile 65535' >> /etc/security/limits.conf
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查日志
   sudo journalctl -u data-report -f
   
   # 检查端口占用
   sudo netstat -tlnp | grep 8000
   
   # 检查权限
   ls -la /opt/data-report
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   free -h
   top -p $(pgrep -f uvicorn)
   
   # 调整工作进程数
   systemctl edit data-report
   ```

3. **文件上传失败**
   ```bash
   # 检查磁盘空间
   df -h
   
   # 检查文件权限
   ls -la /opt/data-report/uploads
   
   # 检查Nginx配置
   nginx -t
   ```

### 健康检查

```bash
#!/bin/bash
# health-check.sh

# 检查服务状态
if ! systemctl is-active --quiet data-report; then
    echo "Service is not running"
    exit 1
fi

# 检查HTTP响应
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Health check failed"
    exit 1
fi

# 检查磁盘空间
USAGE=$(df /opt/data-report | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 90 ]; then
    echo "Disk usage is high: ${USAGE}%"
    exit 1
fi

echo "All checks passed"
```

## 更新和维护

### 应用更新

```bash
#!/bin/bash
# update.sh

# 备份当前版本
./backup.sh

# 拉取最新代码
cd /opt/data-report
sudo -u datareport git pull origin main

# 更新依赖
sudo -u datareport uv sync

# 重启服务
sudo systemctl restart data-report

# 验证更新
sleep 10
if systemctl is-active --quiet data-report; then
    echo "Update successful"
else
    echo "Update failed, rolling back"
    # 回滚逻辑
fi
```

### 维护计划

- **每日**: 检查服务状态和日志
- **每周**: 检查系统资源使用情况
- **每月**: 更新系统包和安全补丁
- **每季度**: 性能评估和优化
- **每年**: 安全审计和架构评估

通过遵循这个部署指南，您可以成功地在各种环境中部署和维护数据分析报告系统。