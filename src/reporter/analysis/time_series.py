"""
时间序列分析模块

负责：
- ADF平稳性检验
- 时间范围计算
- 时间序列特征提取
- 趋势分析
"""

import polars as pl
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.stattools import adfuller


def calculate_time_range(time_series: pl.Series) -> Dict[str, Any]:
    """
    计算时间范围信息
    
    Args:
        time_series: 时间序列数据
        
    Returns:
        Dict[str, Any]: 时间范围信息
    """
    if time_series is None or len(time_series) == 0:
        return {
            'start': None,
            'end': None,
            'duration_days': None,
            'total_points': 0,
            'frequency': None,
            'gaps': []
        }
    
    # 确保时间序列是datetime类型
    if time_series.dtype != pl.Datetime:
        time_series = time_series.cast(pl.Datetime)
    
    # 排序时间序列
    sorted_series = time_series.sort()
    
    # 计算时间范围
    start_time = sorted_series.min()
    end_time = sorted_series.max()
    
    if start_time is None or end_time is None:
        return {
            'start': None,
            'end': None,
            'duration_days': None,
            'total_points': len(time_series),
            'frequency': None,
            'gaps': []
        }
    
    # 计算持续时间（天数）
    duration_days = (end_time - start_time).days
    
    # 检测频率
    if len(sorted_series) > 1:
        # 计算连续时间点的平均间隔
        diffs = []
        for i in range(1, len(sorted_series)):
            diff = (sorted_series[i] - sorted_series[i-1]).days
            diffs.append(diff)
        
        avg_interval = np.mean(diffs) if diffs else 1
        
        if avg_interval == 1:
            frequency = 'daily'
        elif avg_interval == 7:
            frequency = 'weekly'
        elif avg_interval > 27 and avg_interval < 32:
            frequency = 'monthly'
        elif avg_interval > 360 and avg_interval < 370:
            frequency = 'yearly'
        else:
            frequency = f'{avg_interval:.1f} days'
    else:
        frequency = 'single_point'
    
    # 检测时间间隔
    gaps = []
    if len(sorted_series) > 1:
        for i in range(1, len(sorted_series)):
            gap_days = (sorted_series[i] - sorted_series[i-1]).days
            if gap_days > 1:  # 大于1天的认为是gap
                gaps.append({
                    'start': str(sorted_series[i-1]),
                    'end': str(sorted_series[i]),
                    'duration_days': gap_days
                })
    
    return {
        'start': str(start_time),
        'end': str(end_time),
        'duration_days': duration_days,
        'total_points': len(time_series),
        'frequency': frequency,
        'gaps': gaps
    }


def perform_adf_test(series: pl.Series) -> Dict[str, Any]:
    """
    执行ADF平稳性检验
    
    Args:
        series: 时间序列数据
        
    Returns:
        Dict[str, Any]: ADF检验结果
    """
    if series is None or len(series) < 4:
        return {
            'adf_statistic': None,
            'p_value': None,
            'critical_values': {},
            'is_stationary': None,
            'interpretation': '数据不足，无法进行ADF检验'
        }
    
    # 去除空值并转换为numpy数组
    clean_series = series.drop_nulls()
    if len(clean_series) < 4:
        return {
            'adf_statistic': None,
            'p_value': None,
            'critical_values': {},
            'is_stationary': None,
            'interpretation': '有效数据不足，无法进行ADF检验'
        }
    
    values = clean_series.to_numpy()
    
    try:
        # 执行ADF检验
        result = adfuller(values, autolag='AIC')
        
        adf_statistic, p_value, _, _, critical_values, _ = result
        
        # 判断平稳性
        is_stationary = p_value < 0.05
        
        # 生成解释
        if is_stationary:
            interpretation = '时间序列是平稳的（p值 < 0.05）'
        else:
            interpretation = '时间序列是非平稳的（p值 ≥ 0.05）'
        
        return {
            'adf_statistic': float(adf_statistic),
            'p_value': float(p_value),
            'critical_values': {str(k): float(v) for k, v in critical_values.items()},
            'is_stationary': bool(is_stationary),
            'interpretation': interpretation
        }
        
    except Exception as e:
        return {
            'adf_statistic': None,
            'p_value': None,
            'critical_values': {},
            'is_stationary': None,
            'interpretation': f'ADF检验失败: {str(e)}'
        }


def analyze_time_series(df: pl.DataFrame, time_column: str, value_column: str) -> Dict[str, Any]:
    """
    综合分析时间序列
    
    Args:
        df: 数据框
        time_column: 时间列名
        value_column: 数值列名
        
    Returns:
        Dict[str, Any]: 时间序列分析结果
    """
    if time_column not in df.columns or value_column not in df.columns:
        return {}
    
    time_series = df[time_column]
    values = df[value_column]
    
    return {
        'time_analysis': calculate_time_range(time_series),
        'adf_test': perform_adf_test(values),
        'basic_stats': {
            'count': len(values.drop_nulls()),
            'mean': float(values.drop_nulls().mean()) if len(values.drop_nulls()) > 0 else None,
            'std': float(values.drop_nulls().std()) if len(values.drop_nulls()) > 0 else None
        }
    }