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


def calculate_descriptive_stats(df: pl.DataFrame, columns: List[str]) -> Dict[str, Dict[str, float]]:
    """
    计算描述性统计量
    
    Args:
        df: 数据框
        columns: 要分析的列名列表
        
    Returns:
        Dict[str, Dict[str, float]]: 各列的描述性统计
    """
    stats_dict = {}
    
    for col in columns:
        if col not in df.columns:
            continue
            
        col_data = df[col].drop_nulls()
        if len(col_data) == 0:
            continue
            
        # 转换为numpy数组进行计算
        values = col_data.to_numpy()
        
        stats_dict[col] = {
            'count': len(values),
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std': float(np.std(values, ddof=1)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            'q1': float(np.percentile(values, 25)),
            'q3': float(np.percentile(values, 75)),
            'skewness': float(stats.skew(values)),
            'kurtosis': float(stats.kurtosis(values))
        }
    
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
            'total_count': total_rows,
            'null_count': null_count,
            'non_null_count': non_null_count,
            'null_percentage': round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0
        }
    
    return missing_stats


def detect_outliers(df: pl.DataFrame, columns: List[str], method: str = 'iqr') -> Dict[str, Dict[str, Any]]:
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
        
        if method == 'iqr':
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outlier_mask = (values < lower_bound) | (values > upper_bound)
            outlier_indices = np.where(outlier_mask)[0]
            outlier_values = values[outlier_mask]
            
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(values))
            outlier_mask = z_scores > 3
            outlier_indices = np.where(outlier_mask)[0]
            outlier_values = values[outlier_mask]
        
        outliers_dict[col] = {
            'outlier_count': len(outlier_values),
            'outlier_indices': outlier_indices.tolist(),
            'outlier_values': outlier_values.tolist(),
            'outlier_percentage': round((len(outlier_values) / len(values)) * 100, 2),
            'bounds': {
                'lower': float(lower_bound) if method == 'iqr' else None,
                'upper': float(upper_bound) if method == 'iqr' else None
            }
        }
    
    return outliers_dict


def calculate_correlation_matrix(df: pl.DataFrame, columns: List[str]) -> Dict[str, Any]:
    """
    计算相关系数矩阵
    
    Args:
        df: 数据框
        columns: 要分析的数值列列表
        
    Returns:
        Dict[str, Any]: 相关系数矩阵和相关信息
    """
    if not columns or len(columns) < 2:
        return {"matrix": {}, "columns": [], "shape": (0, 0)}
    
    # 创建数值数据框，去除缺失值
    numeric_df = df.select(columns).drop_nulls()
    
    if len(numeric_df) == 0:
        return {"matrix": {}, "columns": columns, "shape": (0, 0)}
    
    # 计算相关系数矩阵
    corr_matrix = numeric_df.corr()
    
    # 转换为字典格式
    matrix_dict = {}
    for i, col1 in enumerate(columns):
        matrix_dict[col1] = {}
        for j, col2 in enumerate(columns):
            matrix_dict[col1][col2] = float(corr_matrix[i, j])
    
    return {
        "matrix": matrix_dict,
        "columns": columns,
        "shape": (len(columns), len(columns)),
        "sample_size": len(numeric_df)
    }


def get_data_summary(df: pl.DataFrame) -> Dict[str, Any]:
    """
    获取数据摘要信息
    
    Args:
        df: 数据框
        
    Returns:
        Dict[str, Any]: 数据摘要信息
    """
    numeric_columns = [col for col in df.columns 
                      if df[col].dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]]
    
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'numeric_columns': len(numeric_columns),
        'categorical_columns': len(df.columns) - len(numeric_columns),
        'columns': df.columns,
        'dtypes': {col: str(df[col].dtype) for col in df.columns}
    }
    
    # 添加描述性统计
    if numeric_columns:
        summary['descriptive_stats'] = calculate_descriptive_stats(df, numeric_columns)
        summary['missing_values'] = analyze_missing_values(df)
        summary['correlation_matrix'] = calculate_correlation_matrix(df, numeric_columns)
    
    return summary