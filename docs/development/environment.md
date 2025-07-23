# 开发环境配置

本文档详细说明如何配置数据分析报告系统的开发环境，包括IDE设置、调试配置和开发工具链。

## IDE配置

### Visual Studio Code

#### 推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "ms-python.isort",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-playwright.playwright",
    "ms-vscode.test-adapter-converter",
    "ms-vscode.extension-test-runner",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag",
    "esbenp.prettier-vscode"
  ]
}
```

#### 工作区设置

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
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
    "source.organizeImports": true,
    "source.fixAll.ruff": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  }
}
```

#### 调试配置

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "ENVIRONMENT": "development",
        "DEBUG": "true"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${workspaceFolder}/tests",
        "-v"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: Pytest Current File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v",
        "-s"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### PyCharm配置

#### 项目设置

1. **Python解释器**
   - 路径: `<project_root>/.venv/bin/python`
   - 类型: Virtual Environment

2. **代码风格**
   - Python: 使用Black格式化器
   - 行长度: 88字符
   - 导入排序: 使用isort

3. **运行配置**
   ```
   名称: FastAPI Development Server
   脚本路径: main.py
   工作目录: <project_root>
   环境变量:
     ENVIRONMENT=development
     DEBUG=true
   ```

## 环境变量配置

### 开发环境配置文件

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# 服务器配置
HOST=127.0.0.1
PORT=8000
RELOAD=true

# 数据目录
DATA_DIR=./data
UPLOAD_DIR=./uploads
TEMP_DIR=./temp

# 文件限制
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=csv,parquet

# 安全配置
SECRET_KEY=dev-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 数据库配置（开发用）
DATABASE_URL=sqlite:///./dev.db

# 缓存配置
CACHE_ENABLED=false
CACHE_TTL=300

# 监控配置
PROMETHEUS_ENABLED=false
METRICS_PORT=9090

# 日志配置
LOG_FILE=./logs/dev.log
LOG_FORMAT=detailed
LOG_ROTATION=false
```

### 环境变量管理

```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # 基础配置
    environment: str = "development"
    debug: bool = False
    log_level: str = "info"
    
    # 服务器配置
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    
    # 目录配置
    data_dir: str = "./data"
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"
    
    # 文件配置
    max_file_size: str = "50MB"
    allowed_extensions: List[str] = ["csv", "parquet"]
    
    # 安全配置
    secret_key: str
    allowed_hosts: List[str] = ["localhost"]
    cors_origins: List[str] = []
    
    # 数据库配置
    database_url: Optional[str] = None
    
    # 缓存配置
    cache_enabled: bool = False
    cache_ttl: int = 300
    
    # 监控配置
    prometheus_enabled: bool = False
    metrics_port: int = 9090
    
    # 日志配置
    log_file: Optional[str] = None
    log_format: str = "simple"
    log_rotation: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 全局设置实例
settings = Settings()
```

## 开发工具配置

### Pre-commit钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

安装pre-commit:

```bash
# 安装pre-commit
uv add --dev pre-commit

# 安装钩子
uv run pre-commit install

# 运行所有文件检查
uv run pre-commit run --all-files
```

### Ruff配置

```toml
# pyproject.toml中的ruff配置
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by black
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*" = ["B011", "B018"]

