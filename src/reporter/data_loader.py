# 数据加载模块
"""
文件 I/O、CSV/Parquet 处理、路径验证

负责：
- 文件读取和数据预处理
- 时间列自动检测
- 数据类型转换和验证
- 大数据集内存优化
"""

import polars as pl
import re
from typing import Optional, Dict, Any
from pathlib import Path
import logging


def load_data_file(file_path: str, max_rows: int = 1000000) -> pl.DataFrame:
    """
    加载 CSV 或 Parquet 文件，支持大数据集优化

    Args:
        file_path: 文件路径
        max_rows: 最大行数限制（默认100万行）

    Returns:
        pl.DataFrame: 加载的数据框

    Raises:
        ValueError: 不支持的文件格式或数据过大
        FileNotFoundError: 文件不存在
    """
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_size = file_path_obj.stat().st_size
    
    # 大文件警告
    if file_size > 1024 * 1024 * 1024:  # 1GB
        logging.warning(f"处理大文件: {file_size / 1024 / 1024:.1f}MB")

    suffix = file_path_obj.suffix.lower()

    try:
        if suffix == ".csv":
            # 使用流式读取处理大文件
            return pl.read_csv(
                file_path,
                low_memory=True,
                n_rows=max_rows if file_size > 50 * 1024 * 1024 else None,  # 50MB以上限制行数
                ignore_errors=True,
                try_parse_dates=True
            )
        elif suffix == ".parquet":
            # Parquet文件通常更高效，使用内存映射
            return pl.read_parquet(
                file_path,
                use_pyarrow=True,
                memory_map=True,
                n_rows=max_rows if file_size > 1024 * 1024 * 1024 else None  # 1GB以上限制行数
            )
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
    
    except Exception as e:
        logging.error(f"文件加载失败 {file_path}: {str(e)}")
        raise ValueError(f"文件加载失败: {str(e)}")


def detect_time_column(df: pl.DataFrame) -> Optional[str]:
    """
    自动检测时间列

    检测逻辑：
    1. 检查列名是否匹配 DateTime|tagTime|timestamp|time 模式
    2. 检查第一列数据类型是否为 datetime
    3. 尝试解析字符串列为日期时间格式

    Args:
        df: 数据框

    Returns:
        Optional[str]: 检测到的时间列名或 None
    """
    if df is None or df.is_empty():
        return None

    # 时间列名称模式
    time_patterns = [
        r"datetime",
        r"date",
        r"time",
        r"timestamp",
        r"tagtime",
        r"日期",
        r"时间",
        r"年月日",
        r"年月",
        r"年月日时分秒",
    ]

    # 检查列名匹配
    for col in df.columns:
        col_lower = col.lower()
        for pattern in time_patterns:
            if re.search(pattern, col_lower):
                return col

    # 检查数据类型
    for col in df.columns:
        dtype = df[col].dtype
        if str(dtype).startswith("datetime") or str(dtype) == "date":
            return col

    # 检查是否可以解析为日期时间
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            try:
                # 尝试解析第一行
                sample_value = df[col].drop_nulls().head(1)[0]
                if sample_value:
                    # 检查是否是标准日期时间格式
                    date_patterns = [
                        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
                        r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",  # YYYY-MM-DD HH:MM:SS
                    ]
                    for pattern in date_patterns:
                        if re.search(pattern, str(sample_value)):
                            return col
            except (IndexError, ValueError):
                continue

    return None


