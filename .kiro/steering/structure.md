---
inclusion: always
---

# Project Structure & Architecture

## Directory Structure
Follow this structure when creating new files and organizing code:

```
data-report/
├── main.py                 # FastAPI app entry point - keep minimal, delegate to src/
├── src/reporter/           # Core business logic package
│   ├── __init__.py
│   ├── data_loader.py      # File I/O, CSV/Parquet handling, path validation
│   ├── security.py         # Path traversal protection, file type validation
│   ├── analysis/           # Statistical analysis modules
│   │   ├── __init__.py
│   │   ├── time_series.py  # Stationarity tests, trend analysis
│   │   └── correlation.py  # Correlation matrices, statistical tests
│   └── visualization/      # Plotly chart generation
│       ├── __init__.py
│       └── charts.py       # Interactive time-series plots
├── static/                 # Frontend assets
│   ├── app.js             # Client-side logic
│   └── styles.css         # UI styling
└── templates/
    └── index.html         # Main web interface
```

## API Design Patterns

### Endpoint Structure
- **GET /**: Serve main web interface
- **GET /api/list-files**: List server files (with security filtering)
- **POST /api/analyze-server-file**: Analyze existing server file
- **POST /api/upload-and-analyze**: Handle file upload and analysis

### Request/Response Flow
1. Frontend sends file selection or upload
2. FastAPI validates and delegates to `src/reporter`
3. `data_loader.py` handles file operations with security checks
4. Analysis modules process data and generate statistics
5. Visualization modules create interactive charts
6. Return JSON response with charts and analysis results

## Code Organization Rules

### Module Responsibilities
- **main.py**: Route definitions only, delegate business logic to src/
- **data_loader.py**: All file operations, data validation, Polars DataFrame creation
- **security.py**: Path validation, prevent directory traversal, file type checks
- **analysis/**: Pure statistical functions, no file I/O
- **visualization/**: Chart generation functions, return Plotly JSON

### Import Patterns
- Use relative imports within `src/reporter` package
- Import external dependencies at module level
- Keep main.py imports minimal

## Naming Conventions
- **Python files/modules**: snake_case
- **Directories**: lowercase with underscores
- **API endpoints**: kebab-case with `/api/` prefix
- **Functions**: snake_case, descriptive verbs
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE

## Data Handling Standards
- **Time columns**: Auto-detect "DateTime", "tagTime", or similar patterns
- **File formats**: Support CSV and Parquet only
- **Data processing**: Use Polars for performance
- **Security**: Validate all file paths, restrict to designated directories