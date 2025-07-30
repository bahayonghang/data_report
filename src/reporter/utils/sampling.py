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
    
    使用polars的group_by_dynamic进行高效的时间序列重采样。
    
    Args:
        df: 数据框
        time_col: 时间列名
        freq: 重采样频率 (如 '1h', '1d', '1w')
        agg_method: 聚合方法 ('mean', 'max', 'min', 'sum')
        
    Returns:
        pl.DataFrame: 重采样后的数据框
    """
    try:
        import polars as pl
        
        # 检查数据有效性
        if df.height == 0:
            logger.warning("输入数据为空")
            return df
            
        if time_col not in df.columns:
            logger.warning(f"时间列 '{time_col}' 不存在")
            return df
            
        # 检查时间列是否全部为空
        if df[time_col].is_null().all():
            logger.warning(f"时间列 '{time_col}' 全部为空")
            return df
            
        # 计算有效时间数据的比例
        valid_time_count = df[time_col].is_not_null().sum()
        valid_time_ratio = valid_time_count / len(df)
        if valid_time_ratio < 0.1:  # 如果有效时间数据少于10%
            logger.warning(f"时间列 '{time_col}' 有效数据比例过低: {valid_time_ratio:.2%}")
            return df
        
        # 确保时间列是datetime类型
        if df[time_col].dtype == pl.Datetime:
            # 如果已经是datetime类型，直接使用
            df_with_time = df
        elif df[time_col].dtype == pl.Date:
            # 如果是date类型，转换为datetime
            df_with_time = df.with_columns(
                pl.col(time_col).cast(pl.Datetime).alias(time_col)
            )
        else:
            # 如果是字符串类型，转换为datetime
            df_with_time = df.with_columns(
                pl.col(time_col).str.to_datetime(strict=False).alias(time_col)
            )
        
        # 过滤掉时间列中的空值，group_by_dynamic不支持空值
        df_filtered = df_with_time.filter(pl.col(time_col).is_not_null())
        
        # 在过滤后检查剩余数据量
        if df_filtered.height == 0:
            logger.warning("时间列过滤后无有效数据")
            return df
            
        if df_filtered.height < 2:
            logger.warning("有效数据点过少，无法进行重采样")
            return df_filtered
        
        # 按时间列排序，group_by_dynamic要求数据按时间排序
        df_sorted = df_filtered.sort(time_col)
        
        # 获取除时间列外的所有数值列
        numeric_cols = [col for col in df_sorted.columns 
                       if col != time_col and df_sorted[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.Int16, pl.Int8]]
        
        if not numeric_cols:
            logger.warning("没有找到数值列进行重采样")
            return df_sorted
        
        # 根据聚合方法选择相应的polars表达式
        if agg_method == "mean":
            agg_exprs = [pl.col(col).mean().alias(col) for col in numeric_cols]
        elif agg_method == "max":
            agg_exprs = [pl.col(col).max().alias(col) for col in numeric_cols]
        elif agg_method == "min":
            agg_exprs = [pl.col(col).min().alias(col) for col in numeric_cols]
        elif agg_method == "sum":
            agg_exprs = [pl.col(col).sum().alias(col) for col in numeric_cols]
        else:
            # 默认使用mean
            agg_exprs = [pl.col(col).mean().alias(col) for col in numeric_cols]
        
        # 使用group_by_dynamic进行重采样
        # 注意：polars的频率格式与pandas略有不同
        # 将pandas格式转换为polars格式
        polars_freq = _convert_freq_to_polars(freq)
        
        result_df = df_sorted.group_by_dynamic(
            index_column=time_col,
            every=polars_freq,
            closed="left"  # 左闭右开区间，与pandas默认行为一致
        ).agg(agg_exprs)
        
        # 过滤掉空的时间窗口（所有值都是null的行）
        if numeric_cols:
            result_df = result_df.filter(
                pl.any_horizontal([pl.col(col).is_not_null() for col in numeric_cols])
            )
        
        # 如果重采样后数据为空，返回原始的过滤后数据
        if result_df.height == 0:
            logger.warning("重采样后数据为空，返回过滤后的原始数据")
            return df_filtered
        
        logger.info(f"重采样完成：从 {len(df)} 行降至 {len(result_df)} 行")
        return result_df
        
    except Exception as e:
        logger.warning(f"重采样失败: {e}，返回原始数据")
        return df


def _convert_freq_to_polars(pandas_freq: str) -> str:
    """将pandas频率格式转换为polars格式
    
    Args:
        pandas_freq: pandas风格的频率字符串 (如 '1h', '1d', '1w')
        
    Returns:
        str: polars风格的频率字符串
    """
    # polars和pandas的频率格式基本相同，但有一些细微差别
    freq_mapping = {
        'h': 'h',    # 小时
        'd': 'd',    # 天
        'w': 'w',    # 周
        'm': 'mo',   # 月份（polars使用'mo'而不是'm'）
        'y': 'y',    # 年
        's': 's',    # 秒
        'min': 'm',  # 分钟（polars使用'm'表示分钟）
        'ms': 'ms',  # 毫秒
        'us': 'us',  # 微秒
        'ns': 'ns'   # 纳秒
    }
    
    # 解析频率字符串
    import re
    match = re.match(r'(\d*)([a-zA-Z]+)', pandas_freq)
    if match:
        number, unit = match.groups()
        number = number or '1'  # 如果没有数字，默认为1
        
        # 转换单位
        polars_unit = freq_mapping.get(unit, unit)
        return f"{number}{polars_unit}"
    
    # 如果解析失败，返回原始字符串
    return pandas_freq


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
            # 数据质量检查
            valid_time_count = df[time_col].is_not_null().sum()
            valid_time_ratio = valid_time_count / original_size
            
            if valid_time_ratio < 0.5:
                logger.warning(f"时间列 '{time_col}' 有效数据比例过低: {valid_time_ratio:.2%}，跳过时间序列采样")
                # 降级到简单随机采样
                sampled_df = df.sample(n=target_size, seed=42)
                sampling_info.update({
                    "sampled_size": target_size,
                    "sampling_method": "random_fallback_low_quality",
                    "sampling_ratio": target_size / original_size,
                    "performance_gain": original_size / target_size
                })
                return sampled_df, sampling_info
            
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
                if len(resampled_df) > 0 and len(resampled_df) <= target_size:
                    sampling_info.update({
                        "sampled_size": len(resampled_df),
                        "sampling_method": f"time_resample_{freq}",
                        "sampling_ratio": len(resampled_df) / original_size,
                        "performance_gain": original_size / len(resampled_df)
                    })
                    logger.info(f"重采样成功：{original_size} -> {len(resampled_df)} 行")
                    return resampled_df, sampling_info
                elif len(resampled_df) == 0:
                    logger.warning("重采样结果为空，使用智能采样")
            
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
        # 检查时间列是否存在
        if time_col not in df.columns:
            logger.warning(f"时间列 '{time_col}' 不存在")
            return None
            
        # 检查时间列是否全部为空
        if df[time_col].is_null().all():
            logger.warning(f"时间列 '{time_col}' 全部为空")
            return None
            
        # 计算有效时间数据的比例
        valid_time_count = df[time_col].is_not_null().sum()
        valid_time_ratio = valid_time_count / len(df)
        if valid_time_ratio < 0.1:  # 如果有效时间数据少于10%
            logger.warning(f"时间列 '{time_col}' 有效数据比例过低: {valid_time_ratio:.2%}")
            return None
        
        # 确保时间列是datetime类型
        if df[time_col].dtype != pl.Datetime:
            df = df.with_columns(pl.col(time_col).cast(pl.Datetime))
        
        # 过滤掉空值后计算时间范围
        df_filtered = df.filter(pl.col(time_col).is_not_null())
        if df_filtered.height == 0:
            logger.warning("时间列过滤后无有效数据")
            return None
        
        # 使用polars表达式计算时间范围
        result = df_filtered.select([
            (pl.col(time_col).max() - pl.col(time_col).min()).dt.total_days().alias("days_diff")
        ])
        
        days_diff = result["days_diff"][0]
        if days_diff is not None and days_diff > 0:
            return float(days_diff)
        else:
            logger.warning(f"计算得到的时间范围无效: {days_diff}")
            return None
            
    except Exception as e:
        logger.warning(f"估算时间范围失败: {e}")
        return None