def prepare_analysis_data(df: pl.DataFrame, sample_size: int = 100000) -> Dict[str, Any]:
    """
    准备分析数据，分离时间列和数值列，支持大数据集优化（增强版本）

    Args:
        df: 原始数据框
        sample_size: 大数据集采样大小（默认10万行）

    Returns:
        Dict[str, Any]: 包含时间列、数值列等信息的字典
    """
    if df is None or df.is_empty():
        raise ValueError("数据框为空")

    total_rows = len(df)
    warnings_list = []
    
    # 大数据集采样
    if total_rows > sample_size:
        logging.info(f"大数据集采样: {total_rows} -> {sample_size} 行")
        warnings_list.append(f"数据集过大，已采样至 {sample_size} 行进行分析")
        df = df.sample(sample_size, seed=42)

    time_column = detect_time_column(df)

    # 优化：使用select快速过滤数值列
    if time_column:
        numeric_columns = [
            col for col in df.columns
            if col != time_column and df[col].dtype in (pl.Int64, pl.Int32, pl.Float64, pl.Float32)
        ]
    else:
        numeric_columns = [
            col for col in df.columns
            if df[col].dtype in (pl.Int64, pl.Int32, pl.Float64, pl.Float32)
        ]

    if not numeric_columns:
        raise ValueError("没有找到数值列进行分析")

    # 预处理：检查并移除常数列（零方差列）
    import numpy as np
    valid_numeric_columns = []
    constant_columns = []
    
    for col in numeric_columns:
        col_data = df[col].drop_nulls()
        if len(col_data) > 0:
            values = col_data.to_numpy()
            col_std = np.std(values, ddof=1)
            if col_std < 1e-10:  # 接近零的阈值
                constant_columns.append(col)
                warnings_list.append(f"列 '{col}' 为常数列，已从数值分析中排除")
            else:
                valid_numeric_columns.append(col)
        else:
            warnings_list.append(f"列 '{col}' 全为缺失值，已从数值分析中排除")
    
    # 更新数值列列表
    numeric_columns = valid_numeric_columns
    
    if not numeric_columns:
        raise ValueError("没有找到有效的数值列进行分析（所有数值列都是常数列或全为缺失值）")

    # 数据预处理优化：使用lazy evaluation
    processed_df = df.lazy()

    # 转换时间列为 datetime 类型（修复版本）
    if time_column:
        col_dtype = df[time_column].dtype
        if col_dtype == pl.Utf8:
            try:
                # 逐个尝试不同格式，而不是链式调用
                time_formats = [
                    "%Y-%m-%d %H:%M:%S%.f",
                    "%Y-%m-%d %H:%M:%S", 
                    "%Y-%m-%d",
                    "%Y/%m/%d %H:%M:%S",
                    "%Y/%m/%d",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y",
                    "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y"
                ]
                
                converted_col = None
                for fmt in time_formats:
                    try:
                        # 尝试当前格式
                        test_conversion = processed_df.with_columns(
                            pl.col(time_column).str.strptime(pl.Datetime, format=fmt, strict=False)
                        ).collect()
                        
                        # 检查转换结果是否有效（非全部为null）
                        non_null_count = test_conversion[time_column].drop_nulls().len()
                        if non_null_count > 0:
                            logging.info(f"时间列 '{time_column}' 使用格式 '{fmt}' 成功转换，有效值: {non_null_count}")
                            processed_df = processed_df.with_columns(
                                pl.col(time_column).str.strptime(pl.Datetime, format=fmt, strict=False)
                            )
                            converted_col = time_column
                            break
                    except Exception:
                        continue
                
                if converted_col is None:
                    warnings_list.append(f"时间列 '{time_column}' 无法转换为日期时间格式，将作为普通列处理")
                    time_column = None
                    
            except Exception as e:
                warnings_list.append(f"时间列 '{time_column}' 转换失败: {str(e)}")
                time_column = None
        elif str(col_dtype).startswith("datetime"):
            pass  # 已经是datetime类型

    # 收集结果
    try:
        processed_df = processed_df.collect()
    except Exception as e:
        logging.error(f"数据处理失败: {str(e)}")
        # 回退到原始数据框
        processed_df = df
        warnings_list.append(f"数据预处理失败，使用原始数据: {str(e)}")

    # 按时间排序（如果有时序列）
    if time_column and time_column in processed_df.columns:
        try:
            processed_df = processed_df.sort(time_column)
        except Exception as e:
            warnings_list.append(f"时间排序失败: {str(e)}")

    # 优化：批量计算缺失值
    missing_values = {}
    for col in df.columns:
        null_count = df[col].null_count()
        missing_values[col] = {
            "missing_count": null_count,
            "missing_ratio": null_count / total_rows if total_rows > 0 else 0
        }

    # 内存优化：释放不需要的数据
    sampled_rows = len(df)
    
    return {
        "original_df": df,
        "processed_df": processed_df,
        "time_column": time_column,
        "numeric_columns": numeric_columns,
        "constant_columns": constant_columns,
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "sampled_rows": sampled_rows,
        "missing_values": missing_values,
        "warnings": warnings_list,
        "data_quality": {
            "valid_numeric_columns": len(numeric_columns),
            "constant_columns_count": len(constant_columns),
            "has_time_column": time_column is not None,
            "missing_data_ratio": sum(info["missing_count"] for info in missing_values.values()) / (total_rows * len(df.columns)) if total_rows > 0 else 0
        }
    }
