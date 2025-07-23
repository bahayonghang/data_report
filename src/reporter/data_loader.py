# 数据加载模块
"""
文件 I/O、CSV/Parquet 处理、路径验证

负责：
- 文件读取和数据预处理
- 时间列自动检测
- 数据类型转换和验证
"""

import polars as pl
import re
from typing import Optional, Dict, Any
from pathlib import Path


def load_data_file(file_path: str) -> pl.DataFrame:
    """
    加载 CSV 或 Parquet 文件

    Args:
        file_path: 文件路径

    Returns:
        pl.DataFrame: 加载的数据框

    Raises:
        ValueError: 不支持的文件格式
        FileNotFoundError: 文件不存在
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pl.read_csv(file_path)
    elif suffix == ".parquet":
        return pl.read_parquet(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")


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


def prepare_analysis_data(df: pl.DataFrame) -> Dict[str, Any]:
    """
    准备分析数据，分离时间列和数值列

    Args:
        df: 原始数据框

    Returns:
        Dict[str, Any]: 包含时间列、数值列等信息的字典
    """
    if df is None or df.is_empty():
        raise ValueError("数据框为空")

    time_column = detect_time_column(df)

    # 分离时间列和数值列
    if time_column:
        time_data = df[time_column]
        numeric_columns = [
            col
            for col in df.columns
            if col != time_column
            and df[col].dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]
        ]
    else:
        time_data = None
        numeric_columns = [
            col
            for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Int32, pl.Float64, pl.Float32]
        ]

    if not numeric_columns:
        raise ValueError("没有找到数值列进行分析")

    # 数据预处理：处理缺失值
    processed_df = df.clone()

    # 转换时间列为 datetime 类型
    if time_column and time_data is not None:
        if processed_df[time_column].dtype == pl.Utf8:
            try:
                processed_df = processed_df.with_columns(
                    pl.col(time_column)
                    .str.strptime(pl.Datetime, format="%Y-%m-%d %H:%M:%S", strict=False)
                    .alias(time_column)
                )
            except:
                try:
                    processed_df = processed_df.with_columns(
                        pl.col(time_column)
                        .str.strptime(pl.Datetime, format="%Y-%m-%d", strict=False)
                        .alias(time_column)
                    )
                except:
                    pass

    # 按时间排序（如果有时序列）
    if time_column and time_data is not None:
        processed_df = processed_df.sort(time_column)

    return {
        "original_df": df,
        "processed_df": processed_df,
        "time_column": time_column,
        "numeric_columns": numeric_columns,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": {col: df[col].null_count() for col in df.columns},
    }
