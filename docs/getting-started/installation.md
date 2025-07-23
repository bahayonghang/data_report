# 安装指南

本指南将帮助您在本地环境中安装和配置数据分析报告系统。

## 系统要求

### 最低要求
- **操作系统**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.11 或更高版本
- **内存**: 4GB RAM（推荐 8GB+）
- **存储**: 2GB 可用空间
- **网络**: 互联网连接（用于下载依赖）

### 推荐配置
- **CPU**: 4核心或更多
- **内存**: 16GB RAM
- **存储**: SSD 硬盘

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-username/data_report.git
cd data_report
```

### 2. 安装 uv（推荐）

我们推荐使用 `uv` 作为包管理器，它比 pip 更快更可靠。

#### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. 安装项目依赖

#### 使用 uv（推荐）
```bash
# 安装所有依赖（包括开发和文档依赖）
uv sync --all-groups

# 或者只安装运行时依赖
uv sync

# 安装开发依赖
uv sync --group dev

# 安装文档依赖
uv sync --group docs
```

#### 使用 pip
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -e .
pip install -e ".[dev,docs]"
```

### 4. 环境配置

#### 创建环境变量文件
```bash
cp .env.example .env
```

#### 编辑 .env 文件
```bash
# 数据目录路径（可选，默认为 ./data）
DATA_DIRECTORY=./data

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 安全配置
MAX_FILE_SIZE=1GB
ALLOWED_EXTENSIONS=.csv,.parquet

# 日志级别
LOG_LEVEL=INFO
```

### 5. 验证安装

#### 运行测试
```bash
# 使用 uv
uv run pytest

# 使用 pip
pytest
```

#### 启动开发服务器
```bash
# 使用 uv
uv run uvicorn main:app --reload

# 使用 pip
uvicorn main:app --reload
```

#### 访问应用
打开浏览器访问 `http://localhost:8000`，您应该能看到应用的主页。

## Docker 安装（可选）

如果您更喜欢使用 Docker，可以按照以下步骤操作：

### 1. 构建镜像
```bash
docker build -t data-report .
```

### 2. 运行容器
```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data data-report
```

### 3. 使用 Docker Compose
```bash
docker-compose up -d
```

## 常见问题

### Q: 安装依赖时出现网络错误
**A**: 可以尝试使用国内镜像源：

```bash
# 使用阿里云镜像
uv sync --index-url https://mirrors.aliyun.com/pypi/simple/

# 或使用清华镜像
uv sync --index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/
```

### Q: Python 版本不兼容
**A**: 请确保使用 Python 3.11 或更高版本：

```bash
python --version
```

如果版本过低，请升级 Python 或使用 pyenv 管理多个 Python 版本。

### Q: 权限错误
**A**: 在 Linux/macOS 上，可能需要使用 sudo 或调整文件权限：

```bash
# 调整数据目录权限
chmod 755 data/

# 或使用用户权限安装
pip install --user -e .
```

### Q: 端口被占用
**A**: 如果 8000 端口被占用，可以指定其他端口：

```bash
uvicorn main:app --port 8080
```

## 下一步

安装完成后，您可以：

1. 查看[基本使用指南](basic-usage.md)了解如何使用系统
2. 阅读[配置说明](configuration.md)了解详细配置选项
3. 查看[开发指南](../development/environment.md)了解如何参与开发

## 获取帮助

如果在安装过程中遇到问题：

1. 查看[故障排除指南](../deployment/troubleshooting.md)
2. 搜索或提交 [GitHub Issues](https://github.com/your-username/data_report/issues)
3. 联系开发团队