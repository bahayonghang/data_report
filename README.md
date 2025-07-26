# Data Analysis Report System

[简体中文](README_CN.md)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

<div align="center">
  <img src="image/README/网页截图.png" width="600" alt="Web Interface Screenshot">
</div>

A web-based, automated data analysis and reporting tool designed for time-series data. It provides an intuitive web interface to upload data files (CSV/Parquet), and automatically generates a comprehensive report with statistical analysis and rich, interactive visualizations. [Suitable for smaller datasets (<100MB)]

## 🚀 Key Features

- **📊 Multi-Format Support**: Natively handles both CSV and Parquet file formats.
- **🤖 Automated Analysis**: Automatically detects time columns and performs time-series analysis, descriptive statistics, and more.
- **📈 Rich Visualizations**: Generates interactive time-series plots, correlation heatmaps, distribution histograms, and box plots.
- **⚡ High Performance**: Built with FastAPI and Polars for efficient processing of large datasets.
- **🗄️ Analysis History**: Automatically saves analysis results and provides a history browser to revisit past reports.
- **🔒 Secure by Design**: Includes built-in checks for file type, size, and path validation.
- **🐳 Containerized**: Ready for easy deployment with Docker and Docker Compose.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Data Processing**: Polars, NumPy
- **Statistical Analysis**: Statsmodels
- **Visualization Engine**: Plotly
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Database**: SQLite (via SQLAlchemy and aiosqlite)
- **Deployment**: Docker, Nginx
- **Monitoring**: Prometheus

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1.  **Clone the repository**
    ```bash
    git clone https://github.com/bahayonghang/data_report.git
    cd data_report
    ```
2.  **Build and run with Docker Compose**
    ```bash
    docker-compose up --build
    ```
3.  **Access the application**
    Open your browser and go to `http://localhost:8080`.

### Option 2: Using `uv`

1.  **Install `uv`** (if you haven't already)
    ```bash
    # macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
2.  **Clone the repository and install dependencies**
    ```bash
    git clone https://github.com/bahayonghang/data_report.git
    cd data_report
    uv sync
    ```
3.  **Run the application**
    ```bash
    uv run uvicorn main:app --reload
    ```
4.  **Access the application**
    Open your browser and go to `http://localhost:8000`.

## 📖 Usage

1.  **Navigate to the Web Interface**: Open the application in your browser.
2.  **Upload Data**: Drag and drop or select a CSV or Parquet file for analysis.
3.  **View Report**: The system automatically processes the file and displays a full report with interactive charts and statistical tables.
4.  **Browse History**: Navigate to the history page to view, search, and re-open past analysis reports.

The project includes sample data (`data/sample_data.csv`) that you can use to test the system's functionality.

## 🔧 Development

### Setting up the development environment

1.  **Install all dependencies, including dev tools**
    ```bash
    uv sync --all-extras
    ```
2.  **Run tests**
    ```bash
    uv run pytest
    ```
3.  **Lint and format code**
    ```bash
    # Format code
    uv run ruff format .
    # Check for linting errors
    uv run ruff check . --fix
    ```

### Project Structure

```
data_report/
├── src/reporter/            # Core application logic
│   ├── analysis/           # Statistical analysis modules
│   ├── visualization/      # Chart generation modules
│   ├── database.py         # Database management
│   ├── data_loader.py      # Data loading with Polars
│   ├── file_manager.py     # File storage logic
│   └── security.py         # Security and validation
├── templates/              # Frontend HTML templates
├── static/                 # Frontend JS/CSS assets
├── data/                   # Default directory for data files
├── tests/                  # Unit and E2E tests
├── docs/                   # Project documentation
├── main.py                 # FastAPI application entry point
├── pyproject.toml          # Project configuration and dependencies
└── Dockerfile              # Docker configuration
```

## 📚 Documentation

For more detailed information, you can build and serve the documentation locally.

1.  **Install documentation dependencies**
    ```bash
    uv sync --extra docs
    ```
2.  **Serve the documentation**
    ```bash
    uv run mkdocs serve
    ```
3.  Open your browser and go to `http://127.0.0.1:8000`.

Key documents include:
- [Architecture Overview](docs/architecture/overview.md)
- [API Endpoints](docs/api/endpoints.md)
- [Development Setup](docs/development/setup.md)

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](docs/development/contributing.md) to learn how you can get involved.

You can contribute by:
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 📝 Improving documentation
- 🔧 Submitting code pull requests

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.