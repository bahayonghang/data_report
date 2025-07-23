# FastAPI 应用入口点
# 提供完整的 Web API 和静态文件服务

import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import UploadFile, File, Form

from src.reporter.security import (
    validate_path,
    is_allowed_file_type,
    check_file_size,
    validate_file_operation,
)
from src.reporter.data_loader import load_data_file, prepare_analysis_data
from src.reporter.analysis.basic_stats import (
    calculate_descriptive_stats,
    analyze_missing_values,
    calculate_correlation_matrix,
)
from src.reporter.analysis.time_series import calculate_time_range, perform_adf_test
from src.reporter.visualization.charts import (
    create_time_series_plot,
    create_correlation_heatmap,
    create_distribution_plots,
    create_box_plots,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Data Analysis Report Tool",
    description="Web-based automated data analysis and reporting tool for time-series data",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 配置模板引擎
templates = Jinja2Templates(directory="templates")

# 配置静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 环境配置
DATA_DIRECTORY = os.getenv("DATA_DIRECTORY", "./data")
Path(DATA_DIRECTORY).mkdir(parents=True, exist_ok=True)


# 异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 HTTP 异常"""
    # 如果detail已经是字典格式，直接使用
    if isinstance(exc.detail, dict):
        error_response = {"success": False, "error": exc.detail}
    else:
        error_response = {
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
            },
        }

    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=exc.status_code, content=error_response)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证异常"""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据验证失败",
                "details": str(exc),
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": None,
            },
        },
    )


# 主页路由
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """主页面 - 返回数据分析工具界面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """分析结果页面"""
    return templates.TemplateResponse("analysis.html", {"request": request})


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "data_directory": DATA_DIRECTORY,
        "data_directory_exists": Path(DATA_DIRECTORY).exists(),
    }


# 文件管理 API 端点
@app.get("/api/list-files")
async def list_server_files():
    """
    列出服务器数据目录中的可用文件

    Returns:
        Dict: 包含文件列表的响应
    """
    try:
        data_dir = Path(DATA_DIRECTORY)

        # 检查数据目录是否存在
        if not data_dir.exists():
            logger.warning(f"Data directory does not exist: {DATA_DIRECTORY}")
            return {"success": True, "files": []}

        files_info = []

        # 遍历目录中的文件
        for file_path in data_dir.iterdir():
            if file_path.is_file():
                # 检查文件类型是否被允许
                if not is_allowed_file_type(file_path.name):
                    continue

                # 验证文件路径安全性
                if not validate_path(file_path.name, DATA_DIRECTORY):
                    continue

                # 检查文件大小
                if not check_file_size(str(file_path)):
                    continue

                try:
                    # 获取文件统计信息
                    stat_info = file_path.stat()

                    file_info = {
                        "name": file_path.name,
                        "size": stat_info.st_size,
                        "modified": datetime.fromtimestamp(
                            stat_info.st_mtime
                        ).isoformat()
                        + "Z",
                    }

                    files_info.append(file_info)

                except (OSError, ValueError) as e:
                    logger.warning(
                        f"Error reading file info for {file_path.name}: {str(e)}"
                    )
                    continue

        # 按修改时间排序（最新的在前）
        files_info.sort(key=lambda x: x["modified"], reverse=True)

        logger.info(f"Listed {len(files_info)} files from {DATA_DIRECTORY}")

        return {"success": True, "files": files_info}

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FILE_LIST_ERROR",
                "message": "获取文件列表失败",
                "details": None,
            },
        )


