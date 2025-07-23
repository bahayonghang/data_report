---
inclusion: always
---

# Technology Stack & Development Guidelines

## Required Technologies
- **Python**: 3.11+ (check `.python-version`)
- **Package Manager**: `uv` - ALWAYS use `uv` commands, never `pip` directly
- **Web Framework**: FastAPI - use for all API endpoints
- **Data Processing**: Polars - REQUIRED for all DataFrame operations, never pandas
- **Visualization**: Plotly - return charts as JSON, not HTML
- **Server**: uvicorn for development

## Development Commands

### Environment & Dependencies
```bash
# Setup (Windows)
uv venv
.venv\Scripts\activate
uv pip install -e .

# Run application
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality (when tools are configured)
```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

## Critical Security Rules
- **File Operations**: ALL file paths MUST be validated against path traversal
- **File Types**: Accept ONLY CSV and Parquet files
- **Data Directory**: Use environment variable `DATA_DIRECTORY` for file storage
- **Path Validation**: Implement in `src/reporter/security.py`

## Performance Requirements
- Use Polars for ALL data operations (never pandas)
- Minimize memory usage for large datasets
- Return Plotly charts as JSON objects, not rendered HTML
- Use async/await patterns in FastAPI endpoints

## Import Conventions
```python
# External dependencies
import polars as pl
from fastapi import FastAPI, HTTPException
import plotly.graph_objects as go

# Internal modules (use relative imports within src/reporter)
from .data_loader import load_file
from .security import validate_path
```

## Error Handling Standards
- Use FastAPI's HTTPException for API errors
- Provide clear error messages for file validation failures
- Log security violations but don't expose details to users
- Handle missing data gracefully in analysis functions