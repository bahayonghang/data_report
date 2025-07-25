# 并行处理核心模块
# 负责数据分析任务的并行化处理和性能优化

import asyncio
import concurrent.futures
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
import polars as pl
from functools import partial
import os
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)

# 并行处理配置
MAX_WORKERS = 4  # 最大工作线程数
CHUNK_SIZE = 10000  # 数据块大小
MEMORY_THRESHOLD = 0.8  # 内存使用阈值


@dataclass
class TaskResult:
    """任务结果数据类"""
    task_name: str
    result: Any
    execution_time: float
    success: bool
    error: Optional[str] = None


class ParallelProcessor:
    """并行处理器类"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化并行处理器
        
        Args:
            max_workers: 最大工作线程数，默认为CPU核心数
        """
        self.max_workers = max_workers or min(MAX_WORKERS, (os.cpu_count() or 1) + 4)
        self.executor = None
        self.results = {}
        self.start_time = None
        
        logger.info(f"并行处理器初始化完成，最大工作线程数: {self.max_workers}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        total_time = time.time() - self.start_time if self.start_time else 0
        logger.info(f"并行处理完成，总耗时: {total_time:.2f}秒")
    
    def submit_task(self, task_name: str, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交并行任务
        
        Args:
            task_name: 任务名称
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            Future对象
        """
        if not self.executor:
            raise RuntimeError("并行处理器未初始化")
        
        logger.info(f"提交任务: {task_name}")
        
        # 包装函数以记录执行时间和错误处理
        def wrapped_func(*args, **kwargs):
            task_start = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - task_start
                logger.info(f"任务 '{task_name}' 完成，耗时: {execution_time:.2f}秒")
                return TaskResult(
                    task_name=task_name,
                    result=result,
                    execution_time=execution_time,
                    success=True
                )
            except Exception as e:
                execution_time = time.time() - task_start
                logger.error(f"任务 '{task_name}' 失败: {e}，耗时: {execution_time:.2f}秒")
                return TaskResult(
                    task_name=task_name,
                    result=None,
                    execution_time=execution_time,
                    success=False,
                    error=str(e)
                )
        
        return self.executor.submit(wrapped_func, *args, **kwargs)
    
    def wait_for_tasks(self, futures: List[concurrent.futures.Future], timeout: Optional[float] = None) -> Dict[str, TaskResult]:
        """
        等待任务完成
        
        Args:
            futures: Future对象列表
            timeout: 超时时间（秒）
            
        Returns:
            任务结果字典
        """
        results = {}
        
        try:
            # 等待所有任务完成
            completed_futures = concurrent.futures.as_completed(futures, timeout=timeout)
            
            for future in completed_futures:
                try:
                    task_result = future.result()
                    results[task_result.task_name] = task_result
                except Exception as e:
                    logger.error(f"获取任务结果失败: {e}")
                    
        except concurrent.futures.TimeoutError:
            logger.warning(f"任务执行超时 ({timeout}秒)")
            # 取消未完成的任务
            for future in futures:
                if not future.done():
                    future.cancel()
        
        return results


class AsyncVisualizationProcessor:
    """异步可视化处理器"""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(2)  # 限制并发可视化任务数
    
    async def create_visualization_async(self, viz_func: Callable, *args, **kwargs) -> Dict:
        """
        异步创建可视化图表
        
        Args:
            viz_func: 可视化函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            可视化结果
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            
            # 在线程池中执行可视化函数
            try:
                result = await loop.run_in_executor(
                    None, 
                    partial(viz_func, *args, **kwargs)
                )
                return result
            except Exception as e:
                logger.error(f"异步可视化创建失败: {e}")
                return {"error": str(e)}
    
    async def create_multiple_visualizations(self, viz_tasks: List[Tuple[str, Callable, tuple, dict]]) -> Dict[str, Dict]:
        """
        并行创建多个可视化图表
        
        Args:
            viz_tasks: 可视化任务列表，每个元素为 (名称, 函数, 参数, 关键字参数)
            
        Returns:
            可视化结果字典
        """
        tasks = []
        
        for task_name, viz_func, args, kwargs in viz_tasks:
            task = asyncio.create_task(
                self.create_visualization_async(viz_func, *args, **kwargs),
                name=task_name
            )
            tasks.append((task_name, task))
        
        results = {}
        
        # 等待所有任务完成
        for task_name, task in tasks:
            try:
                result = await task
                results[task_name] = result
                logger.info(f"可视化任务 '{task_name}' 完成")
            except Exception as e:
                logger.error(f"可视化任务 '{task_name}' 失败: {e}")
                results[task_name] = {"error": str(e)}
        
        return results


def optimize_dataframe_processing(df: pl.DataFrame, chunk_size: int = CHUNK_SIZE) -> pl.DataFrame:
    """
    优化数据框处理，利用Polars的并行能力
    
    Args:
        df: 输入数据框
        chunk_size: 数据块大小
        
    Returns:
        优化后的数据框
    """
    try:
        # 启用Polars的并行处理
        with pl.Config(streaming_chunk_size=chunk_size):
            # 如果数据量大，使用lazy evaluation
            if df.height > chunk_size:
                logger.info(f"使用lazy evaluation处理大数据集 ({df.height} 行)")
                return df.lazy().collect()
            else:
                return df
    except Exception as e:
        logger.warning(f"数据框优化失败，使用原始数据: {e}")
        return df


def parallel_column_processing(df: pl.DataFrame, columns: List[str], 
                             process_func: Callable, max_workers: int = MAX_WORKERS) -> Dict[str, Any]:
    """
    并行处理多个列
    
    Args:
        df: 数据框
        columns: 列名列表
        process_func: 处理函数
        max_workers: 最大工作线程数
        
    Returns:
        处理结果字典
    """
    results = {}
    
    if not columns:
        return results
    
    # 如果列数较少，直接顺序处理
    if len(columns) <= 2:
        for col in columns:
            if col in df.columns:
                try:
                    results[col] = process_func(df[col])
                except Exception as e:
                    logger.error(f"处理列 '{col}' 失败: {e}")
                    results[col] = None
        return results
    
    # 并行处理多个列
    with ParallelProcessor(max_workers=min(max_workers, len(columns))) as processor:
        futures = []
        
        for col in columns:
            if col in df.columns:
                future = processor.submit_task(
                    f"process_column_{col}",
                    process_func,
                    df[col]
                )
                futures.append((col, future))
        
        # 收集结果
        for col, future in futures:
            try:
                task_result = future.result(timeout=30)  # 30秒超时
                if task_result.success:
                    results[col] = task_result.result
                else:
                    logger.error(f"列 '{col}' 处理失败: {task_result.error}")
                    results[col] = None
            except Exception as e:
                logger.error(f"获取列 '{col}' 处理结果失败: {e}")
                results[col] = None
    
    return results


def get_optimal_chunk_size(data_size: int, available_memory: Optional[float] = None) -> int:
    """
    根据数据大小和可用内存计算最优数据块大小
    
    Args:
        data_size: 数据大小（行数）
        available_memory: 可用内存（GB）
        
    Returns:
        最优数据块大小
    """
    # 基础块大小
    base_chunk_size = CHUNK_SIZE
    
    # 根据数据大小调整
    if data_size < 1000:
        return data_size  # 小数据集不分块
    elif data_size < 10000:
        return min(base_chunk_size, data_size // 2)
    elif data_size < 100000:
        return base_chunk_size
    else:
        # 大数据集，根据可用内存调整
        if available_memory and available_memory > 4:
            return base_chunk_size * 2
        else:
            return base_chunk_size // 2


def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = get_memory_usage()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            logger.info(
                f"函数 '{func.__name__}' 执行完成 - "
                f"耗时: {execution_time:.2f}秒, "
                f"内存变化: {memory_delta:.2f}MB"
            )
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(
                f"函数 '{func.__name__}' 执行失败 - "
                f"耗时: {execution_time:.2f}秒, 错误: {e}"
            )
            raise
    
    return wrapper


def get_memory_usage() -> float:
    """
    获取当前内存使用量（MB）
    
    Returns:
        内存使用量
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # 如果没有psutil，返回0
        return 0.0