def analyze_data_file(file_path: str, filename: str) -> Dict[str, Any]:
    """
    分析数据文件的核心函数

    Args:
        file_path: 文件完整路径
        filename: 文件名

    Returns:
        Dict[str, Any]: 分析结果
    """
    try:
        # 加载数据
        df = load_data_file(file_path)

        # 准备分析数据
        data_info = prepare_analysis_data(df)

        # 获取基本信息
        time_column = data_info.get("time_column")
        numeric_columns = data_info.get("numeric_columns", [])
        processed_df = data_info.get("processed_df")

        # 计算描述性统计
        descriptive_stats = calculate_descriptive_stats(processed_df, numeric_columns)

        # 分析缺失值
        missing_values = analyze_missing_values(processed_df)

        # 计算相关性矩阵
        correlation_matrix = calculate_correlation_matrix(processed_df, numeric_columns)

        # 时间序列分析
        time_info = {}
        stationarity_tests = {}

        if time_column:
            time_series = processed_df[time_column]
            time_info = calculate_time_range(time_series)

            # 对每个数值列进行ADF检验
            for col in numeric_columns:
                stationarity_tests[col] = perform_adf_test(processed_df[col])

        # 生成可视化图表
        visualizations = {}

        # 时序图表
        if time_column and numeric_columns:
            try:
                visualizations["time_series"] = create_time_series_plot(
                    processed_df, time_column, numeric_columns
                )
            except Exception as viz_error:
                logger.warning(f"Failed to create time series plot: {viz_error}")
                visualizations["time_series"] = {"error": "时序图表生成失败"}

        # 相关性热力图
        if len(numeric_columns) > 1 and correlation_matrix.get("matrix"):
            # 为热力图准备相关系数矩阵
            import polars as pl

            corr_data = []
            matrix_data = correlation_matrix["matrix"]

            for col1 in numeric_columns:
                row = {"variable": col1}
                for col2 in numeric_columns:
                    row[col2] = matrix_data.get(col1, {}).get(col2, 0.0)
                corr_data.append(row)

            try:
                corr_df = pl.DataFrame(corr_data)
                visualizations["correlation_heatmap"] = create_correlation_heatmap(
                    corr_df
                )
            except Exception as viz_error:
                logger.warning(f"Failed to create correlation heatmap: {viz_error}")
                visualizations["correlation_heatmap"] = {
                    "error": "相关性热力图生成失败"
                }

        # 分布直方图
        if numeric_columns:
            try:
                visualizations["distributions"] = create_distribution_plots(
                    processed_df, numeric_columns
                )
            except Exception as viz_error:
                logger.warning(f"Failed to create distribution plots: {viz_error}")
                visualizations["distributions"] = {"error": "分布直方图生成失败"}

        # 箱形图
        if numeric_columns:
            try:
                visualizations["box_plots"] = create_box_plots(
                    processed_df, numeric_columns
                )
            except Exception as viz_error:
                logger.warning(f"Failed to create box plots: {viz_error}")
                visualizations["box_plots"] = {"error": "箱形图生成失败"}

        # 构建完整响应
        result = {
            "success": True,
            "data": {
                "file_info": {
                    "name": filename,
                    "rows": data_info.get("total_rows", 0),
                    "columns": data_info.get("total_columns", 0),
                },
                "time_info": {"time_column": time_column, "time_range": time_info},
                "statistics": descriptive_stats,
                "missing_values": missing_values,
                "correlation_matrix": correlation_matrix,
                "stationarity_tests": stationarity_tests,
                "visualizations": visualizations,
            },
        }

        logger.info(f"Successfully analyzed file: {filename}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing file {filename}: {str(e)}", exc_info=True)
        raise


# 数据分析 API 端点
@app.post("/api/analyze-server-file")
async def analyze_server_file(filename: str = Form(...)):
    """
    分析服务器上的文件

    Args:
        filename: 服务器文件名

    Returns:
        Dict: 分析结果
    """
    try:
        # 验证文件操作安全性
        is_safe, error_msg = validate_file_operation(filename, DATA_DIRECTORY)
        if not is_safe:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_FILE", "message": error_msg, "details": None},
            )

        # 构建完整文件路径
        file_path = Path(DATA_DIRECTORY) / filename

        # 检查文件是否存在
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "FILE_NOT_FOUND",
                    "message": f"文件不存在: {filename}",
                    "details": None,
                },
            )

        # 执行分析
        result = analyze_data_file(str(file_path), filename)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_server_file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_ERROR",
                "message": "文件分析失败",
                "details": None,
            },
        )


@app.post("/api/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    上传并分析文件

    Args:
        file: 上传的文件

    Returns:
        Dict: 分析结果
    """
    import tempfile

    try:
        # 验证文件类型
        if not is_allowed_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": "不支持的文件类型，仅支持 CSV 和 Parquet 文件",
                    "details": f"上传的文件: {file.filename}",
                },
            )

        # 检查文件大小
        content = await file.read()
        file_size = len(content)

        MAX_UPLOAD_SIZE = 1024 * 1024 * 1024  # 1GB
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"文件过大，最大支持 {MAX_UPLOAD_SIZE // 1024 // 1024}MB",
                    "details": f"上传文件大小: {file_size // 1024 // 1024}MB",
                },
            )

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # 执行分析
            result = analyze_data_file(temp_file_path, file.filename)
            return result

        finally:
            # 清理临时文件
            try:
                Path(temp_file_path).unlink()
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_and_analyze: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "UPLOAD_ANALYSIS_ERROR",
                "message": "文件上传和分析失败",
                "details": None,
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
