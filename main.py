# FastAPI 应用入口点
# 提供完整的 Web API 和静态文件服务

import os
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Query
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
    create_charts_batch,
    create_charts_parallel
)
from src.reporter.analysis.parallel_processor import ParallelProcessor, optimize_dataframe_processing
from src.reporter.utils.performance import PerformanceMonitor, ResourceManager, monitor_performance, optimize_polars_settings
import asyncio
from src.reporter.database import DatabaseManager, calculate_file_hash
from src.reporter.file_manager import file_storage_manager

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

# 数据库管理器实例
db_manager = DatabaseManager()


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    try:
        await db_manager.init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


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


# 文件管理 API 端点已删除 - 所有分析都通过文件上传进行


# 服务器文件列表API已删除 - 所有分析都通过文件上传进行


@monitor_performance
def analyze_data_file(file_path: str, filename: str) -> Dict[str, Any]:
    """
    分析数据文件的核心函数

    Args:
        file_path: 文件完整路径
        filename: 文件名

    Returns:
        Dict[str, Any]: 分析结果
    """
    import time
    start_time = time.time()
    
    # 初始化性能监控和资源管理
    performance_monitor = PerformanceMonitor()
    resource_manager = ResourceManager(memory_limit_mb=2048)  # 2GB内存限制
    
    # 优化Polars设置
    optimize_polars_settings()
    
    try:
        logger.info(f"开始分析文件: {filename}")
        
        # 阶段1: 加载数据 (10%)
        logger.info("阶段1: 加载数据...")
        df = load_data_file(file_path)
        # 优化数据框处理
        df = optimize_dataframe_processing(df)
        logger.info(f"数据加载完成，共{df.height}行，{df.width}列")
        
        # 检查内存使用情况
        if not resource_manager.check_resource_availability():
            logger.warning("内存使用接近限制，启用内存优化")
            resource_manager.optimize_memory_usage()

        # 阶段2: 准备分析数据 (20%)
        logger.info("阶段2: 准备分析数据...")
        data_info = prepare_analysis_data(df)
        
        # 获取基本信息
        time_column = data_info.get("time_column")
        numeric_columns = data_info.get("numeric_columns", [])
        processed_df = data_info.get("processed_df")
        warnings = data_info.get("warnings", [])
        
        # 验证处理后的数据
        if processed_df is None:
            raise ValueError("数据预处理失败，无法获取处理后的数据")
        
        if warnings:
            for warning in warnings:
                logger.warning(f"数据预处理警告: {warning}")
        
        logger.info(f"数据预处理完成，时间列: {time_column}, 数值列: {len(numeric_columns)}个")

        # 阶段3: 计算描述性统计 (30%)
        logger.info("阶段3: 计算描述性统计...")
        descriptive_stats = calculate_descriptive_stats(processed_df, numeric_columns)
        logger.info("描述性统计计算完成")

        # 阶段4: 分析缺失值 (40%)
        logger.info("阶段4: 分析缺失值...")
        missing_values = analyze_missing_values(processed_df)
        logger.info("缺失值分析完成")

        # 阶段5: 计算相关性矩阵 (50%)
        logger.info("阶段5: 计算相关性矩阵...")
        correlation_matrix = calculate_correlation_matrix(processed_df, numeric_columns)
        if correlation_matrix.get("warnings"):
            for warning in correlation_matrix["warnings"]:
                logger.warning(f"相关性分析警告: {warning}")
        logger.info("相关性矩阵计算完成")

        # 阶段6: 时间序列分析 (60%) - 优化版本
        logger.info("阶段6: 时间序列分析（优化版本）...")
        time_info = {}
        stationarity_tests = {}
        time_series_performance = {}

        if time_column:
            try:
                # 使用优化的时间序列分析
                from src.reporter.analysis.time_series import analyze_time_series_optimized
                
                logger.info(f"开始优化时间序列分析，数据量: {len(processed_df)} 行")
                
                # 执行优化的时间序列分析
                time_series_result = analyze_time_series_optimized(
                    df=processed_df,
                    time_column=time_column,
                    numeric_columns=numeric_columns,
                    performance_threshold=10000  # 超过1万行启用采样
                )
                
                # 提取结果
                time_info = time_series_result.get("time_analysis", {})
                stationarity_tests = time_series_result.get("adf_tests", {})
                time_series_performance = time_series_result.get("performance_metrics", {})
                
                # 记录性能信息
                sampling_info = time_series_result.get("sampling_info", {})
                if sampling_info.get("sampling_method") != "none":
                    logger.info(
                        f"时间序列分析采用采样优化: {sampling_info['original_size']} -> "
                        f"{sampling_info['sampled_size']} 行 "
                        f"(方法: {sampling_info['sampling_method']}, "
                        f"性能提升: {sampling_info.get('performance_gain', 1):.1f}x)"
                    )
                
                logger.info(
                    f"时间序列分析完成: 处理了 {time_series_performance.get('processed_rows', 0)} 行数据, "
                    f"分析了 {time_series_performance.get('columns_analyzed', 0)} 个列, "
                    f"执行了 {time_series_performance.get('adf_tests_performed', 0)} 个ADF检验"
                )
                
            except Exception as e:
                logger.warning(f"优化时间序列分析失败，降级到基础分析: {e}")
                # 降级到原始方法（但限制处理量）
                try:
                    time_series = processed_df[time_column]
                    time_info = calculate_time_range(time_series)
                    
                    # 限制ADF检验的列数以提高性能
                    max_adf_columns = min(len(numeric_columns), 3)
                    logger.info(f"降级模式：仅对前{max_adf_columns}个数值列进行ADF检验")
                    
                    for i, col in enumerate(numeric_columns[:max_adf_columns]):
                        try:
                            stationarity_tests[col] = perform_adf_test(processed_df[col])
                        except Exception as adf_error:
                            logger.warning(f"ADF检验失败 {col}: {adf_error}")
                            stationarity_tests[col] = {"error": str(adf_error)}
                    
                    logger.info(f"降级时间序列分析完成，检验了{len(stationarity_tests)}个数值列")
                except Exception as fallback_error:
                    logger.error(f"降级时间序列分析也失败: {fallback_error}")
        else:
            logger.info("未检测到时间列，跳过时间序列分析")

        # 阶段7: 生成可视化图表 (70%-100%)
        logger.info("阶段7: 生成可视化图表...")
        visualizations = {}
        
        # 尝试使用并行处理生成图表
        try:
            # 检查是否有足够的资源进行并行处理
            if resource_manager.check_resource_availability():
                logger.info("使用批量处理生成图表")
                charts_result = create_charts_batch(
                    df=processed_df,
                    time_col=time_column,
                    numeric_cols=numeric_columns,
                    correlation_matrix=correlation_matrix
                )
            else:
                logger.warning("资源不足，使用串行处理生成图表")
                # 降级到串行处理
                charts_result = {
                    'time_series_plot': None,
                    'distribution_plots': {},
                    'box_plots': {},
                    'correlation_heatmap': None
                }
            
            # 提取结果（修复键名映射）
            visualizations["time_series"] = charts_result.get('time_series', {"error": "时序图表生成失败"})
            visualizations["distributions"] = charts_result.get('distribution', {"error": "分布直方图生成失败"})
            visualizations["box_plots"] = charts_result.get('box_plots', {"error": "箱形图生成失败"})
            visualizations["correlation_heatmap"] = charts_result.get('correlation', {"error": "相关性热力图生成失败"})
            
            logger.info("所有图表生成完成")
            
        except Exception as e:
            logger.error(f"图表生成过程出错: {e}")
            # 降级到串行处理
            logger.info("降级到串行处理生成图表")
            
            # 时序图表 (75%)
            if time_column and numeric_columns:
                try:
                    logger.info("生成时序图表...")
                    visualizations["time_series"] = create_time_series_plot(
                        processed_df, time_column, numeric_columns
                    )
                    logger.info("时序图表生成成功")
                except Exception as viz_error:
                    logger.warning(f"时序图表生成失败: {viz_error}")
                    visualizations["time_series"] = {"error": "时序图表生成失败"}

            # 相关性热力图 (80%)
            if len(numeric_columns) > 1 and correlation_matrix.get("matrix"):
                try:
                    logger.info("生成相关性热力图...")
                    # 为热力图准备相关系数矩阵
                    import polars as pl

                    corr_data = []
                    matrix_data = correlation_matrix["matrix"]

                    for col1 in numeric_columns:
                        row = {"variable": col1}
                        for col2 in numeric_columns:
                            row[col2] = matrix_data.get(col1, {}).get(col2, 0.0)
                        corr_data.append(row)

                    corr_df = pl.DataFrame(corr_data)
                    visualizations["correlation_heatmap"] = create_correlation_heatmap(
                        corr_df
                    )
                    logger.info("相关性热力图生成成功")
                except Exception as viz_error:
                    logger.warning(f"相关性热力图生成失败: {viz_error}")
                    visualizations["correlation_heatmap"] = {
                        "error": "相关性热力图生成失败"
                    }

            # 分布直方图 (90%)
            if numeric_columns:
                try:
                    logger.info("生成分布直方图...")
                    visualizations["distributions"] = create_distribution_plots(
                        processed_df, numeric_columns
                    )
                    logger.info(f"分布直方图生成成功，共{len(visualizations['distributions'])}个图表")
                except Exception as viz_error:
                    logger.warning(f"分布直方图生成失败: {viz_error}")
                    visualizations["distributions"] = {"error": "分布直方图生成失败"}

            # 箱形图 (95%)
            if numeric_columns:
                try:
                    logger.info("生成箱形图...")
                    visualizations["box_plots"] = create_box_plots(
                        processed_df, numeric_columns
                    )
                    logger.info(f"箱形图生成成功，共{len(visualizations['box_plots'])}个图表")
                except Exception as viz_error:
                    logger.warning(f"箱形图生成失败: {viz_error}")
                    visualizations["box_plots"] = {"error": "箱形图生成失败"}
        
        logger.info("所有可视化图表生成完成")
        
        # 获取性能监控摘要
        performance_summary = performance_monitor.get_performance_summary()
        logger.info(f"性能监控摘要: {performance_summary}")
        
        # 最终内存优化
        resource_manager.optimize_memory_usage()
        
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
                "performance_info": {
                    "total_execution_time": f"{time.time() - start_time:.2f}秒",
                    "memory_usage": f"{performance_monitor.get_memory_usage():.2f}MB",
                    "operations_count": performance_summary.get("总操作数", 0),
                    "time_series_optimization": time_series_performance
                }
            },
        }

        logger.info(f"Successfully analyzed file: {filename} in {time.time() - start_time:.2f}s")
        return result

    except Exception as e:
        logger.error(f"Error analyzing file {filename}: {str(e)}", exc_info=True)
        raise