[tool.ruff.isort]
known-first-party = ["src"]
```

### Black配置

```toml
# pyproject.toml中的black配置
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
(
  /(
      \.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''
```

### Pytest配置

```toml
# pyproject.toml中的pytest配置
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = [
    "tests",
]
python_files = [
    "test_*.py",
    "*_test.py",
]
python_classes = [
    "Test*",
]
python_functions = [
    "test_*",
]
markers = [
    "slow: marks tests as slow (deselect with '-m "not slow"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "e2e: marks tests as end-to-end tests",
]
filterwarnings = [
    "error",
    "ignore::UserWarning",
    "ignore::DeprecationWarning",
]
```

## 调试配置

### 日志配置

```python
# src/logging_config.py
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any

def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """配置日志系统"""
    
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # 添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": str(log_path),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        
        config["root"]["handlers"].append("file")
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
    
    logging.config.dictConfig(config)
```

### 性能分析

```python
# src/profiling.py
import cProfile
import pstats
import io
from functools import wraps
from typing import Callable, Any

def profile_function(func: Callable) -> Callable:
    """函数性能分析装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        print(f"\n=== Profile for {func.__name__} ===")
        print(s.getvalue())
        
        return result
    return wrapper

# 使用示例
@profile_function
def analyze_data(df):
    # 数据分析逻辑
    pass
```

### 内存监控

```python
# src/memory_monitor.py
import psutil
import tracemalloc
from functools import wraps
from typing import Callable, Any

def monitor_memory(func: Callable) -> Callable:
    """内存使用监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # 开始内存跟踪
        tracemalloc.start()
        process = psutil.Process()
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 获取内存快照
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n=== Memory Usage for {func.__name__} ===")
        print(f"Initial RSS: {initial_memory:.2f} MB")
        print(f"Final RSS: {final_memory:.2f} MB")
        print(f"Memory change: {final_memory - initial_memory:.2f} MB")
        print(f"Peak traced memory: {peak / 1024 / 1024:.2f} MB")
        
        return result
    return wrapper
```

## 开发工作流

### 日常开发流程

```bash
# 1. 更新代码
git pull origin main

# 2. 安装/更新依赖
uv sync

# 3. 运行代码质量检查
uv run ruff check .
uv run black --check .
uv run mypy src/

# 4. 运行测试
uv run pytest

# 5. 启动开发服务器
uv run python main.py

# 6. 进行开发工作
# ...

# 7. 提交前检查
uv run pre-commit run --all-files

# 8. 提交代码
git add .
git commit -m "feat: add new feature"
git push origin feature-branch
```

### 测试驱动开发

```python
# 示例：TDD开发新功能

# 1. 先写测试
def test_new_analysis_feature():
    """测试新的分析功能"""
    data = create_test_data()
    result = new_analysis_function(data)
    
    assert result is not None
    assert "correlation" in result
    assert len(result["correlation"]) > 0

# 2. 运行测试（应该失败）
# uv run pytest tests/test_new_feature.py::test_new_analysis_feature

# 3. 实现功能
def new_analysis_function(data):
    """新的分析功能"""
    # 实现逻辑
    correlation = data.corr()
    return {"correlation": correlation.to_dict()}

# 4. 再次运行测试（应该通过）
# uv run pytest tests/test_new_feature.py::test_new_analysis_feature

# 5. 重构和优化
# ...
```

### 性能测试

```python
# tests/performance/test_performance.py
import time
import pytest
from src.data_loader import DataLoader
from src.analysis.stats import StatisticalAnalyzer

class TestPerformance:
    """性能测试"""
    
    @pytest.mark.slow
    def test_large_file_loading_performance(self):
        """测试大文件加载性能"""
        start_time = time.time()
        
        loader = DataLoader()
        df = loader.load_csv("tests/data/large_dataset.csv")
        
        load_time = time.time() - start_time
        
        assert load_time < 10.0  # 应在10秒内完成
        assert len(df) > 100000  # 确保数据量足够大
    
    @pytest.mark.slow
    def test_analysis_performance(self):
        """测试分析性能"""
        # 创建大数据集
        import polars as pl
        import numpy as np
        
        data = pl.DataFrame({
            "col1": np.random.randn(100000),
            "col2": np.random.randn(100000),
            "col3": np.random.randn(100000),
        })
        
        start_time = time.time()
        
        analyzer = StatisticalAnalyzer()
        result = analyzer.analyze(data)
        
        analysis_time = time.time() - start_time
        
        assert analysis_time < 5.0  # 应在5秒内完成
        assert "basic_stats" in result
```

## 故障排除

### 常见开发问题

#### 1. 虚拟环境问题

```bash
# 问题：找不到Python解释器
# 解决：重新创建虚拟环境
rm -rf .venv
uv sync

# 问题：包版本冲突
# 解决：清理并重新安装
uv clean
uv sync --refresh
```

#### 2. 导入错误

```python
# 问题：ModuleNotFoundError
# 解决：检查PYTHONPATH
import sys
print(sys.path)

# 或者在项目根目录运行
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 3. 测试失败

```bash
# 详细输出
uv run pytest -v -s

# 只运行失败的测试
uv run pytest --lf

# 调试模式
uv run pytest --pdb
```

### 开发环境重置

```bash
#!/bin/bash
# reset-dev-env.sh

echo "重置开发环境..."

# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 清理测试缓存
rm -rf .pytest_cache
rm -f .coverage
rm -rf htmlcov

# 重新创建虚拟环境
rm -rf .venv
uv sync

# 重新安装pre-commit钩子
uv run pre-commit install

# 运行测试确保环境正常
uv run pytest tests/ -x

echo "开发环境重置完成！"
```

通过遵循这个开发环境配置指南，您可以建立一个高效、一致的开发环境，提高开发效率和代码质量。