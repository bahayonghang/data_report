"""数据采样工具模块

提供时间序列数据的智能采样功能，用于优化大数据集的分析性能。
"""

import polars as pl
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_optimal_sample_size(data_length: int, max_sample_size: int = 10000) -> int:
    """计算最优采样大小
    
    Args:
        data_length: 原始数据长度
        max_sample_size: 最大采样大小
        
    Returns:
        int: 最优采样大小
    """
    if data_length <= max_sample_size:
        return data_length
    
    # 对于大数据集，采用分层采样策略
    if data_length > 100000:
        return min(max_sample_size, max(5000, int(data_length * 0.05)))
    elif data_length > 50000:
        return min(max_sample_size, max(8000, int(data_length * 0.1)))
    else:
        return min(max_sample_size, max(5000, int(data_length * 0.2)))


def smart_time_series_sample(
    df: pl.DataFrame, 
    time_col: str, 
    target_size: int,
    preserve_patterns: bool = True
) -> pl.DataFrame:
    """智能时间序列采样
    
    保持时间序列的关键特征，包括趋势、季节性和异常值。
    
    Args:
        df: 原始数据框
        time_col: 时间列名
        target_size: 目标采样大小
        preserve_patterns: 是否保持时间模式
        
    Returns:
        pl.DataFrame: 采样后的数据框
    """
    if len(df) <= target_size:
        return df
    
    logger.info(f"开始智能采样：从 {len(df)} 行采样到 {target_size} 行")
    
    try:
        # 确保数据按时间排序
        df_sorted = df.sort(time_col)
        
        if preserve_patterns:
            # 分层采样策略：保持时间分布
            return _stratified_time_sample(df_sorted, time_col, target_size)
        else:
            # 简单等间隔采样
            step = len(df_sorted) // target_size
            indices = list(range(0, len(df_sorted), step))[:target_size]
            return df_sorted[indices]
            
    except Exception as e:
        logger.warning(f"智能采样失败，使用简单采样: {e}")
        # 降级到简单随机采样
        return df.sample(n=target_size, seed=42)


