# 开发环境设置

本文档详细说明如何设置数据分析报告系统的开发环境。

## 系统要求

### 硬件要求

- **CPU**: 2核心以上，推荐4核心
- **内存**: 最低4GB，推荐8GB以上
- **存储**: 至少10GB可用空间
- **网络**: 稳定的互联网连接（用于下载依赖）

### 软件要求

- **操作系统**: 
  - Windows 10/11
  - macOS 10.15+
  - Linux (Ubuntu 20.04+, CentOS 8+)
- **Python**: 3.11 或更高版本
- **Git**: 2.30 或更高版本
- **Node.js**: 18+ (可选，用于前端开发工具)

## 开发工具安装

### 1. Python 环境

#### 使用 uv (推荐)

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或者使用 pip
pip install uv

# 验证安装
uv --version
```

#### 传统方式

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 2. 代码编辑器配置

#### VS Code (推荐)

安装以下扩展：

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml",
    "yzhang.markdown-all-in-one",
    "ms-vscode.vscode-json"
  ]
}
```

配置文件 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".coverage": true,
    "htmlcov": true
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

1. 打开项目目录
2. 配置Python解释器：`File > Settings > Project > Python Interpreter`
3. 启用代码格式化：`File > Settings > Tools > External Tools`
4. 配置测试运行器：`File > Settings > Tools > Python Integrated Tools`

## 项目设置

### 1. 克隆项目

```bash
# 克隆仓库
git clone https://github.com/your-username/data_report.git
cd data_report

# 查看分支
git branch -a

# 切换到开发分支（如果存在）
git checkout develop
```

### 2. 安装依赖

#### 使用 uv

```bash
# 安装所有依赖（包括开发依赖）
uv sync --all-groups

# 或者分别安装
uv sync                    # 核心依赖
uv sync --group dev        # 开发依赖
uv sync --group test       # 测试依赖
uv sync --group docs       # 文档依赖
```

#### 使用 pip

```bash
# 安装核心依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev,test,docs]"
```

### 3. 环境配置

创建环境配置文件：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
# Windows
notepad .env
# macOS/Linux
nano .env
```

基本配置示例：

```env
# 开发环境配置
ENVIRONMENT=development
DEBUG=true

# 服务器配置
HOST=127.0.0.1
PORT=8000
RELOAD=true

# 数据目录
DATA_DIR=./data
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# 日志配置
LOG_LEVEL=DEBUG
LOG_FILE=./logs/app.log

# 性能配置
MAX_FILE_SIZE=1073741824  # 1GB
MAX_MEMORY_USAGE=2147483648  # 2GB
WORKERS=1

# 开发工具
ENABLE_PROFILER=true
ENABLE_DEBUGGER=true
```

### 4. 数据库设置（如果需要）

```bash
# 创建数据目录
mkdir -p data/db

# 初始化数据库（如果使用SQLite）
python -c "from app.database import init_db; init_db()"
```

## 开发工作流

### 1. 代码质量检查

```bash
# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy src/

# 安全检查
uv run bandit -r src/
```

### 2. 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_analysis.py

# 运行特定测试函数
uv run pytest tests/test_analysis.py::test_basic_stats

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 查看覆盖率报告
# Windows
start htmlcov/index.html
# macOS
open htmlcov/index.html
# Linux
xdg-open htmlcov/index.html
```

### 3. 启动开发服务器

```bash
# 使用 uv
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

# 或者使用项目脚本
uv run python -m src.main

# 使用 FastAPI CLI（如果安装）
fastapi dev src/main.py
```

### 4. 调试配置

#### VS Code 调试配置

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
      ],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Pytest Debug",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v"
      ],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### PyCharm 调试配置

1. **FastAPI 配置**:
   - Script path: `uvicorn`
   - Parameters: `src.main:app --reload --host 127.0.0.1 --port 8000`
   - Working directory: 项目根目录

2. **Pytest 配置**:
   - Target: `Custom`
   - Additional Arguments: `-v`
   - Working directory: 项目根目录

## 开发最佳实践

### 1. 代码组织

```
src/
├── __init__.py
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── dependencies.py      # 依赖注入
├── exceptions.py        # 自定义异常
├── models/              # 数据模型
│   ├── __init__.py
│   ├── base.py
│   └── analysis.py
├── api/                 # API 路由
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── files.py
│   │   └── analysis.py
├── core/                # 核心业务逻辑
│   ├── __init__.py
│   ├── analysis.py
│   ├── visualization.py
│   └── statistics.py
├── utils/               # 工具函数
│   ├── __init__.py
│   ├── file_utils.py
│   └── data_utils.py
└── tests/               # 测试文件
    ├── __init__.py
    ├── conftest.py
    ├── test_api/
    ├── test_core/
    └── test_utils/
```

### 2. 编码规范

#### 命名约定

```python
# 类名：PascalCase
class DataAnalyzer:
    pass

# 函数和变量名：snake_case
def calculate_statistics(data_frame):
    result_dict = {}
    return result_dict

# 常量：UPPER_SNAKE_CASE
MAX_FILE_SIZE = 100 * 1024 * 1024
DEFAULT_CHUNK_SIZE = 10000

# 私有成员：前缀下划线
class DataProcessor:
    def __init__(self):
        self._cache = {}
        self.__secret_key = "private"
```

#### 文档字符串

