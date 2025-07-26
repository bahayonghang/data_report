import polars as pl
from typing import Dict, Any, List
from datetime import datetime
import logging

from .task_manager import TaskInfo, task_manager
from .chunk_processor import DataChunkProcessor, ChunkInfo

# 导入现有的分析模块和管理器
try:
    from ..analysis.basic_stats import calculate_descriptive_stats
except ImportError:
    def calculate_descriptive_stats(df, columns):
        return {}

try:
    from ..analysis.correlation import calculate_correlation_matrix
except ImportError:
    def calculate_correlation_matrix(df: pl.DataFrame) -> pl.DataFrame:
        return pl.DataFrame()

try:
    from ..analysis.time_series import analyze_time_series
except ImportError:
    def analyze_time_series(df: pl.DataFrame, time_column: str, value_column: str) -> Dict[str, Any]:
        return {}

from ..memory_manager import MemoryManager
# 创建占位符FileManager
class FileManager:
    def save_analysis_result(self, result, task_id):
        return f"result_{task_id}.json"

logger = logging.getLogger(__name__)

class AnalysisTaskProcessor:
    """分析任务处理器
    
    负责执行具体的数据分析任务，包括：
    - 分块数据处理
    - 进度跟踪
    - 结果合并和存储
    - 错误处理和恢复
    """
    
    def __init__(self):
        self.chunk_processor = DataChunkProcessor()
        self.memory_manager = MemoryManager()
        self.file_manager = FileManager()
        
        # 注册任务处理器
        task_manager.register_handler("full_analysis", self.handle_full_analysis)
        task_manager.register_handler("basic_stats", self.handle_basic_stats)
        task_manager.register_handler("correlation", self.handle_correlation)
        task_manager.register_handler("time_series", self.handle_time_series)
    
    async def handle_full_analysis(self, task_info: TaskInfo, 
                                 df: pl.DataFrame, 
                                 **kwargs) -> Dict[str, Any]:
        """处理完整数据分析任务"""
        try:
            logger.info(f"开始完整分析任务: {task_info.task_id}")
            
            # 1. 数据预处理和分块
            await task_manager.update_progress(
                task_info.task_id, 5, "正在准备数据分块...", 1
            )
            
            time_column = kwargs.get("time_column")
            chunks = self.chunk_processor.create_adaptive_chunks(
                df, time_column=time_column
            )
            
            await task_manager.update_progress(
                task_info.task_id, 15, f"数据分块完成，共{len(chunks)}个块", 2
            )
            
            # 2. 基础统计分析
            stats_results = await self._process_chunks_parallel(
                df, chunks, "basic_stats", task_info.task_id, 25, 45
            )
            merged_stats = self.chunk_processor.merge_chunk_results(stats_results, "stats")
            
            await task_manager.update_progress(
                task_info.task_id, 50, "基础统计完成，开始相关性分析...", 3
            )
            
            # 3. 相关性分析（使用采样数据以提高性能）
            correlation_result = await self._analyze_correlation(
                df, task_info.task_id, 50, 70
            )
            
            await task_manager.update_progress(
                task_info.task_id, 75, "相关性分析完成，开始时间序列分析...", 4
            )
            
            # 4. 时间序列分析
            time_series_result = {}
            if time_column and time_column in df.columns:
                time_series_results = await self._process_chunks_parallel(
                    df, chunks, "time_series", task_info.task_id, 75, 90,
                    time_column=time_column
                )
                time_series_result = self.chunk_processor.merge_chunk_results(
                    time_series_results, "time_series"
                )
            
            await task_manager.update_progress(
                task_info.task_id, 90, "分析完成，正在保存结果...", 5
            )
            
            # 5. 合并和保存结果
            final_result = {
                "basic_stats": merged_stats,
                "correlation": correlation_result,
                "time_series": time_series_result,
                "metadata": {
                    "total_chunks": len(chunks),
                    "processing_time": datetime.now().isoformat(),
                    "data_shape": {"rows": len(df), "columns": len(df.columns)}
                }
            }
            
            # 保存结果
            self.file_manager.save_analysis_result(
                final_result, task_info.task_id
            )
            
            await task_manager.update_progress(
                task_info.task_id, 100, "分析任务完成", 6
            )
            
            logger.info(f"完整分析任务完成: {task_info.task_id}")
            return final_result
            
        except Exception as e:
            logger.error(f"完整分析任务失败: {e}")
            await task_manager.update_progress(
                task_info.task_id, -1, f"分析失败: {str(e)}"
            )
            raise
        
        finally:
            # 清理内存
            try:
                self.memory_manager.force_garbage_collection()
            except AttributeError:
                pass
    
    async def handle_basic_stats(self, task_info: TaskInfo, 
                               df: pl.DataFrame, 
                               **kwargs) -> Dict[str, Any]:
        """处理基础统计分析任务"""
        try:
            logger.info(f"开始基础统计分析: {task_info.task_id}")
            
            # 获取数值列
            numeric_columns = [col for col in df.columns 
                             if df[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]]
            
            if not numeric_columns:
                return {"error": "没有找到数值列"}
            
            # 计算统计量
            stats_result = calculate_descriptive_stats(df, numeric_columns)
            
            await task_manager.update_progress(
                task_info.task_id, 100, "基础统计分析完成"
            )
            
            return {"basic_stats": stats_result}
            
        except Exception as e:
            logger.error(f"基础统计分析失败: {e}")
            raise
    
    async def handle_correlation(self, task_info: TaskInfo, 
                               df: pl.DataFrame, 
                               **kwargs) -> Dict[str, Any]:
        """处理相关性分析任务"""
        try:
            logger.info(f"开始相关性分析: {task_info.task_id}")
            
            # 对大数据集进行采样
            if len(df) > 50000:
                df_sample = df.sample(50000, seed=42)
                logger.info("使用采样数据进行相关性分析")
            else:
                df_sample = df
            
            corr_matrix = calculate_correlation_matrix(df_sample)
            correlation_result = {"correlation_matrix": corr_matrix.to_dict() if hasattr(corr_matrix, 'to_dict') else {}}
            
            await task_manager.update_progress(
                task_info.task_id, 100, "相关性分析完成"
            )
            
            return {"correlation": correlation_result}
            
        except Exception as e:
            logger.error(f"相关性分析失败: {e}")
            raise
    
    async def handle_time_series(self, task_info: TaskInfo, 
                               df: pl.DataFrame, 
                               **kwargs) -> Dict[str, Any]:
        """处理时间序列分析任务"""
        try:
            logger.info(f"开始时间序列分析: {task_info.task_id}")
            
            time_column = kwargs.get("time_column")
            if not time_column or time_column not in df.columns:
                return {"error": "未指定有效的时间列"}
            
            # 执行时间序列分析
            value_column = kwargs.get("value_column", df.columns[0] if df.columns else "")
            ts_result = analyze_time_series(df, time_column, value_column)
            
            await task_manager.update_progress(
                task_info.task_id, 100, "时间序列分析完成"
            )
            
            return {"time_series": ts_result}
            
        except Exception as e:
            logger.error(f"时间序列分析失败: {e}")
            raise
    
    async def _process_chunks_parallel(self, df: pl.DataFrame, 
                                     chunks: List[ChunkInfo],
                                     analysis_type: str,
                                     task_id: str,
                                     start_progress: float,
                                     end_progress: float,
                                     **analysis_kwargs) -> List[Dict[str, Any]]:
        """并行处理数据块"""
        results = []
        total_chunks = len(chunks)
        progress_range = end_progress - start_progress
        
        # 处理每个数据块
        for i, chunk_info in enumerate(chunks):
            try:
                # 获取数据块
                chunk_data = self.chunk_processor.get_chunk_data(df, chunk_info)
                
                # 执行分析
                if analysis_type == "basic_stats":
                    result = calculate_descriptive_stats(chunk_data, chunk_data.columns)
                elif analysis_type == "correlation":
                    corr_matrix = calculate_correlation_matrix(chunk_data)
                    result = {"correlation_matrix": corr_matrix.to_dict() if hasattr(corr_matrix, 'to_dict') else {}}
                elif analysis_type == "time_series":
                    time_column = analysis_kwargs.get("time_column")
                    if not time_column:
                        result = {"error": "未指定时间列"}
                    else:
                        value_column = analysis_kwargs.get("value_column", chunk_data.columns[0] if chunk_data.columns else "")
                        result = analyze_time_series(chunk_data, time_column, value_column)
                else:
                    raise ValueError(f"不支持的分析类型: {analysis_type}")
                
                results.append(result)
                
                # 更新进度
                progress = start_progress + (i + 1) / total_chunks * progress_range
                await task_manager.update_progress(
                    task_id, progress, f"处理数据块 {i+1}/{total_chunks}"
                )
                
                # 内存管理
                if i % 5 == 0:  # 每处理5个块清理一次内存
                    try:
                        self.memory_manager.force_garbage_collection()
                    except AttributeError:
                        pass
                
            except Exception as e:
                logger.error(f"处理数据块 {i} 失败: {e}")
                results.append({"error": str(e)})
        
        return results
    
    async def _analyze_correlation(self, df: pl.DataFrame, 
                                 task_id: str,
                                 start_progress: float,
                                 end_progress: float) -> Dict[str, Any]:
        """分析相关性（使用采样以提高性能）"""
        try:
            # 对于大数据集，使用采样来计算相关性
            if len(df) > 100000:
                sample_size = min(50000, len(df))
                df_sample = df.sample(sample_size, seed=42)
                logger.info(f"使用采样数据计算相关性，样本大小: {sample_size}")
            else:
                df_sample = df
            
            await task_manager.update_progress(
                task_id, (start_progress + end_progress) / 2, 
                "正在计算相关系数矩阵..."
            )
            
            corr_matrix = calculate_correlation_matrix(df_sample)
            result = {"correlation_matrix": corr_matrix.to_dict() if hasattr(corr_matrix, 'to_dict') else {}}
            
            return result
            
        except Exception as e:
            logger.error(f"相关性分析失败: {e}")
            return {}

# 创建全局实例
analysis_processor = AnalysisTaskProcessor()