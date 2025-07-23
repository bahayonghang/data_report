# 故障排除指南

本文档提供数据分析报告系统常见问题的诊断和解决方案。

## 快速诊断

### 系统健康检查清单

```bash
#!/bin/bash
# quick-diagnosis.sh

echo "=== 数据分析报告系统健康检查 ==="
echo

# 1. 服务状态检查
echo "1. 检查服务状态:"
if systemctl is-active --quiet data-report; then
    echo "   ✓ 服务正在运行"
else
    echo "   ✗ 服务未运行"
    echo "   建议: sudo systemctl start data-report"
fi

# 2. 端口检查
echo "2. 检查端口占用:"
if netstat -tlnp | grep -q ":8000"; then
    echo "   ✓ 端口8000已监听"
else
    echo "   ✗ 端口8000未监听"
fi

# 3. 磁盘空间检查
echo "3. 检查磁盘空间:"
USAGE=$(df /opt/data-report 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo "0")
if [ "$USAGE" -lt 90 ]; then
    echo "   ✓ 磁盘空间充足 (${USAGE}%)"
else
    echo "   ⚠ 磁盘空间不足 (${USAGE}%)"
fi

# 4. 内存检查
echo "4. 检查内存使用:"
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -lt 90 ]; then
    echo "   ✓ 内存使用正常 (${MEM_USAGE}%)"
else
    echo "   ⚠ 内存使用过高 (${MEM_USAGE}%)"
fi

# 5. HTTP响应检查
echo "5. 检查HTTP响应:"
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "   ✓ HTTP服务正常"
else
    echo "   ✗ HTTP服务异常"
fi

echo
echo "=== 检查完成 ==="
```

## 启动问题

### 服务无法启动

#### 症状
- `systemctl start data-report` 失败
- 服务状态显示为 `failed`
- 无法访问Web界面

#### 诊断步骤

1. **查看服务状态**
   ```bash
   sudo systemctl status data-report
   ```

2. **查看详细日志**
   ```bash
   sudo journalctl -u data-report -f --no-pager
   ```

3. **检查配置文件**
   ```bash
   # 检查systemd服务文件
   sudo systemctl cat data-report
   
   # 检查环境变量文件
   sudo -u datareport cat /opt/data-report/.env
   ```

#### 常见原因和解决方案

**原因1: 端口被占用**
```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000

# 解决方案1: 杀死占用进程
sudo kill -9 <PID>

# 解决方案2: 更改端口
sudo -u datareport nano /opt/data-report/.env
# 修改 PORT=8001
```

**原因2: 权限问题**
```bash
# 检查文件权限
ls -la /opt/data-report/

# 修复权限
sudo chown -R datareport:datareport /opt/data-report
sudo chmod -R 755 /opt/data-report
sudo chmod 600 /opt/data-report/.env
```

**原因3: Python环境问题**
```bash
# 检查Python版本
sudo -u datareport /opt/data-report/.venv/bin/python --version

# 重新创建虚拟环境
sudo -u datareport rm -rf /opt/data-report/.venv
sudo -u datareport cd /opt/data-report && uv sync
```

**原因4: 依赖缺失**
```bash
# 检查依赖
sudo -u datareport cd /opt/data-report && uv sync --frozen

# 如果失败，尝试重新安装
sudo -u datareport cd /opt/data-report && uv sync
```

### 启动缓慢

#### 症状
- 服务启动时间超过30秒
- 启动过程中出现超时

#### 解决方案

1. **调整启动超时**
   ```bash
   sudo systemctl edit data-report
   ```
   添加内容：
   ```ini
   [Service]
   TimeoutStartSec=120
   ```

2. **优化启动配置**
   ```bash
   # 减少工作进程数
   sudo -u datareport nano /opt/data-report/.env
   # 设置 WORKERS=1
   ```

3. **检查系统资源**
   ```bash
   # 检查CPU和内存
   top
   free -h
   
   # 检查磁盘I/O
   iostat -x 1
   ```

## 性能问题

### 响应缓慢

#### 症状
- 页面加载时间超过5秒
- API响应时间过长
- 文件上传/分析缓慢

#### 诊断工具

1. **应用性能监控**
   ```bash
   # 查看进程资源使用
   top -p $(pgrep -f uvicorn)
   
   # 查看内存详情
   cat /proc/$(pgrep -f uvicorn)/status
   
   # 查看文件描述符使用
   lsof -p $(pgrep -f uvicorn) | wc -l
   ```

2. **网络性能测试**
   ```bash
   # 测试本地响应时间
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
   
   # curl-format.txt 内容:
   # time_namelookup:  %{time_namelookup}\n
   # time_connect:     %{time_connect}\n
   # time_appconnect:  %{time_appconnect}\n
   # time_pretransfer: %{time_pretransfer}\n
   # time_redirect:    %{time_redirect}\n
   # time_starttransfer: %{time_starttransfer}\n
   # time_total:       %{time_total}\n
   ```

#### 优化方案