```python
def analyze_data(df: pd.DataFrame, analysis_type: str = "basic") -> dict:
    """
    分析数据框并返回统计结果。
    
    Args:
        df: 要分析的数据框
        analysis_type: 分析类型，可选值：'basic', 'comprehensive'
        
    Returns:
        包含分析结果的字典，包含以下键：
        - basic_stats: 基本统计信息
        - visualizations: 可视化数据
        - insights: 数据洞察
        
    Raises:
        ValueError: 当数据框为空或分析类型无效时
        MemoryError: 当数据过大导致内存不足时
        
    Example:
        >>> df = pd.read_csv("data.csv")
        >>> result = analyze_data(df, "comprehensive")
        >>> print(result['insights'])
    """
    pass
```

#### 类型注解

```python
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import pandas as pd

def process_file(
    file_path: Union[str, Path],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Union[str, int, List[str]]]:
    """
    处理文件并返回结果。
    """
    if options is None:
        options = {}
    
    # 实现逻辑
    return {
        "status": "success",
        "rows": 1000,
        "columns": ["col1", "col2"]
    }
```

### 3. 错误处理

```python
# 自定义异常
class DataAnalysisError(Exception):
    """数据分析相关错误的基类"""
    pass

class FileFormatError(DataAnalysisError):
    """文件格式错误"""
    pass

class InsufficientDataError(DataAnalysisError):
    """数据不足错误"""
    pass

# 错误处理示例
def load_data(file_path: str) -> pd.DataFrame:
    """
    加载数据文件。
    """
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            raise FileFormatError(f"不支持的文件格式: {file_path}")
        
        if df.empty:
            raise InsufficientDataError("数据文件为空")
        
        return df
        
    except pd.errors.EmptyDataError:
        raise InsufficientDataError("数据文件为空")
    except pd.errors.ParserError as e:
        raise FileFormatError(f"文件解析失败: {e}")
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        raise DataAnalysisError(f"加载数据失败: {e}")
```

### 4. 日志配置

```python
import logging
from pathlib import Path

# 配置日志
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    配置应用日志。
    """
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# 使用日志
logger = logging.getLogger(__name__)

def analyze_data(df: pd.DataFrame) -> dict:
    logger.info(f"开始分析数据，形状: {df.shape}")
    
    try:
        # 分析逻辑
        result = perform_analysis(df)
        logger.info("数据分析完成")
        return result
    except Exception as e:
        logger.error(f"数据分析失败: {e}", exc_info=True)
        raise
```

### 5. 性能优化

```python
import time
from functools import wraps
from typing import Callable

# 性能监控装饰器
def monitor_performance(func: Callable) -> Callable:
    """
    监控函数执行性能。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行时间: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败 ({execution_time:.2f}秒): {e}")
            raise
    return wrapper

# 内存使用监控
import psutil
import os

def get_memory_usage() -> dict:
    """
    获取当前内存使用情况。
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "rss": memory_info.rss / 1024 / 1024,  # MB
        "vms": memory_info.vms / 1024 / 1024,  # MB
        "percent": process.memory_percent()
    }

# 数据处理优化
def process_large_dataset(file_path: str, chunk_size: int = 10000) -> dict:
    """
    分块处理大型数据集。
    """
    results = []
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # 处理每个数据块
        chunk_result = process_chunk(chunk)
        results.append(chunk_result)
        
        # 监控内存使用
        memory_usage = get_memory_usage()
        if memory_usage["percent"] > 80:
            logger.warning(f"内存使用率过高: {memory_usage['percent']:.1f}%")
    
    # 合并结果
    return combine_results(results)
```

## 常见问题解决

### 1. 依赖安装问题

```bash
# 清理缓存
uv cache clean
pip cache purge

# 重新安装
rm -rf .venv  # 或删除虚拟环境目录
uv sync --reinstall

# 使用国内镜像
uv pip install -i https://mirrors.aliyun.com/pypi/simple/ package_name
```

### 2. 端口占用问题

```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>

# 使用不同端口
uvicorn src.main:app --port 8001
```

### 3. 权限问题

```bash
# 创建必要的目录
mkdir -p data uploads temp logs

# 设置权限（Linux/macOS）
chmod 755 data uploads temp logs

# Windows 权限设置
icacls data /grant Users:F
```

### 4. 环境变量问题

```bash
# 检查环境变量
echo $PYTHONPATH  # Linux/macOS
echo %PYTHONPATH%  # Windows

# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%CD%\src  # Windows
```

## 开发工具推荐

### 1. 代码质量工具

- **Ruff**: 快速的Python代码检查和格式化
- **Black**: 代码格式化
- **MyPy**: 静态类型检查
- **Bandit**: 安全漏洞检查
- **Pre-commit**: Git提交前检查

### 2. 调试工具

- **pdb**: Python内置调试器
- **ipdb**: 增强的调试器
- **Jupyter**: 交互式开发
- **FastAPI自动文档**: http://localhost:8000/docs

### 3. 性能分析工具

- **cProfile**: 性能分析
- **memory_profiler**: 内存使用分析
- **py-spy**: 生产环境性能分析
- **Grafana**: 监控仪表板

### 4. 数据库工具

- **SQLite Browser**: SQLite数据库查看
- **DBeaver**: 通用数据库工具
- **pgAdmin**: PostgreSQL管理工具

## 下一步

- [贡献指南](contributing.md) - 了解如何为项目贡献代码
- [测试指南](testing.md) - 学习如何编写和运行测试
- [部署指南](../deployment/docker.md) - 了解如何部署应用
- [API文档](../api/overview.md) - 查看API接口文档