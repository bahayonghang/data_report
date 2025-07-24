# GEMINI.md

This file provides guidance to Gemini Code (gemini.ai/code) when working with code in this repository.

## AI助手核心规则
- 请始终保持对话语言为中文。
- 请在生成或编辑代码时补充详细的中文注释。
- 在回答用户问题时，请详细解释每一步改动的原因。
- 错误信息和调试信息优先使用中文解释。
- 使用`uv run`执行python代码。

## 项目概述

一个基于 FastAPI 的 Web 数据分析和报告工具，专门为时间序列数据设计。系统提供文件上传、自动数据分析、可视化图表生成和历史记录管理功能。

### 核心特性
- 支持 CSV 和 Parquet 文件格式
- 自动时间列检测和时间序列分析
- 实时生成统计报告和交互式图表
- 文件历史记录和分析结果缓存
- 响应式 Web 界面

## 开发环境命令

### 使用 uv（推荐）

```bash
# 安装依赖
uv sync

# 开发模式启动服务器
uv run uvicorn main:app --reload

# 运行测试
uv run pytest

# 代码格式化和检查
uv run ruff format .
uv run ruff check .

# 安装开发依赖
uv sync --group dev

# 构建文档
uv sync --group docs
uv run mkdocs serve
```

### 传统方式

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .

# 启动开发服务器
uvicorn main:app --reload
```

### Docker 部署

```bash
# 使用 Docker Compose 构建和启动全栈服务
docker-compose up --build

# 仅构建应用容器
docker build -t data-report .

# 启动监控服务 (可选)
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

## 测试

### 单元测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_basic_stats.py

# 运行带覆盖率的测试
uv run pytest --cov=src/reporter

# 详细输出
uv run pytest -v
```

### 端到端测试
```bash
# 运行 E2E 测试（需要先安装 Playwright）
uv run playwright install
uv run pytest tests/e2e/
```

### 数据库相关
```bash
# 初始化数据库
python scripts/init_database.py

# 路径分隔符修复（跨平台兼容）
python scripts/fix_path_separators.py
```

## 项目架构

### 整体架构
```
FastAPI (main.py) 
├── 前端 (templates/, static/)
├── 核心业务逻辑 (src/reporter/)
├── 数据持久化 (SQLite + 文件存储)
└── 容器化部署 (Docker + Nginx + 监控)
```

### 核心组件关系

**数据流向**: 文件上传 → 数据加载 → 分析引擎 → 可视化 → 结果存储 → Web 展示

1. **文件处理管道** (`data_loader.py` + `file_manager.py`)
   - 支持大文件流式处理和内存优化
   - 自动时间列检测（基于列名模式和数据类型）
   - 数据预处理和采样策略

2. **分析引擎** (`analysis/`)
   - `basic_stats.py`: 描述性统计、缺失值分析、异常值检测
   - `time_series.py`: 时间范围计算、ADF 平稳性检验
   - `correlation.py`: 相关性矩阵计算

3. **可视化系统** (`visualization/`)
   - 基于 Plotly 的交互式图表生成
   - 响应式设计适配和主题系统
   - 支持时序图、热力图、分布图、箱形图

4. **数据库层** (`database.py`)
   - SQLite 数据库，支持文件记录和分析历史
   - 文件去重机制（基于 SHA256 哈希）
   - 异步数据库操作和连接管理

5. **安全层** (`security.py`)
   - 路径遍历攻击防护
   - 文件类型和大小验证
   - 文件名清理和安全化

### 关键架构特性

**内存管理**: 
- 大数据集自动采样（默认10万行）
- Polars lazy evaluation 和流式处理
- 分析结果文件化存储避免内存占用

**并发处理**:
- FastAPI 异步路由处理
- 数据库异步操作（aiosqlite）
- 文件 I/O 异步操作

**缓存机制**:
- 基于文件哈希的重复分析避免
- 分析结果持久化存储
- 历史记录快速检索

**错误处理**:
- 分层异常处理（HTTP、验证、通用）
- 结构化错误响应格式
- 操作日志记录

## 关键配置

### 环境变量
```bash
PORT=8000                           # 服务端口
HOST=0.0.0.0                       # 服务主机
DATA_DIRECTORY=./data               # 数据存储目录
MAX_MEMORY_MB=2048                  # 内存限制
MEMORY_WARNING_THRESHOLD_MB=1500    # 内存警告阈值
LOG_LEVEL=INFO                      # 日志级别
ENVIRONMENT=production              # 运行环境
```

### 文件限制
- 支持格式：CSV, Parquet
- 最大文件大小：1GB
- 最大处理行数：100万行（大文件自动采样）

### 数据库
- SQLite 数据库：`data/database/history.db`
- 自动创建表结构和索引
- 支持文件记录和分析历史管理

## API 端点

### 主要 API
- `POST /api/upload-and-analyze` - 文件上传和分析
- `GET /api/file-history` - 获取文件历史记录
- `GET /api/files/{file_id}/analysis` - 获取文件分析历史
- `GET /api/analysis/{analysis_id}/result` - 获取分析结果详情
- `DELETE /api/history/{history_id}` - 删除历史记录
- `POST /api/search` - 搜索文件

### 页面路由
- `/` - 主页（文件上传界面）
- `/analysis` - 分析结果页面
- `/health` - 健康检查
- `/docs` - API 文档（Swagger UI）

## 常见开发任务

### 添加新的分析功能
1. 在 `src/reporter/analysis/` 下创建新模块
2. 在 `main.py` 的 `analyze_data_file()` 函数中集成
3. 更新前端 JavaScript 处理逻辑
4. 添加相应的单元测试

### 添加新的图表类型
1. 在 `src/reporter/visualization/charts.py` 中添加函数
2. 更新 `theme.py` 配置（如需要）
3. 在前端 `static/app.js` 中添加渲染逻辑

### 数据库模式变更
1. 修改 `src/reporter/database.py` 中的表结构
2. 运行 `python scripts/init_database.py` 重新初始化
3. 更新相关的数据模型和操作函数

### 添加新的文件格式支持
1. 更新 `security.py` 中的 `ALLOWED_EXTENSIONS`
2. 在 `data_loader.py` 中添加新格式的加载逻辑
3. 更新文件类型验证和错误消息

## 故障排除

### 常见问题
- **内存不足**: 检查 `MAX_MEMORY_MB` 设置，考虑增加采样限制
- **数据库锁定**: 确保正确关闭数据库连接，检查异步操作
- **文件上传失败**: 验证文件大小和格式，检查磁盘空间
- **图表渲染异常**: 检查 Plotly 版本兼容性，验证数据格式

### Nginx 代理配置
```nginx
# 大文件上传支持
client_max_body_size 1G;
proxy_read_timeout 300s;
proxy_send_timeout 300s;
```

### 性能优化建议
- 启用 Polars 的 lazy evaluation
- 使用数据采样减少内存占用
- 定期清理历史分析文件
- 监控内存使用情况