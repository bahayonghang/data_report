import polars as pl
from typing import List, Dict, Any, Iterator, Optional, Tuple
import math
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ChunkInfo:
    """数据块信息"""
    chunk_id: int
    start_row: int
    end_row: int
    row_count: int
    memory_estimate: float  # MB
    time_column: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None

class DataChunkProcessor:
    """数据分块处理器
    
    负责将大数据集分割成可管理的块，支持：
    - 基于内存限制的智能分块
    - 时间序列数据的时间窗口分块
    - 重叠窗口处理
    - 自适应块大小调整
    """
    
    def __init__(self, 
                 max_chunk_memory_mb: float = 500,  # 每块最大内存限制
                 min_chunk_rows: int = 1000,        # 最小行数
                 max_chunk_rows: int = 1000000,     # 最大行数
                 overlap_ratio: float = 0.1):       # 重叠比例
        self.max_chunk_memory_mb = max_chunk_memory_mb
        self.min_chunk_rows = min_chunk_rows
        self.max_chunk_rows = max_chunk_rows
        self.overlap_ratio = overlap_ratio
        
    def estimate_memory_usage(self, df: pl.DataFrame) -> float:
        """估算DataFrame的内存使用量（MB）
        
        Args:
            df: Polars DataFrame
            
        Returns:
            估算的内存使用量（MB）
        """
        try:
            # 获取DataFrame的估算大小
            estimated_size = df.estimated_size()
            return estimated_size / (1024 * 1024)  # 转换为MB
        except Exception:
            # 如果无法获取估算大小，使用简单计算
            bytes_per_row = sum([
                8 if dtype in [pl.Float64, pl.Int64, pl.Datetime] else
                4 if dtype in [pl.Float32, pl.Int32] else
                1 if dtype == pl.Boolean else
                50  # 字符串类型的平均估算
                for dtype in df.dtypes
            ])
            return (len(df) * bytes_per_row) / (1024 * 1024)
    
    def calculate_optimal_chunk_size(self, df: pl.DataFrame) -> int:
        """计算最优的块大小
        
        Args:
            df: 数据框
            
        Returns:
            最优的块大小（行数）
        """
        total_rows = len(df)
        if total_rows == 0:
            return self.min_chunk_rows
        
        # 估算单行内存使用量
        sample_size = min(1000, total_rows)
        sample_df = df.head(sample_size)
        sample_memory = self.estimate_memory_usage(sample_df)
        memory_per_row = sample_memory / sample_size
        
        # 基于内存限制计算块大小
        rows_per_chunk = int(self.max_chunk_memory_mb / memory_per_row)
        
        # 应用最小和最大限制
        rows_per_chunk = max(self.min_chunk_rows, 
                           min(self.max_chunk_rows, rows_per_chunk))
        
        logger.info(f"计算得出最优块大小: {rows_per_chunk} 行 "
                   f"(估算内存: {rows_per_chunk * memory_per_row:.2f} MB)")
        
        return rows_per_chunk
    
    def create_row_based_chunks(self, df: pl.DataFrame) -> List[ChunkInfo]:
        """基于行数创建数据块
        
        Args:
            df: 数据框
            
        Returns:
            数据块信息列表
        """
        total_rows = len(df)
        if total_rows == 0:
            return []
        
        chunk_size = self.calculate_optimal_chunk_size(df)
        chunks = []
        
        for i in range(0, total_rows, chunk_size):
            start_row = i
            end_row = min(i + chunk_size, total_rows)
            
            # 估算这个块的内存使用量
            chunk_df = df.slice(start_row, end_row - start_row)
            memory_estimate = self.estimate_memory_usage(chunk_df)
            
            chunk_info = ChunkInfo(
                chunk_id=len(chunks),
                start_row=start_row,
                end_row=end_row,
                row_count=end_row - start_row,
                memory_estimate=memory_estimate
            )
            chunks.append(chunk_info)
        
        logger.info(f"创建了 {len(chunks)} 个基于行数的数据块")
        return chunks
    
    def create_time_based_chunks(self, df: pl.DataFrame, 
                               time_column: str,
                               time_window: str = "1d") -> List[ChunkInfo]:
        """基于时间窗口创建数据块
        
        Args:
            df: 数据框
            time_column: 时间列名
            time_window: 时间窗口大小 (如 "1d", "1h", "1w")
            
        Returns:
            数据块信息列表
        """
        if time_column not in df.columns:
            logger.warning(f"时间列 '{time_column}' 不存在，回退到基于行数的分块")
            return self.create_row_based_chunks(df)
        
        try:
            import polars as pl
            # 确保时间列是datetime类型
            if df[time_column].dtype != pl.Datetime:
                df = df.with_columns(pl.col(time_column).str.to_datetime())
            
            # 获取时间范围
            time_min = df[time_column].min()
            time_max = df[time_column].max()
            
            if time_min is None or time_max is None:
                logger.warning("无法获取时间范围，回退到基于行数的分块")
                return self.create_row_based_chunks(df)
            
            # 按时间排序
            df_sorted = df.sort(time_column)
            
            # 简化的时间分块：基于时间列排序后按行数分块
            # 这样可以保持时间的连续性，同时避免复杂的时间窗口计算
            chunks = self.create_row_based_chunks(df_sorted)
            
            # 为每个块添加时间范围信息
            for chunk in chunks:
                try:
                    chunk_df = df_sorted.slice(chunk.start_row, chunk.row_count)
                    if len(chunk_df) > 0:
                        chunk_time_min = chunk_df[time_column].min()
                        chunk_time_max = chunk_df[time_column].max()
                        
                        # 使用polars转换为Python datetime对象
                        if chunk_time_min is not None and chunk_time_max is not None:
                            try:
                                import polars as pl
                                
                                # 将polars时间值转换为Python datetime对象
                                # 如果是字符串，先转换为datetime类型
                                if isinstance(chunk_time_min, str):
                                    time_start_pl = pl.Series([chunk_time_min]).str.to_datetime().item()
                                else:
                                    time_start_pl = chunk_time_min
                                    
                                if isinstance(chunk_time_max, str):
                                    time_end_pl = pl.Series([chunk_time_max]).str.to_datetime().item()
                                else:
                                    time_end_pl = chunk_time_max
                                
                                # 转换为Python datetime对象
                                if hasattr(time_start_pl, 'to_pydatetime'):
                                    time_start = time_start_pl.to_pydatetime()
                                else:
                                    time_start = time_start_pl
                                    
                                if hasattr(time_end_pl, 'to_pydatetime'):
                                    time_end = time_end_pl.to_pydatetime()
                                else:
                                    time_end = time_end_pl
                                
                                chunk.time_column = time_column
                                chunk.time_range = (time_start, time_end)
                            except Exception:
                                # 如果转换失败，保持原有信息
                                chunk.time_column = time_column
                except Exception as e:
                    logger.warning(f"为块 {chunk.chunk_id} 添加时间信息时出错: {e}")
            
            logger.info(f"创建了 {len(chunks)} 个基于时间的数据块")
            return chunks
            
        except Exception as e:
            logger.error(f"创建时间分块时出错: {e}，回退到基于行数的分块")
            return self.create_row_based_chunks(df)
    
    def create_adaptive_chunks(self, df: pl.DataFrame, 
                             time_column: Optional[str] = None) -> List[ChunkInfo]:
        """自适应创建数据块
        
        根据数据特征自动选择最佳的分块策略
        
        Args:
            df: 数据框
            time_column: 可选的时间列名
            
        Returns:
            数据块信息列表
        """
        total_rows = len(df)
        total_memory = self.estimate_memory_usage(df)
        
        logger.info(f"数据集信息: {total_rows} 行, 估算内存: {total_memory:.2f} MB")
        
        # 如果数据集很小，不需要分块
        if total_memory <= self.max_chunk_memory_mb:
            logger.info("数据集较小，不需要分块")
            return [ChunkInfo(
                chunk_id=0,
                start_row=0,
                end_row=total_rows,
                row_count=total_rows,
                memory_estimate=total_memory
            )]
        
        # 如果有时间列且数据量大，优先使用时间分块
        if time_column and time_column in df.columns and total_rows > 100000:
            logger.info(f"使用时间分块策略，时间列: {time_column}")
            
            # 根据数据量选择时间窗口
            if total_rows > 10000000:  # 1000万行以上
                time_window = "1d"
            elif total_rows > 1000000:  # 100万行以上
                time_window = "1w"
            else:
                time_window = "1M"  # 1个月
            
            chunks = self.create_time_based_chunks(df, time_column, time_window)
            
            # 如果时间分块产生的块太大，进一步细分
            refined_chunks = []
            for chunk in chunks:
                if chunk.memory_estimate > self.max_chunk_memory_mb * 1.5:
                    # 这个块太大，需要进一步分割
                    chunk_df = df.slice(chunk.start_row, chunk.row_count)
                    sub_chunks = self.create_row_based_chunks(chunk_df)
                    
                    # 调整子块的行号
                    for i, sub_chunk in enumerate(sub_chunks):
                        sub_chunk.chunk_id = len(refined_chunks)
                        sub_chunk.start_row += chunk.start_row
                        sub_chunk.end_row += chunk.start_row
                        refined_chunks.append(sub_chunk)
                else:
                    refined_chunks.append(chunk)
            
            return refined_chunks
        
        # 默认使用基于行数的分块
        logger.info("使用基于行数的分块策略")
        return self.create_row_based_chunks(df)
    
    def get_chunk_data(self, df: pl.DataFrame, chunk_info: ChunkInfo, 
                      with_overlap: bool = False) -> pl.DataFrame:
        """获取指定块的数据
        
        Args:
            df: 原始数据框
            chunk_info: 块信息
            with_overlap: 是否包含重叠数据
            
        Returns:
            块数据
        """
        start_row = chunk_info.start_row
        end_row = chunk_info.end_row
        
        if with_overlap and self.overlap_ratio > 0:
            # 计算重叠行数
            overlap_rows = int(chunk_info.row_count * self.overlap_ratio)
            
            # 向前扩展
            start_row = max(0, start_row - overlap_rows)
            # 向后扩展
            end_row = min(len(df), end_row + overlap_rows)
        
        return df.slice(start_row, end_row - start_row)
    
    def get_chunk_iterator(self, df: pl.DataFrame, 
                          chunks: List[ChunkInfo],
                          with_overlap: bool = False) -> Iterator[Tuple[ChunkInfo, pl.DataFrame]]:
        """获取块数据迭代器
        
        Args:
            df: 原始数据框
            chunks: 块信息列表
            with_overlap: 是否包含重叠数据
            
        Yields:
            (块信息, 块数据) 元组
        """
        for chunk_info in chunks:
            chunk_data = self.get_chunk_data(df, chunk_info, with_overlap)
            yield chunk_info, chunk_data
    
    def merge_chunk_results(self, chunk_results: List[Dict[str, Any]], 
                          result_type: str = "stats") -> Dict[str, Any]:
        """合并多个块的处理结果
        
        Args:
            chunk_results: 块处理结果列表
            result_type: 结果类型 ("stats", "correlation", "time_series")
            
        Returns:
            合并后的结果
        """
        if not chunk_results:
            return {}
        
        if result_type == "stats":
            return self._merge_stats_results(chunk_results)
        elif result_type == "correlation":
            return self._merge_correlation_results(chunk_results)
        elif result_type == "time_series":
            return self._merge_time_series_results(chunk_results)
        else:
            # 默认合并策略：简单合并字典
            merged = {}
            for result in chunk_results:
                merged.update(result)
            return merged
    
    def _merge_stats_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并统计结果"""
        if not chunk_results:
            return {}
        
        # 初始化合并结果
        merged = {
            "total_rows": 0,
            "columns": {},
            "missing_values": {},
            "data_types": chunk_results[0].get("data_types", {})
        }
        
        # 合并每个块的结果
        for result in chunk_results:
            merged["total_rows"] += result.get("total_rows", 0)
            
            # 合并列统计
            for col, stats in result.get("columns", {}).items():
                if col not in merged["columns"]:
                    merged["columns"][col] = {
                        "count": 0,
                        "sum": 0,
                        "sum_sq": 0,
                        "min": float('inf'),
                        "max": float('-inf')
                    }
                
                col_merged = merged["columns"][col]
                col_merged["count"] += stats.get("count", 0)
                col_merged["sum"] += stats.get("sum", 0)
                col_merged["sum_sq"] += stats.get("sum_sq", 0)
                col_merged["min"] = min(col_merged["min"], stats.get("min", float('inf')))
                col_merged["max"] = max(col_merged["max"], stats.get("max", float('-inf')))
            
            # 合并缺失值统计
            for col, missing_count in result.get("missing_values", {}).items():
                merged["missing_values"][col] = merged["missing_values"].get(col, 0) + missing_count
        
        # 计算最终统计值
        for col, stats in merged["columns"].items():
            if stats["count"] > 0:
                stats["mean"] = stats["sum"] / stats["count"]
                if stats["count"] > 1:
                    variance = (stats["sum_sq"] - stats["sum"]**2 / stats["count"]) / (stats["count"] - 1)
                    stats["std"] = math.sqrt(max(0, variance))
                else:
                    stats["std"] = 0
        
        return merged
    
    def _merge_correlation_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并相关性分析结果"""
        # 相关性分析需要重新计算，这里返回第一个有效结果
        # 在实际实现中，应该收集所有数据重新计算相关系数
        for result in chunk_results:
            if result.get("correlation_matrix"):
                return result
        return {}
    
    def _merge_time_series_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并时间序列分析结果"""
        merged = {
            "time_series_data": [],
            "trends": {},
            "seasonality": {}
        }
        
        # 合并时间序列数据
        for result in chunk_results:
            if "time_series_data" in result:
                merged["time_series_data"].extend(result["time_series_data"])
        
        # 按时间排序
        if merged["time_series_data"]:
            merged["time_series_data"].sort(key=lambda x: x.get("timestamp", ""))
        
        return merged