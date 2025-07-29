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
from typing import Dict, Any
from statsmodels.tsa.stattools import adfuller
import logging
from ..utils.sampling import adaptive_sampling_strategy

logger = logging.getLogger(__name__)


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
            "start": None,
            "end": None,
            "duration_days": None,
            "total_points": 0,
            "frequency": None,
            "gaps": [],
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
            "start": None,
            "end": None,
            "duration_days": None,
            "total_points": len(time_series),
            "frequency": None,
            "gaps": [],
        }

    # 计算持续时间（天数）
    try:
        # 使用polars进行时间计算
        # 将时间值转换为polars datetime类型
        start_pl = pl.Series([str(start_time)]).str.to_datetime().item()
        end_pl = pl.Series([str(end_time)]).str.to_datetime().item()
        
        # 计算时间差并转换为天数
        duration_pl = end_pl - start_pl
        duration_days = duration_pl.total_days() if hasattr(duration_pl, 'total_days') else 0
    except Exception:
        duration_days = 0

    # 检测频率
    if len(sorted_series) > 1:
        # 计算连续时间点的平均间隔
        diffs = []
        # 使用polars计算时间差以提高性能
        try:
            # 使用polars进行差分计算
            # 确保时间列是datetime类型
            if sorted_series.dtype != pl.Datetime:
                sorted_series = sorted_series.str.to_datetime()
            
            # 计算时间差分（天数）
            time_diffs = sorted_series.diff().dt.total_days()
            # 过滤掉null值并转换为列表
            diffs = time_diffs.drop_nulls().to_list()
        except Exception:
            # 降级到简单采样计算
            diffs = []
            sample_size = min(len(sorted_series), 100)  # 大幅限制计算量
            step = max(1, len(sorted_series) // sample_size)
            for i in range(step, len(sorted_series), step):
                try:
                    # 使用polars进行时间转换和计算
                    t1 = pl.Series([str(sorted_series[i-step])]).str.to_datetime().item()
                    t2 = pl.Series([str(sorted_series[i])]).str.to_datetime().item()
                    diff_days = (t2 - t1).total_days()
                    diffs.append(diff_days)
                except Exception:
                    continue

        avg_interval = np.mean(diffs) if diffs else 1

        if avg_interval == 1:
            frequency = "daily"
        elif avg_interval == 7:
            frequency = "weekly"
        elif avg_interval > 27 and avg_interval < 32:
            frequency = "monthly"
        elif avg_interval > 360 and avg_interval < 370:
            frequency = "yearly"
        else:
            frequency = f"{avg_interval:.1f} days"
    else:
        frequency = "single_point"

    # 检测时间间隔
    gaps = []
    if len(sorted_series) > 1:
        # 限制gap检测的数量以提高性能
        max_gap_checks = min(len(sorted_series), 100)  # 进一步限制
        step = max(1, len(sorted_series) // max_gap_checks)
        
        for i in range(step, len(sorted_series), step):
            try:
                # 使用polars进行时间转换和计算
                t1 = pl.Series([str(sorted_series[i-step])]).str.to_datetime().item()
                t2 = pl.Series([str(sorted_series[i])]).str.to_datetime().item()
                gap_days = (t2 - t1).total_days()
                if gap_days > step:  # 考虑步长的gap
                    gaps.append(
                        {
                            "start": str(sorted_series[i - step]),
                            "end": str(sorted_series[i]),
                            "duration_days": gap_days,
                        }
                    )
            except Exception:
                continue

    return {
        "start": str(start_time),
        "end": str(end_time),
        "duration_days": duration_days,
        "total_points": len(time_series),
        "frequency": frequency,
        "gaps": gaps,
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
            "adf_statistic": None,
            "p_value": None,
            "critical_values": {},
            "is_stationary": None,
            "interpretation": "数据不足，无法进行ADF检验",
        }

    # 去除空值并转换为numpy数组
    clean_series = series.drop_nulls()
    if len(clean_series) < 4:
        return {
            "adf_statistic": None,
            "p_value": None,
            "critical_values": {},
            "is_stationary": None,
            "interpretation": "有效数据不足，无法进行ADF检验",
        }

    values = clean_series.to_numpy()

    try:
        # 执行ADF检验
        result = adfuller(values, autolag="AIC")
        
        # 安全解包结果（处理不同版本的statsmodels）
        adf_statistic = result[0]
        p_value = result[1]
        critical_values = result[4] if len(result) > 4 else {}

        # 判断平稳性
        is_stationary = p_value < 0.05

        # 生成解释
        if is_stationary:
            interpretation = "时间序列是平稳的（p值 < 0.05）"
        else:
            interpretation = "时间序列是非平稳的（p值 ≥ 0.05）"

        return {
            "adf_statistic": float(adf_statistic),
            "p_value": float(p_value),
            "critical_values": {str(k): float(v) for k, v in critical_values.items()},
            "is_stationary": bool(is_stationary),
            "interpretation": interpretation,
        }

    except Exception as e:
        return {
            "adf_statistic": None,
            "p_value": None,
            "critical_values": {},
            "is_stationary": None,
            "interpretation": f"ADF检验失败: {str(e)}",
        }


def analyze_time_series_optimized(
    df: pl.DataFrame, 
    time_column: str, 
    numeric_columns: list,
    performance_threshold: int = 10000
) -> Dict[str, Any]:
    """
    优化的时间序列分析，支持大数据集处理

    Args:
        df: 数据框
        time_column: 时间列名
        numeric_columns: 数值列名列表
        performance_threshold: 性能阈值，超过此值启用采样

    Returns:
        Dict[str, Any]: 时间序列分析结果
    """
    if time_column not in df.columns:
        return {"error": "时间列不存在"}
    
    original_size = len(df)
    logger.info(f"开始时间序列分析，数据量: {original_size} 行")
    
    # 应用自适应采样策略
    sampled_df, sampling_info = adaptive_sampling_strategy(
        df, time_column, performance_threshold
    )
    
    logger.info(
        f"采样完成: {sampling_info['original_size']} -> {sampling_info['sampled_size']} 行, "
        f"方法: {sampling_info['sampling_method']}"
    )
    
    # 分析时间范围
    time_analysis = calculate_time_range(sampled_df[time_column])
    
    # 对数值列进行ADF检验（限制数量以提高性能）
    adf_results = {}
    max_adf_tests = min(len(numeric_columns), 5)  # 最多测试5列
    
    for i, col in enumerate(numeric_columns[:max_adf_tests]):
        if col in sampled_df.columns:
            logger.info(f"执行ADF检验: {col} ({i+1}/{max_adf_tests})")
            try:
                adf_results[col] = perform_adf_test(sampled_df[col])
            except Exception as e:
                logger.warning(f"ADF检验失败 {col}: {e}")
                adf_results[col] = {
                    "error": f"检验失败: {str(e)}",
                    "is_stationary": None
                }
    
    # 计算基础统计信息
    basic_stats = {}
    for col in numeric_columns[:5]:  # 限制统计列数
        if col in sampled_df.columns:
            try:
                clean_values = sampled_df[col].drop_nulls()
                if len(clean_values) > 0:
                    basic_stats[col] = {
                        "count": len(clean_values),
                        "mean": float(clean_values.mean()) if clean_values.mean() is not None else None,
                        "std": float(clean_values.std()) if clean_values.std() is not None else None,
                        "min": float(clean_values.min()) if clean_values.min() is not None else None,
                        "max": float(clean_values.max()) if clean_values.max() is not None else None,
                    }
            except Exception as e:
                logger.warning(f"统计计算失败 {col}: {e}")
                basic_stats[col] = {"error": str(e)}
    
    return {
        "time_analysis": time_analysis,
        "adf_tests": adf_results,
        "basic_stats": basic_stats,
        "sampling_info": sampling_info,
        "performance_metrics": {
            "original_rows": original_size,
            "processed_rows": len(sampled_df),
            "columns_analyzed": min(len(numeric_columns), 5),
            "adf_tests_performed": len(adf_results)
        }
    }


def analyze_time_series(
    df: pl.DataFrame, time_column: str, value_column: str
) -> Dict[str, Any]:
    """
    综合分析时间序列（保持向后兼容）

    Args:
        df: 数据框
        time_column: 时间列名
        value_column: 数值列名

    Returns:
        Dict[str, Any]: 时间序列分析结果
    """
    if time_column not in df.columns or value_column not in df.columns:
        return {}

    # 使用优化版本
    return analyze_time_series_optimized(df, time_column, [value_column])
