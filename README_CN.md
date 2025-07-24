# 数据分析报告系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

<div align="center">
  <img src="image/README/网页截图.png" width="600" alt="Web 界面截图">
</div>

一个基于 Web 的自动化数据分析和报告工具，专为时间序列数据设计。它提供了一个直观的 Web 界面，用于上传数据文件（CSV/Parquet），并自动生成包含统计分析和丰富的交互式可视化图表的综合报告。

## 🚀 主要特性

- **📊 多格式支持**: 原生支持 CSV 和 Parquet 文件格式。
- **🤖 自动分析**: 自动检测时间列并执行时间序列分析、描述性统计等。
- **📈 丰富的可视化**: 生成交互式时间序列图、相关性热力图、分布直方图和箱形图。
- **⚡ 高性能**: 基于 FastAPI 和 Polars 构建，可高效处理大型数据集。
- **🗄️ 分析历史**: 自动保存分析结果，并提供历史记录浏览器以重新访问过去的报告。
- **🔒 安全设计**: 内置文件类型、大小和路径验证检查。
- **🐳 容器化**: 可通过 Docker 和 Docker Compose 轻松部署。

## 🛠️ 技术栈

- **后端**: FastAPI, Python 3.11+
- **数据处理**: Polars, NumPy
- **统计分析**: Statsmodels
- **可视化引擎**: Plotly
- **前端**: 原生 HTML5, CSS3, JavaScript
- **数据库**: SQLite (通过 SQLAlchemy 和 aiosqlite)
- **部署**: Docker, Nginx
- **监控**: Prometheus

## 🚀 快速入门

### 方式一：Docker (推荐)

1.  **克隆仓库**
    ```bash
    git clone https://github.com/bahayonghang/data_report.git
    cd data_report
    ```
2.  **使用 Docker Compose 构建并运行**
    ```bash
    docker-compose up --build
    ```
3.  **访问应用**
    打开浏览器并访问 `http://localhost:8080`。

### 方式二：使用 `uv`

1.  **安装 `uv`** (如果尚未安装)
    ```bash
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **克隆仓库并安装依赖**
    ```bash
    git clone https://github.com/bahayonghang/data_report.git
    cd data_report
    uv sync
    ```
3.  **运行应用**
    ```bash
    uv run uvicorn main:app --reload
    ```
4.  **访问应用**
    打开浏览器并访问 `http://localhost:8000`。

## 📖 使用方法

1.  **访问 Web 界面**: 在浏览器中打开应用。
2.  **上传数据**: 拖放或选择一个 CSV 或 Parquet 文件进行分析。
3.  **查看报告**: 系统会自动处理文件并显示包含交互式图表和统计表格的完整报告。
4.  **浏览历史**: 访问历史页面以查看、搜索和重新打开过去的分析报告。

项目包含示例数据 (`data/sample_data.csv`)，您可以用它来测试系统的功能。

## 🔧 开发

### 设置开发环境

1.  **安装所有依赖，包括开发工具**
    ```bash
    uv sync --all-extras
    ```
2.  **运行测试**
    ```bash
    uv run pytest
    ```
3.  **代码格式化与检查**
    ```bash
    # 格式化代码
    uv run ruff format .
    # 检查 lint 错误
    uv run ruff check . --fix
    ```

### 项目结构

```
data_report/
├── src/reporter/            # 核心应用逻辑
│   ├── analysis/           # 统计分析模块
│   ├── visualization/      # 图表生成模块
│   ├── database.py         # 数据库管理
│   ├── data_loader.py      # 使用 Polars 加载数据
│   ├── file_manager.py     # 文件存储逻辑
│   └── security.py         # 安全与验证
├── templates/              # 前端 HTML 模板
├── static/                 # 前端 JS/CSS 资源
├── data/                   # 数据文件默认目录
├── tests/                  # 单元和端到端测试
├── docs/                   # 项目文档
├── main.py                 # FastAPI 应用入口点
├── pyproject.toml          # 项目配置和依赖
└── Dockerfile              # Docker 配置
```

## 📚 文档

如需更详细信息，您可以在本地构建并查看文档。

1.  **安装文档依赖**
    ```bash
    uv sync --extra docs
    ```
2.  **启动文档服务**
    ```bash
    uv run mkdocs serve
    ```
3.  打开浏览器并访问 `http://127.0.0.1:8000`。

关键文档包括：
- [架构概览](docs/architecture/overview.md)
- [API 端点](docs/api/endpoints.md)
- [开发设置](docs/development/setup.md)

## 🤝 贡献

欢迎贡献！请阅读 [贡献指南](docs/development/contributing.md) 以了解如何参与。

您可以通过以下方式做出贡献：
- 🐛 报告错误
- 💡 建议新功能
- 📝 改进文档
- 🔧 提交代码拉取请求

## 📄 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。