1. **增加工作进程**
   ```bash
   # 根据CPU核心数调整
   CORES=$(nproc)
   sudo -u datareport nano /opt/data-report/.env
   # 设置 WORKERS=$CORES
   ```

2. **启用缓存**
   ```bash
   sudo -u datareport nano /opt/data-report/.env
   # 添加:
   # CACHE_ENABLED=true
   # CACHE_TTL=3600
   ```

3. **优化数据处理**
   ```python
   # 在配置中调整Polars设置
   POLARS_MAX_THREADS=4
   POLARS_STREAMING_CHUNK_SIZE=1000
   ```

### 内存不足

#### 症状
- 系统出现OOM (Out of Memory)
- 服务频繁重启
- 大文件处理失败

#### 诊断

```bash
# 查看内存使用情况
free -h
cat /proc/meminfo

# 查看进程内存使用
ps aux --sort=-%mem | head -10

# 查看系统日志中的OOM记录
sudo dmesg | grep -i "killed process"
sudo journalctl | grep -i "out of memory"
```

#### 解决方案

1. **增加系统内存**
   - 物理内存升级
   - 增加swap空间

2. **优化应用配置**
   ```bash
   # 限制文件大小
   sudo -u datareport nano /opt/data-report/.env
   # 设置 MAX_FILE_SIZE=50MB
   
   # 减少工作进程数
   # 设置 WORKERS=2
   
   # 启用流式处理
   # 设置 STREAMING_ENABLED=true
   ```

3. **配置内存限制**
   ```bash
   # 使用systemd限制内存
   sudo systemctl edit data-report
   ```
   添加：
   ```ini
   [Service]
   MemoryLimit=2G
   MemoryAccounting=yes
   ```

## 文件处理问题

### 文件上传失败

#### 症状
- 上传进度卡在某个百分比
- 收到"文件太大"错误
- 上传后文件损坏

#### 诊断步骤

1. **检查文件大小限制**
   ```bash
   # 检查应用配置
   grep MAX_FILE_SIZE /opt/data-report/.env
   
   # 检查Nginx配置
   sudo nginx -T | grep client_max_body_size
   
   # 检查系统限制
   ulimit -f
   ```

2. **检查磁盘空间**
   ```bash
   df -h /opt/data-report/uploads
   df -h /tmp
   ```

3. **检查权限**
   ```bash
   ls -la /opt/data-report/uploads/
   sudo -u datareport touch /opt/data-report/uploads/test.txt
   ```

#### 解决方案

1. **调整大小限制**
   ```bash
   # 应用配置
   sudo -u datareport nano /opt/data-report/.env
   # 修改 MAX_FILE_SIZE=200MB
   
   # Nginx配置
   sudo nano /etc/nginx/sites-available/data-report
   # 修改 client_max_body_size 200M;
   sudo nginx -s reload
   ```

2. **清理磁盘空间**
   ```bash
   # 清理临时文件
   sudo find /tmp -name "*.tmp" -mtime +1 -delete
   
   # 清理旧的上传文件
   sudo find /opt/data-report/uploads -mtime +7 -delete
   
   # 清理日志文件
   sudo journalctl --vacuum-time=7d
   ```

### 文件格式错误

#### 症状
- "不支持的文件格式"错误
- 文件解析失败
- 数据显示异常

#### 诊断

```bash
# 检查文件类型
file /path/to/uploaded/file

# 检查文件编码
file -i /path/to/uploaded/file

# 检查CSV文件结构
head -5 /path/to/uploaded/file

# 检查Parquet文件
python -c "import polars as pl; print(pl.read_parquet('/path/to/file').head())"
```

#### 解决方案

1. **文件格式转换**
   ```python
   # CSV编码转换
   import pandas as pd
   df = pd.read_csv('file.csv', encoding='gbk')
   df.to_csv('file_utf8.csv', encoding='utf-8', index=False)
   ```

2. **配置文件类型检测**
   ```bash
   sudo -u datareport nano /opt/data-report/.env
   # 添加 STRICT_FILE_VALIDATION=false
   ```

## 网络问题

### 无法访问Web界面

#### 症状
- 浏览器显示"连接被拒绝"
- 超时错误
- 502/503错误

#### 诊断步骤

1. **检查服务状态**
   ```bash
   sudo systemctl status data-report
   curl -I http://localhost:8000/health
   ```

2. **检查网络连接**
   ```bash
   # 检查端口监听
   sudo netstat -tlnp | grep 8000
   
   # 检查防火墙
   sudo ufw status
   sudo iptables -L
   ```

3. **检查Nginx配置**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

#### 解决方案

1. **修复服务**
   ```bash
   sudo systemctl restart data-report
   sudo systemctl restart nginx
   ```

2. **调整防火墙**
   ```bash
   sudo ufw allow 8000/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. **修复Nginx配置**
   ```bash
   sudo nano /etc/nginx/sites-available/data-report
   # 检查proxy_pass配置
   sudo nginx -s reload
   ```

### SSL/TLS问题

#### 症状
- 证书错误
- 连接不安全警告
- HTTPS无法访问

#### 诊断

```bash
# 检查证书
openssl x509 -in /etc/ssl/certs/data-report.crt -text -noout

