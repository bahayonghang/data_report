"""
基础统计分析模块

负责：
- 描述性统计计算
- 缺失值分析
- 异常值检测
- 数据质量评估
"""

import polars as pl
import numpy as np
from typing import Dict, Any, List
from scipy import stats
import logging
from ..utils.performance import monitor_performance
from .parallel_processor import parallel_column_processing, optimize_dataframe_processing

# 配置日志
logger = logging.getLogger(__name__)


@monitor_performance
def calculate_descriptive_stats(
    df: pl.DataFrame, columns: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    计算描述性统计量（优化版本，支持并行处理）

    Args:
        df: 数据框
        columns: 要分析的列名列表

    Returns:
        Dict[str, Dict[str, float]]: 各列的描述性统计
    """
    if not columns:
        logger.warning("没有提供列名")
        return {}
    
    # 优化数据框处理
    optimized_df = optimize_dataframe_processing(df)
    
    # 过滤有效列
    valid_columns = [col for col in columns if col in optimized_df.columns]
    if not valid_columns:
        logger.warning("没有有效的列")
        return {}
    
    logger.info(f"开始计算 {len(valid_columns)} 列的描述性统计")
    
    def calculate_single_column_stats(col_series: pl.Series) -> Dict[str, float]:
        """
        计算单列的描述性统计
        
        Args:
            col_series: 列数据
            
        Returns:
            统计结果字典
        """
        try:
            # 去除空值
            col_data = col_series.drop_nulls()
            if len(col_data) == 0:
                return {}
            
            # 转换为numpy数组进行计算
            values = col_data.to_numpy()
            
            # 检查数据类型
            if not np.issubdtype(values.dtype, np.number):
                logger.warning(f"列 '{col_series.name}' 不是数值类型，跳过")
                return {}
            
            # 计算统计量
            result = {
                "count": len(values),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "q1": float(np.percentile(values, 25)),
                "q3": float(np.percentile(values, 75)),
            }
            
            # 计算偏度和峰度（需要足够的数据点）
            if len(values) >= 3:
                result["skewness"] = float(stats.skew(values))
                result["kurtosis"] = float(stats.kurtosis(values))
            else:
                result["skewness"] = 0.0
                result["kurtosis"] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"计算列统计失败: {e}")
            return {}
    
    # 根据列数决定是否使用并行处理
    if len(valid_columns) <= 2:
        # 少量列，直接顺序处理
        stats_dict = {}
        for col in valid_columns:
            col_stats = calculate_single_column_stats(optimized_df[col])
            if col_stats:
                stats_dict[col] = col_stats
    else:
        # 多列，使用并行处理
        stats_dict = parallel_column_processing(
            optimized_df, 
            valid_columns, 
            calculate_single_column_stats,
            max_workers=min(4, len(valid_columns))
        )
        # 过滤空结果
        stats_dict = {k: v for k, v in stats_dict.items() if v}
    
    logger.info(f"描述性统计计算完成，处理了 {len(stats_dict)} 列")
    return stats_dict


def analyze_missing_values(df: pl.DataFrame) -> Dict[str, Dict[str, int]]:
    """
    分析缺失值情况

    Args:
        df: 数据框

    Returns:
        Dict[str, Dict[str, int]]: 各列的缺失值统计
    """
    missing_stats = {}
    total_rows = len(df)

    for col in df.columns:
        null_count = df[col].null_count()
        non_null_count = total_rows - null_count

        missing_stats[col] = {
            "total_count": total_rows,
            "null_count": null_count,
            "non_null_count": non_null_count,
            "null_percentage": round((null_count / total_rows) * 100, 2)
            if total_rows > 0
            else 0,
        }

    return missing_stats


def detect_outliers(
    df: pl.DataFrame, columns: List[str], method: str = "iqr"
) -> Dict[str, Dict[str, Any]]:
    """
    检测异常值

    Args:
        df: 数据框
        columns: 要检测的列名列表
        method: 检测方法 ('iqr' 或 'zscore')

    Returns:
        Dict[str, Dict[str, Any]]: 各列的异常值信息
    """
    outliers_dict = {}

    for col in columns:
        if col not in df.columns:
            continue

        col_data = df[col].drop_nulls()
        if len(col_data) == 0:
            continue

        values = col_data.to_numpy()

        # 初始化变量
        outlier_indices = np.array([])
        outlier_values = np.array([])
        lower_bound = None
        upper_bound = None
        
        if method == "iqr":
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_mask = (values < lower_bound) | (values > upper_bound)
            outlier_indices = np.where(outlier_mask)[0]
            outlier_values = values[outlier_mask]

        elif method == "zscore":
            z_scores = np.abs(stats.zscore(values))
            outlier_mask = z_scores > 3
            outlier_indices = np.where(outlier_mask)[0]
            outlier_values = values[outlier_mask]

        outliers_dict[col] = {
            "outlier_count": len(outlier_values),
            "outlier_indices": outlier_indices.tolist(),
            "outlier_values": outlier_values.tolist(),
            "outlier_percentage": round((len(outlier_values) / len(values)) * 100, 2),
            "bounds": {
                "lower": float(lower_bound) if lower_bound is not None else None,
                "upper": float(upper_bound) if upper_bound is not None else None,
            },
        }

    return outliers_dict


@monitor_performance
def calculate_correlation_matrix(
    df: pl.DataFrame, columns: List[str]
) -> Dict[str, Any]:
    """
    计算相关系数矩阵（优化版本，支持并行处理和更好的错误处理）

    Args:
        df: 数据框
        columns: 要分析的数值列列表

    Returns:
        Dict[str, Any]: 相关系数矩阵和相关信息
    """
    if not columns or len(columns) < 2:
        logger.warning("列数不足，无法计算相关性矩阵")
        return {"matrix": {}, "columns": [], "shape": (0, 0), "warnings": []}

    logger.info(f"开始计算 {len(columns)} 列的相关性矩阵")
    
    # 优化数据框处理
    optimized_df = optimize_dataframe_processing(df)
    
    # 创建数值数据框，去除缺失值
    try:
        numeric_df = optimized_df.select(columns).drop_nulls()
    except Exception as e:
        logger.error(f"选择数值列失败: {e}")
        return {"matrix": {}, "columns": [], "shape": (0, 0), "warnings": [f"数据选择失败: {e}"]}

    if len(numeric_df) == 0:
        logger.warning("所有数据都包含缺失值")
        return {"matrix": {}, "columns": columns, "shape": (0, 0), "warnings": ["所有数据都包含缺失值"]}

    warnings_list = []
    valid_columns = []
    
    # 并行检查列的有效性
    def check_column_validity(col: str) -> tuple[str, bool, str]:
        """
        检查列的有效性
        
        Args:
            col: 列名
            
        Returns:
            (列名, 是否有效, 警告信息)
        """
        try:
            if col not in numeric_df.columns:
                return col, False, f"列 '{col}' 不存在"
            
            col_values = numeric_df[col].to_numpy()
            
            # 检查数据类型
            if not np.issubdtype(col_values.dtype, np.number):
                return col, False, f"列 '{col}' 不是数值类型"
            
            # 检查是否为常数列（标准差为0或接近0）
            if len(col_values) < 2:
                return col, False, f"列 '{col}' 数据点不足"
            
            col_std = np.std(col_values, ddof=1)
            if col_std < 1e-10:  # 接近零的阈值
                return col, False, f"列 '{col}' 为常数列，已从相关性分析中排除"
            
            return col, True, ""
            
        except Exception as e:
            return col, False, f"列 '{col}' 检查失败: {e}"
    
    # 检查所有列的有效性
    for col in columns:
        col_name, is_valid, warning = check_column_validity(col)
        if is_valid:
            valid_columns.append(col_name)
        elif warning:
            warnings_list.append(warning)
    
    # 如果有效列少于2个，无法计算相关性
    if len(valid_columns) < 2:
        logger.warning(f"有效列数不足: {len(valid_columns)}")
        return {
            "matrix": {}, 
            "columns": valid_columns, 
            "shape": (len(valid_columns), len(valid_columns)),
            "warnings": warnings_list + ["有效数值列少于2个，无法计算相关性矩阵"]
        }
    
    # 只选择有效列进行相关性计算
    valid_df = numeric_df.select(valid_columns)
    
    # 抑制NumPy除零警告并计算相关系数矩阵
    with np.errstate(divide='ignore', invalid='ignore'):
        try:
            # 选择有效列并转换为numpy数组
            logger.info(f"计算 {len(valid_columns)} 个有效列的相关性")
            correlation_data = valid_df.to_numpy()
            
            # 使用numpy计算相关系数矩阵
            corr_matrix = np.corrcoef(correlation_data, rowvar=False)
            
            # 处理NaN值（用0替换）
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
            
            # 确保矩阵是对称的
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            np.fill_diagonal(corr_matrix, 1.0)
            
            # 转换为字典格式
            matrix_dict = {}
            for i, col1 in enumerate(valid_columns):
                matrix_dict[col1] = {}
                for j, col2 in enumerate(valid_columns):
                    matrix_dict[col1][col2] = float(corr_matrix[i, j])
            
            logger.info(f"相关性矩阵计算完成，矩阵大小: {corr_matrix.shape}")
            
            return {
                "matrix": matrix_dict,
                "columns": valid_columns,
                "shape": corr_matrix.shape,
                "sample_size": len(valid_df),
                "warnings": warnings_list,
                "excluded_columns": [col for col in columns if col not in valid_columns]
            }
            
        except Exception as e:
            error_msg = f"相关性矩阵计算失败: {str(e)}"
            logger.error(error_msg)
            warnings_list.append(error_msg)
            return {
                "matrix": {},
                "columns": valid_columns,
                "shape": (0, 0),
                "warnings": warnings_list,
                "error": str(e)
            }


def get_data_summary(df: pl.DataFrame) -> Dict[str, Any]:
    """
    获取数据摘要信息

    Args:
        df: 数据框

    Returns:
        Dict[str, Any]: 数据摘要信息
    """
    numeric_columns = [
        col
        for col in df.columns
        if df[col].dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]
    ]

    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(numeric_columns),
        "categorical_columns": len(df.columns) - len(numeric_columns),
        "columns": df.columns,
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
    }

    # 添加描述性统计
    if numeric_columns:
        summary["descriptive_stats"] = calculate_descriptive_stats(df, numeric_columns)
        summary["missing_values"] = analyze_missing_values(df)
        summary["correlation_matrix"] = calculate_correlation_matrix(
            df, numeric_columns
        )

    return summary
