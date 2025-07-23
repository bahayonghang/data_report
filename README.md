# 数据分析报告系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

<div align="center">
  <img src="image/README/网页截图.png" width="600" alt="网页截图">
</div>
一个基于Web的自动化数据分析和报告工具，专门为时间序列数据设计。提供直观的Web界面，支持多种数据格式，自动生成统计分析报告和可视化图表。

## 🚀 主要特性

- **📊 多格式支持**: 支持CSV和Parquet文件格式
- **🤖 智能分析**: 自动检测时间列，进行时间序列分析
- **📈 丰富可视化**: 提供时序图、相关性热力图、分布图等多种图表
- **🔒 安全可靠**: 内置文件安全检查和路径验证
- **💻 易于使用**: 直观的Web界面，支持文件上传和服务器文件选择
- **⚡ 高性能**: 基于Polars和FastAPI构建，处理大数据集高效
- **🐳 容器化**: 支持Docker部署，开箱即用

## 📊 分析功能

### 统计分析

- 描述性统计（均值、中位数、标准差等）
- 缺失值分析和处理建议
- 相关系数矩阵计算
- 时间序列平稳性检验（ADF检验）

### 可视化图表

- 时序曲线图（支持多变量）
- 相关性热力图
- 数据分布直方图
- 箱形图异常值检测
- 交互式图表（缩放、平移、悬停提示）

## 🛠️ 技术栈

- **后端框架**: FastAPI + Python 3.11+
- **数据处理**: Polars + NumPy
- **统计分析**: Statsmodels
- **可视化引擎**: Plotly
- **前端技术**: HTML5 + CSS3 + JavaScript
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **监控工具**: Prometheus

## 🚀 快速开始

### 方式一：使用 uv（推荐）

1. **安装 uv**

   ```bash
   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **克隆项目**

   ```bash
   git clone https://github.com/your-username/data_report.git
   cd data_report
   ```
3. **安装依赖**

   ```bash
   uv sync
   ```
4. **启动服务**

   ```bash
   uv run uvicorn main:app --reload
   ```
5. **访问应用**
   打开浏览器访问 `http://localhost:8000`

### 方式二：使用 Docker

1. **克隆项目**

   ```bash
   git clone https://github.com/your-username/data_report.git
   cd data_report
   ```
2. **构建并启动**

   ```bash
   docker-compose up --build
   ```
3. **访问应用**
   打开浏览器访问 `http://localhost:8080`

### 方式三：传统 pip 安装

1. **创建虚拟环境**

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```
2. **安装依赖**

   ```bash
   pip install -e .
   ```
3. **启动服务**

   ```bash
   uvicorn main:app --reload
   ```

## 📖 使用指南

### 基本使用流程

1. **上传数据文件**

   - 支持CSV和Parquet格式
   - 文件大小限制：1GB
   - 自动检测时间列
2. **选择分析类型**

   - 基础统计分析
   - 时间序列分析
   - 相关性分析
3. **配置分析参数**

   - 选择目标列
   - 设置时间范围
   - 调整图表样式
4. **查看分析结果**

   - 统计摘要表格
   - 交互式图表
   - 分析结论和建议
5. **导出报告**

   - HTML格式报告
   - 图表PNG/SVG导出
   - 数据CSV导出

### 示例数据

项目包含示例数据文件 `data/sample_data.csv`，您可以直接使用它来体验系统功能。

## 🔧 开发指南

### 开发环境搭建

1. **安装开发依赖**

   ```bash
   uv sync --group dev
   ```
2. **运行测试**

   ```bash
   uv run pytest
   ```
3. **代码格式化**

   ```bash
   uv run ruff format .
   uv run ruff check .
   ```
4. **启动文档服务**

   ```bash
   uv sync --group docs
   uv run mkdocs serve
   ```

### 项目结构

```
data_report/
├── src/reporter/          # 核心业务逻辑
│   ├── analysis/         # 分析模块
│   ├── visualization/    # 可视化模块
│   ├── data_loader.py    # 数据加载
│   └── security.py       # 安全验证
├── templates/            # HTML模板
├── static/              # 静态资源
├── data/                # 数据目录
├── tests/               # 测试文件
├── docs/                # 文档
├── main.py              # 应用入口
└── pyproject.toml       # 项目配置
```

## 📚 文档

完整的文档可以通过以下方式访问：

- **在线文档**: [项目文档站点](https://your-username.github.io/data_report/)
- **本地文档**: 运行 `uv run mkdocs serve` 后访问 `http://localhost:8000`

主要文档包括：

- [安装指南](docs/getting-started/installation.md)
- [API文档](docs/api/overview.md)
- [开发指南](docs/development/environment.md)
- [部署指南](docs/deployment/deployment.md)

## 🤝 贡献

我们欢迎任何形式的贡献！请查看[贡献指南](docs/development/contributing.md)了解如何参与项目开发。

### 贡献方式

- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- ⭐ 给项目点星支持

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 📞 支持与反馈

如果您遇到问题或有任何建议，请：

- 📋 提交 [GitHub Issue](https://github.com/your-username/data_report/issues)
- 📖 查看[故障排除指南](docs/deployment/troubleshooting.md)
- 💬 参与 [Discussions](https://github.com/your-username/data_report/discussions)

## 🌟 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**开始您的数据分析之旅吧！** 🚀