# 服务器文件分析API已删除 - 所有分析都通过文件上传进行


@app.post("/api/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    上传并分析文件（支持历史记录）

    Args:
        file: 上传的文件

    Returns:
        Dict: 分析结果
    """
    try:
        # 验证文件类型
        if not file.filename or not is_allowed_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": "不支持的文件类型，仅支持 CSV 和 Parquet 文件",
                    "details": f"上传的文件: {file.filename}",
                },
            )

        # 读取文件内容
        content = await file.read()
        file_size = len(content)

        # 检查文件大小
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

        # 计算文件哈希
        file_hash = calculate_file_hash(content)
        file_extension = Path(file.filename).suffix
        
        # 检查是否已存在相同文件
        existing_file = await db_manager.get_file_by_hash(file_hash)
        
        if existing_file and existing_file.id is not None:
            # 文件已存在，获取最新的分析结果
            logger.info(f"文件已存在，使用历史记录: {file.filename} (hash: {file_hash})")
            
            latest_analysis = await db_manager.get_latest_analysis_by_file_id(existing_file.id)
            if latest_analysis and latest_analysis.id is not None:
                # 加载历史分析结果
                analysis_result = await file_storage_manager.load_analysis_result(
                    latest_analysis.result_file_path
                )
                
                if analysis_result:
                    # 添加历史记录标识
                    analysis_result["from_history"] = True
                    analysis_result["file_id"] = existing_file.id
                    analysis_result["analysis_id"] = latest_analysis.id
                    return analysis_result
        
        # 新文件或需要重新分析，保存文件
        stored_file_path = await file_storage_manager.save_uploaded_file(
            content, file_hash, file_extension
        )
        
        # 添加文件记录到数据库
        if not existing_file:
            from src.reporter.database import FileRecord
            file_record_obj = FileRecord(
                filename=file.filename,
                original_filename=file.filename,
                file_hash=file_hash,
                file_size=file_size,
                file_type=file_extension.lstrip('.'),
                file_path=str(stored_file_path)
            )
            file_record_id = await db_manager.add_file_record(file_record_obj)
            if file_record_id is None:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "code": "FILE_RECORD_ERROR",
                        "message": "文件记录保存失败",
                        "details": None,
                    },
                )
            file_record_obj.id = file_record_id
            file_record = file_record_obj
        else:
            file_record = existing_file
        
        # 执行分析
        analysis_result = analyze_data_file(str(stored_file_path), file.filename)
        
        # 确保file_record.id不为None
        if file_record.id is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "FILE_RECORD_ID_ERROR",
                    "message": "文件记录ID获取失败",
                    "details": None,
                },
            )
        
        # 保存分析结果
        from src.reporter.database import AnalysisRecord
        import json
        analysis_record_obj = AnalysisRecord(
            file_id=file_record.id,
            analysis_result=json.dumps({}),  # 临时空结果，稍后更新
            result_file_path=""  # 稍后更新
        )
        analysis_record_id = await db_manager.add_analysis_record(analysis_record_obj)
        if analysis_record_id is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "ANALYSIS_RECORD_ERROR",
                    "message": "分析记录保存失败",
                    "details": None,
                },
            )
        analysis_record_obj.id = analysis_record_id
        analysis_record = analysis_record_obj
        
        # 保存分析结果到文件
        result_file_path = await file_storage_manager.save_analysis_result(
            analysis_result, analysis_record_id
        )
        
        # 更新分析记录的结果文件路径
        await db_manager.update_analysis_result_path(
            analysis_record_id, str(result_file_path)
        )
        
        # 添加元数据
        analysis_result["from_history"] = False
        analysis_result["file_id"] = file_record.id
        analysis_result["analysis_id"] = analysis_record.id
        
        logger.info(f"文件分析完成: {file.filename} (file_id: {file_record.id})")
        return analysis_result

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


# 历史记录 API 端点
@app.get("/api/file-history")
@app.get("/api/files/history")
async def get_file_history(
    filter: str = Query("all", description="过滤条件"),
    limit: int = Query(20, description="返回记录数量"),
    offset: int = Query(0, description="偏移量"),
    page: int = Query(1, description="页码")
):
    """获取文件上传历史记录"""
    try:
        # 根据过滤条件确定文件类型
        file_type = None
        if filter in ["csv", "parquet"]:
            file_type = filter
        
        # 如果提供了page参数，计算offset
        if page > 1:
            offset = (page - 1) * limit
        
        history = await db_manager.get_file_history(limit, offset, file_type)
        has_more = len(history) == limit
        
        return {
            "success": True,
            "data": {
                "files": [{
                    "id": record["id"],
                    "filename": record["filename"],
                    "file_type": record["file_type"],
                    "file_size": record["file_size"],
                    "rows": 0,  # 暂时设为0，需要从分析结果中获取
                    "columns": 0,  # 暂时设为0，需要从分析结果中获取
                    "created_at": record["upload_time"],
                    "status": "completed"  # 简化状态
                } for record in history],
                "has_more": has_more
            }
        }
    except Exception as e:
        logger.error(f"获取文件历史记录失败: {e}")
        return {"success": False, "error": {"message": str(e)}}


@app.get("/api/files/{file_id}/analysis")
async def get_file_analysis_history(file_id: int):
    """
    获取指定文件的分析历史记录
    
    Args:
        file_id: 文件ID
    
    Returns:
        Dict: 分析历史记录
    """
    try:
        analyses = await db_manager.get_file_analysis_history(file_id)
        
        return {
            "success": True,
            "data": {
                "file_id": file_id,
                "analyses": analyses
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis history for file {file_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_HISTORY_ERROR",
                "message": "获取分析历史失败",
                "details": None,
            },
        )


@app.get("/api/analysis/{analysis_id}/result")
async def get_analysis_result(analysis_id: int):
    """
    获取指定分析的详细结果
    
    Args:
        analysis_id: 分析ID
    
    Returns:
        Dict: 分析结果
    """
    try:
        # 获取分析记录
        analysis_record = await db_manager.get_analysis_record(analysis_id)
        if not analysis_record:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ANALYSIS_NOT_FOUND",
                    "message": "分析记录不存在",
                    "details": None,
                },
            )
        
        # 加载分析结果
        analysis_result = await file_storage_manager.load_analysis_result(
            analysis_record.result_file_path
        )
        
        if not analysis_result:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "RESULT_FILE_NOT_FOUND",
                    "message": "分析结果文件不存在",
                    "details": None,
                },
            )
        
        # 添加元数据
        analysis_result["from_history"] = True
        analysis_result["analysis_id"] = analysis_id
        analysis_result["file_id"] = analysis_record.file_id
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result {analysis_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "RESULT_ERROR",
                "message": "获取分析结果失败",
                "details": None,
            },
        )


@app.post("/api/search")
async def search_files(request: dict):
    """搜索文件"""
    try:
        query = request.get("query", "").strip()
        if not query:
            return {"success": False, "error": {"message": "搜索关键词不能为空"}}
        
        results = await db_manager.search_files(query, 50)  # 默认限制50条结果
        
        return {
            "success": True,
            "results": [{
                "id": record["id"],
                "filename": record["filename"],
                "file_type": record["file_type"],
                "file_size": record["file_size"],
                "rows": 0,  # 暂时设为0，需要从分析结果中获取
                "columns": 0,  # 暂时设为0，需要从分析结果中获取
                "created_at": record["upload_time"],
                "relevance": 1.0,  # 简化相关性评分
                "snippet": f"文件大小: {record['file_size']} 字节"
            } for record in results]
        }
    except Exception as e:
        logger.error(f"搜索文件失败: {e}")
        return {"success": False, "error": {"message": str(e)}}


@app.get("/api/history/{history_id}")
async def get_history_result(history_id: int):
    """
    获取历史记录的分析结果
    
    Args:
        history_id: 历史记录ID
    
    Returns:
        Dict: 分析结果
    """
    try:
        # 获取文件记录
        file_record = await db_manager.get_file_record(history_id)
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "FILE_NOT_FOUND",
                    "message": "文件记录不存在",
                    "details": None,
                },
            )
        
        # 获取该文件的最新分析结果
        analyses = await db_manager.get_file_analysis_history(history_id)
        if not analyses:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ANALYSIS_NOT_FOUND",
                    "message": "该文件没有分析结果",
                    "details": None,
                },
            )
        
        # 获取最新的分析结果
        latest_analysis = analyses[0]  # 假设按时间倒序排列
        analysis_result = await file_storage_manager.load_analysis_result(
            latest_analysis["result_file_path"]
        )
        
        if not analysis_result:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "RESULT_FILE_NOT_FOUND",
                    "message": "分析结果文件不存在",
                    "details": None,
                },
            )
        
        # 添加元数据
        analysis_result["from_history"] = True
        analysis_result["history_id"] = history_id
        analysis_result["file_id"] = file_record.id
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history result {history_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "HISTORY_RESULT_ERROR",
                "message": "获取历史记录结果失败",
                "details": None,
            },
        )


@app.delete("/api/history/{history_id}")
async def delete_history_item(history_id: int):
    """
    删除历史记录
    
    Args:
        history_id: 历史记录ID
    
    Returns:
        Dict: 删除结果
    """
    try:
        # 获取文件记录
        file_record = await db_manager.get_file_record(history_id)
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "FILE_NOT_FOUND",
                    "message": "文件记录不存在",
                    "details": None,
                },
            )
        
        # 删除相关的分析结果文件
        analyses = await db_manager.get_file_analysis_history(history_id)
        for analysis in analyses:
            try:
                result_file_path = analysis.get("result_file_path")
                if result_file_path:
                    await file_storage_manager.delete_analysis_result(result_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete analysis result file: {e}")
        
        # 删除上传的文件
        try:
            if file_record.file_path:
                file_path = Path(file_record.file_path)
                if file_path.exists():
                    file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete uploaded file: {e}")
        
        # 从数据库中删除记录
        success = await db_manager.delete_file_record(history_id)
        
        if success:
            return {
                "success": True,
                "message": "历史记录删除成功"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "DELETE_FAILED",
                    "message": "删除历史记录失败",
                    "details": None,
                },
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting history item {history_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DELETE_ERROR",
                "message": "删除历史记录失败",
                "details": None,
            },
        )


@app.get("/api/storage/stats")
async def get_storage_stats():
    """
    获取存储统计信息
    
    Returns:
        Dict: 存储统计信息
    """
    try:
        stats = file_storage_manager.get_storage_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "STATS_ERROR",
                "message": "获取存储统计失败",
                "details": None,
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
