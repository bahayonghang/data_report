---
inclusion: always
---

# Product Requirements & Conventions

**data-report** is a Python web application for automated time-series data analysis with interactive reporting.

## Core Product Goals
- Provide zero-configuration data analysis for time-series datasets
- Enable browser-based exploration without requiring data science expertise
- Deliver immediate insights through automated statistical analysis
- Support both file upload and server-side file selection workflows

## Feature Requirements

### File Handling
- Support CSV and Parquet formats exclusively
- Auto-detect time columns (DateTime, tagTime, timestamp patterns)
- Validate file types and prevent path traversal attacks
- Enable both upload and server directory browsing

### Analysis Pipeline
- Automatic time-series detection and validation
- Statistical analysis: stationarity tests, trend analysis, correlation matrices
- Generate summary statistics and data quality metrics
- Handle missing data and outliers gracefully

### Visualization Standards
- Use Plotly for all interactive charts
- Generate time-series plots with zoom/pan capabilities
- Include correlation heatmaps and distribution plots
- Return charts as JSON for frontend rendering

### User Experience
- Single-page application with intuitive file selection
- Real-time analysis feedback and progress indicators
- No file downloads required - all results displayed in browser
- Responsive design for desktop and tablet use

## Development Priorities
1. **Security first**: All file operations must be sandboxed and validated
2. **Performance**: Use Polars for data processing, minimize memory usage
3. **Simplicity**: Minimize user configuration, maximize automation
4. **Reliability**: Graceful error handling with clear user feedback

## Success Metrics
- Users can analyze datasets in under 30 seconds from upload to insights
- Zero manual configuration required for standard time-series data
- All common time-series analysis patterns automated