# 检查证书有效期
openssl x509 -in /etc/ssl/certs/data-report.crt -noout -dates

# 测试SSL连接
openssl s_client -connect data-report.example.com:443
```

#### 解决方案

1. **更新证书**
   ```bash
   # 使用Let's Encrypt
   sudo certbot renew
   
   # 手动更新
   sudo cp new-cert.crt /etc/ssl/certs/data-report.crt
   sudo cp new-key.key /etc/ssl/private/data-report.key
   sudo nginx -s reload
   ```

## 数据库问题

### 连接失败

#### 症状
- "数据库连接失败"错误
- 应用启动时卡住
- 数据保存失败

#### 诊断

```bash
# 检查数据库服务
sudo systemctl status postgresql

# 测试连接
psql -h localhost -U username -d datareport

# 检查连接数
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

#### 解决方案

1. **重启数据库服务**
   ```bash
   sudo systemctl restart postgresql
   ```

2. **检查连接配置**
   ```bash
   sudo -u datareport nano /opt/data-report/.env
   # 检查 DATABASE_URL
   ```

3. **清理连接**
   ```sql
   -- 杀死空闲连接
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'idle' AND state_change < now() - interval '1 hour';
   ```

## 监控和告警

### 设置监控

```bash
# 创建监控脚本
cat > /opt/data-report/scripts/monitor.sh << 'EOF'
#!/bin/bash

# 检查服务状态
if ! systemctl is-active --quiet data-report; then
    echo "CRITICAL: Data Report service is down" | mail -s "Service Alert" admin@example.com
fi

# 检查磁盘空间
USAGE=$(df /opt/data-report | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 90 ]; then
    echo "WARNING: Disk usage is ${USAGE}%" | mail -s "Disk Alert" admin@example.com
fi

# 检查内存使用
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "WARNING: Memory usage is ${MEM_USAGE}%" | mail -s "Memory Alert" admin@example.com
fi
EOF

chmod +x /opt/data-report/scripts/monitor.sh

# 添加到crontab
echo "*/5 * * * * /opt/data-report/scripts/monitor.sh" | crontab -
```

### 日志分析

```bash
# 分析错误日志
grep -i error /opt/data-report/logs/app.log | tail -20

# 分析访问模式
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10

# 分析响应时间
awk '{print $NF}' /var/log/nginx/access.log | sort -n | tail -10
```

## 应急响应

### 服务完全不可用

1. **立即响应**
   ```bash
   # 检查基础服务
   sudo systemctl status data-report nginx
   
   # 快速重启
   sudo systemctl restart data-report nginx
   
   # 检查恢复状态
   curl -I http://localhost:8000/health
   ```

2. **如果重启无效**
   ```bash
   # 回滚到上一个版本
   cd /opt/data-report
   sudo -u datareport git log --oneline -5
   sudo -u datareport git reset --hard <previous-commit>
   sudo systemctl restart data-report
   ```

3. **启用维护模式**
   ```bash
   # 创建维护页面
   sudo nano /var/www/html/maintenance.html
   
   # 修改Nginx配置临时重定向
   sudo nano /etc/nginx/sites-available/data-report
   # 添加: return 503;
   sudo nginx -s reload
   ```

### 数据丢失

1. **立即停止服务**
   ```bash
   sudo systemctl stop data-report
   ```

2. **评估损失**
   ```bash
   ls -la /opt/data-report/data/
   ls -la /backup/data-report/
   ```

3. **恢复数据**
   ```bash
   # 从最近备份恢复
   cd /backup/data-report
   tar -xzf data-report-backup-latest.tar.gz -C /opt/data-report/
   sudo chown -R datareport:datareport /opt/data-report/data
   ```

## 预防措施

### 定期维护

```bash
# 创建维护脚本
cat > /opt/data-report/scripts/maintenance.sh << 'EOF'
#!/bin/bash

echo "开始定期维护..."

# 清理临时文件
find /tmp -name "*.tmp" -mtime +1 -delete
find /opt/data-report/uploads -mtime +7 -delete

# 清理日志
journalctl --vacuum-time=30d
find /opt/data-report/logs -name "*.log.*" -mtime +30 -delete

# 更新系统包
apt update && apt upgrade -y

# 重启服务（如果需要）
if [ -f /var/run/reboot-required ]; then
    echo "系统需要重启"
fi

echo "维护完成"
EOF

# 每周日凌晨3点执行
echo "0 3 * * 0 /opt/data-report/scripts/maintenance.sh" | crontab -
```

### 监控配置

```yaml
# prometheus/rules/data-report.yml
groups:
- name: data-report
  rules:
  - alert: ServiceDown
    expr: up{job="data-report"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Data Report service is down"
      
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      
  - alert: DiskSpaceLow
    expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Disk space is running low"
```

通过遵循这个故障排除指南，您可以快速诊断和解决数据分析报告系统中的各种问题，确保系统的稳定运行。