def _stratified_time_sample(
    df: pl.DataFrame, 
    time_col: str, 
    target_size: int
) -> pl.DataFrame:
    """分层时间采样
    
    将时间序列分成多个时间段，从每个时间段中采样，保持时间分布。
    
    Args:
        df: 排序后的数据框
        time_col: 时间列名
        target_size: 目标采样大小
        
    Returns:
        pl.DataFrame: 采样后的数据框
    """
    total_rows = len(df)
    
    # 计算分层数量（时间段数量）
    num_strata = min(20, max(5, target_size // 100))  # 5-20个时间段
    rows_per_stratum = total_rows // num_strata
    samples_per_stratum = target_size // num_strata
    
    sampled_indices = []
    
    for i in range(num_strata):
        start_idx = i * rows_per_stratum
        end_idx = min((i + 1) * rows_per_stratum, total_rows)
        
        if start_idx >= total_rows:
            break
            
        # 从当前时间段中采样
        stratum_size = end_idx - start_idx
        if stratum_size <= samples_per_stratum:
            # 如果时间段太小，全部保留
            sampled_indices.extend(range(start_idx, end_idx))
        else:
            # 等间隔采样
            step = stratum_size // samples_per_stratum
            stratum_indices = [start_idx + j * step for j in range(samples_per_stratum)]
            sampled_indices.extend(stratum_indices)
    
    # 确保不超过目标大小
    sampled_indices = sampled_indices[:target_size]
    
    return df[sampled_indices]


def resample_time_series(
    df: pl.DataFrame, 
    time_col: str, 
    freq: str = "1h",
    agg_method: str = "mean"
) -> pl.DataFrame:
    """时间序列重采样
    
    使用pandas风格的重采样来降低数据密度。
    
    Args:
        df: 数据框
        time_col: 时间列名
        freq: 重采样频率 (如 '1h', '1d', '1w')
        agg_method: 聚合方法 ('mean', 'max', 'min', 'sum')
        
    Returns:
        pl.DataFrame: 重采样后的数据框
    """
    try:
        # 转换为pandas进行重采样（polars的重采样功能有限）
        import pandas as pd
        
        # 转换为pandas
        pdf = df.to_pandas()
        pdf[time_col] = pd.to_datetime(pdf[time_col])
        pdf = pdf.set_index(time_col)
        
        # 重采样
        if agg_method == "mean":
            resampled = pdf.resample(freq).mean()
        elif agg_method == "max":
            resampled = pdf.resample(freq).max()
        elif agg_method == "min":
            resampled = pdf.resample(freq).min()
        elif agg_method == "sum":
            resampled = pdf.resample(freq).sum()
        else:
            resampled = pdf.resample(freq).mean()
        
        # 重置索引并转换回polars
        resampled = resampled.reset_index().dropna()
        
        # 转换回polars
        result_df = pl.from_pandas(resampled)
        
        logger.info(f"重采样完成：从 {len(df)} 行降至 {len(result_df)} 行")
        return result_df
        
    except Exception as e:
        logger.warning(f"重采样失败: {e}，返回原始数据")
        return df


def adaptive_sampling_strategy(
    df: pl.DataFrame, 
    time_col: Optional[str] = None,
    performance_threshold: int = 10000
) -> Tuple[pl.DataFrame, Dict[str, Any]]:
    """自适应采样策略
    
    根据数据大小和特征自动选择最佳采样方法。
    
    Args:
        df: 原始数据框
        time_col: 时间列名（可选）
        performance_threshold: 性能阈值，超过此值启用采样
        
    Returns:
        Tuple[pl.DataFrame, Dict]: (采样后的数据框, 采样信息)
    """
    original_size = len(df)
    sampling_info = {
        "original_size": original_size,
        "sampled_size": original_size,
        "sampling_method": "none",
        "sampling_ratio": 1.0,
        "performance_gain": 1.0
    }
    
    # 如果数据量小于阈值，不进行采样
    if original_size <= performance_threshold:
        logger.info(f"数据量 {original_size} 小于阈值 {performance_threshold}，无需采样")
        return df, sampling_info
    
    # 计算目标采样大小
    target_size = calculate_optimal_sample_size(original_size, performance_threshold)
    
    # 选择采样策略
    if time_col and time_col in df.columns:
        # 有时间列，使用智能时间序列采样
        try:
            # 首先尝试重采样（如果数据量非常大）
            if original_size > 50000:
                logger.info("数据量过大，尝试时间重采样")
                # 根据数据密度选择重采样频率
                time_range_days = _estimate_time_range_days(df, time_col)
                if time_range_days and time_range_days > 365:
                    freq = "1d"  # 日采样
                elif time_range_days and time_range_days > 30:
                    freq = "1h"  # 小时采样
                else:
                    freq = "10min"  # 10分钟采样
                
                resampled_df = resample_time_series(df, time_col, freq)
                if len(resampled_df) <= target_size:
                    sampling_info.update({
                        "sampled_size": len(resampled_df),
                        "sampling_method": f"time_resample_{freq}",
                        "sampling_ratio": len(resampled_df) / original_size,
                        "performance_gain": original_size / len(resampled_df)
                    })
                    logger.info(f"重采样成功：{original_size} -> {len(resampled_df)} 行")
                    return resampled_df, sampling_info
            
            # 重采样不够或失败，使用智能采样
            sampled_df = smart_time_series_sample(df, time_col, target_size)
            sampling_info.update({
                "sampled_size": len(sampled_df),
                "sampling_method": "smart_time_series",
                "sampling_ratio": len(sampled_df) / original_size,
                "performance_gain": original_size / len(sampled_df)
            })
            
        except Exception as e:
            logger.warning(f"智能时间采样失败: {e}，使用简单采样")
            # 降级到简单采样
            sampled_df = df.sample(n=target_size, seed=42)
            sampling_info.update({
                "sampled_size": target_size,
                "sampling_method": "random_fallback",
                "sampling_ratio": target_size / original_size,
                "performance_gain": original_size / target_size
            })
    else:
        # 无时间列，使用简单随机采样
        sampled_df = df.sample(n=target_size, seed=42)
        sampling_info.update({
            "sampled_size": target_size,
            "sampling_method": "random",
            "sampling_ratio": target_size / original_size,
            "performance_gain": original_size / target_size
        })
    
    logger.info(
        f"采样完成：{original_size} -> {sampling_info['sampled_size']} 行 "
        f"(方法: {sampling_info['sampling_method']}, "
        f"性能提升: {sampling_info['performance_gain']:.1f}x)"
    )
    
    return sampled_df, sampling_info


def _estimate_time_range_days(df: pl.DataFrame, time_col: str) -> Optional[float]:
    """估算时间范围（天数）"""
    try:
        # 确保时间列是datetime类型
        if df[time_col].dtype != pl.Datetime:
            df = df.with_columns(pl.col(time_col).cast(pl.Datetime))
        
        # 使用polars表达式计算时间范围
        result = df.select([
            (pl.col(time_col).max() - pl.col(time_col).min()).dt.total_days().alias("days_diff")
        ])
        
        days_diff = result["days_diff"][0]
        if days_diff is not None:
            return float(days_diff)
    except Exception:
        pass
    return None