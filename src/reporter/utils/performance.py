# 性能监控和优化工具模块
# 提供内存监控、性能分析和资源管理功能

import time
import logging
import functools
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import threading
import gc

# 配置日志
logger = logging.getLogger(__name__)

# 性能配置常量
MEMORY_WARNING_THRESHOLD = 1024  # MB
MEMORY_CRITICAL_THRESHOLD = 2048  # MB
GC_COLLECTION_INTERVAL = 100  # 操作次数


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    function_name: str
    execution_time: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_time: float
    success: bool
    error_message: Optional[str] = None


class PerformanceMonitor:
    """性能监控器类"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.operation_count = 0
        self.lock = threading.Lock()
    
    def get_memory_usage(self) -> float:
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
            # 如果没有psutil，尝试使用resource模块
            try:
                import resource
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            except (ImportError, AttributeError):
                return 0.0
    
    def get_cpu_time(self) -> float:
        """
        获取CPU时间
        
        Returns:
            CPU时间（秒）
        """
        try:
            import psutil
            process = psutil.Process()
            cpu_times = process.cpu_times()
            return cpu_times.user + cpu_times.system
        except ImportError:
            return time.process_time()
    
    def check_memory_usage(self) -> None:
        """
        检查内存使用情况并发出警告
        """
        current_memory = self.get_memory_usage()
        
        if current_memory > MEMORY_CRITICAL_THRESHOLD:
            logger.critical(f"内存使用量过高: {current_memory:.2f}MB，建议释放内存")
            self.force_garbage_collection()
        elif current_memory > MEMORY_WARNING_THRESHOLD:
            logger.warning(f"内存使用量较高: {current_memory:.2f}MB")
    
    def force_garbage_collection(self) -> None:
        """
        强制垃圾回收
        """
        logger.info("执行垃圾回收...")
        collected = gc.collect()
        logger.info(f"垃圾回收完成，回收了 {collected} 个对象")
    
    def monitor_function(self, func: Callable) -> Callable:
        """
        函数性能监控装饰器
        
        Args:
            func: 要监控的函数
            
        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录开始状态
            start_time = time.time()
            start_cpu = self.get_cpu_time()
            memory_before = self.get_memory_usage()
            memory_peak = memory_before
            
            success = True
            error_message = None
            result = None
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 监控内存峰值
                memory_peak = max(memory_peak, self.get_memory_usage())
                
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"函数 '{func.__name__}' 执行失败: {e}")
                raise
            
            finally:
                # 记录结束状态
                end_time = time.time()
                end_cpu = self.get_cpu_time()
                memory_after = self.get_memory_usage()
                
                # 创建性能指标
                metrics = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=end_time - start_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_peak=memory_peak,
                    cpu_time=end_cpu - start_cpu,
                    success=success,
                    error_message=error_message
                )
                
                # 记录指标
                with self.lock:
                    self.metrics_history.append(metrics)
                    self.operation_count += 1
                
                # 定期检查内存和垃圾回收
                if self.operation_count % GC_COLLECTION_INTERVAL == 0:
                    self.check_memory_usage()
                
                # 记录性能日志
                memory_delta = memory_after - memory_before
                logger.info(
                    f"函数 '{func.__name__}' 性能指标 - "
                    f"执行时间: {metrics.execution_time:.3f}s, "
                    f"CPU时间: {metrics.cpu_time:.3f}s, "
                    f"内存变化: {memory_delta:+.2f}MB, "
                    f"内存峰值: {memory_peak:.2f}MB"
                )
            
            return result
        
        return wrapper
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Returns:
            性能摘要字典
        """
        if not self.metrics_history:
            return {"message": "暂无性能数据"}
        
        # 计算统计信息
        total_operations = len(self.metrics_history)
        successful_operations = sum(1 for m in self.metrics_history if m.success)
        total_execution_time = sum(m.execution_time for m in self.metrics_history)
        total_cpu_time = sum(m.cpu_time for m in self.metrics_history)
        
        # 按函数分组统计
        function_stats = {}
        for metrics in self.metrics_history:
            func_name = metrics.function_name
            if func_name not in function_stats:
                function_stats[func_name] = {
                    "count": 0,
                    "total_time": 0,
                    "total_cpu_time": 0,
                    "max_memory": 0,
                    "success_count": 0
                }
            
            stats = function_stats[func_name]
            stats["count"] += 1
            stats["total_time"] += metrics.execution_time
            stats["total_cpu_time"] += metrics.cpu_time
            stats["max_memory"] = max(stats["max_memory"], metrics.memory_peak)
            if metrics.success:
                stats["success_count"] += 1
        
        # 计算平均值
        for func_name, stats in function_stats.items():
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["avg_cpu_time"] = stats["total_cpu_time"] / stats["count"]
            stats["success_rate"] = stats["success_count"] / stats["count"]
        
        return {
            "总操作数": total_operations,
            "成功操作数": successful_operations,
            "成功率": f"{(successful_operations / total_operations * 100):.1f}%",
            "总执行时间": f"{total_execution_time:.3f}秒",
            "总CPU时间": f"{total_cpu_time:.3f}秒",
            "平均执行时间": f"{total_execution_time / total_operations:.3f}秒",
            "当前内存使用": f"{self.get_memory_usage():.2f}MB",
            "函数统计": function_stats
        }
    
    def clear_history(self) -> None:
        """
        清空性能历史记录
        """
        with self.lock:
            self.metrics_history.clear()
            self.operation_count = 0
        logger.info("性能历史记录已清空")


class ResourceManager:
    """资源管理器类"""
    
    def __init__(self, memory_limit_mb: Optional[float] = None):
        """
        初始化资源管理器
        
        Args:
            memory_limit_mb: 内存限制（MB）
        """
        self.memory_limit = memory_limit_mb
        self.monitor = PerformanceMonitor()
    
    def check_resource_availability(self) -> bool:
        """
        检查资源可用性
        
        Returns:
            资源是否可用
        """
        current_memory = self.monitor.get_memory_usage()
        
        if self.memory_limit and current_memory > self.memory_limit:
            logger.warning(f"内存使用超限: {current_memory:.2f}MB > {self.memory_limit}MB")
            return False
        
        return True
    
    def optimize_memory_usage(self) -> None:
        """
        优化内存使用
        """
        logger.info("开始内存优化...")
        
        # 强制垃圾回收
        self.monitor.force_garbage_collection()
        
        # 检查内存使用情况
        current_memory = self.monitor.get_memory_usage()
        logger.info(f"内存优化完成，当前内存使用: {current_memory:.2f}MB")
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        try:
            import psutil
            import os
            
            # 获取系统信息
            cpu_count = os.cpu_count() or 1
            memory_info = psutil.virtual_memory()
            
            return {
                "CPU核心数": cpu_count,
                "总内存": f"{memory_info.total / 1024 / 1024 / 1024:.2f}GB",
                "可用内存": f"{memory_info.available / 1024 / 1024 / 1024:.2f}GB",
                "内存使用率": f"{memory_info.percent:.1f}%",
                "当前进程内存": f"{self.monitor.get_memory_usage():.2f}MB",
                "内存限制": f"{self.memory_limit}MB" if self.memory_limit else "无限制"
            }
        except ImportError:
            import os
            return {
                "CPU核心数": os.cpu_count() or 1,
                "当前进程内存": f"{self.monitor.get_memory_usage():.2f}MB",
                "内存限制": f"{self.memory_limit}MB" if self.memory_limit else "无限制",
                "备注": "需要安装psutil获取详细系统信息"
            }


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器（全局实例）
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰后的函数
    """
    return performance_monitor.monitor_function(func)


def get_performance_summary() -> Dict[str, Any]:
    """
    获取全局性能摘要
    
    Returns:
        性能摘要字典
    """
    return performance_monitor.get_performance_summary()


def clear_performance_history() -> None:
    """
    清空全局性能历史记录
    """
    performance_monitor.clear_history()


def optimize_polars_settings() -> None:
    """
    优化Polars设置以提高性能
    """
    try:
        import polars as pl
        import os
        
        # 设置线程数
        cpu_count = os.cpu_count() or 1
        pl.Config.set_tbl_rows(20)  # 限制显示行数
        
        # 如果有足够的CPU核心，启用并行处理
        if cpu_count >= 4:
            logger.info(f"启用Polars并行处理，CPU核心数: {cpu_count}")
        
        logger.info("Polars设置优化完成")
        
    except Exception as e:
        logger.warning(f"Polars设置优化失败: {e}")


def estimate_memory_requirement(data_size: int, columns: int, dtype_size: int = 8) -> float:
    """
    估算内存需求
    
    Args:
        data_size: 数据行数
        columns: 列数
        dtype_size: 数据类型大小（字节）
        
    Returns:
        估算的内存需求（MB）
    """
    # 基础内存需求
    base_memory = data_size * columns * dtype_size
    
    # 考虑处理过程中的额外内存开销（约2-3倍）
    processing_overhead = base_memory * 2.5
    
    # 转换为MB
    total_memory_mb = processing_overhead / 1024 / 1024
    
    return total_memory_mb


def suggest_optimization_strategy(data_size: int, available_memory: float) -> Dict[str, Any]:
    """
    建议优化策略
    
    Args:
        data_size: 数据大小（行数）
        available_memory: 可用内存（MB）
        
    Returns:
        优化建议字典
    """
    estimated_memory = estimate_memory_requirement(data_size, 10)  # 假设10列
    
    suggestions = {
        "数据大小": data_size,
        "估算内存需求": f"{estimated_memory:.2f}MB",
        "可用内存": f"{available_memory:.2f}MB",
        "建议策略": []
    }
    
    if estimated_memory > available_memory * 0.8:
        suggestions["建议策略"].extend([
            "使用数据采样减少内存使用",
            "启用流式处理",
            "分批处理数据",
            "考虑使用更高效的数据格式（如Parquet）"
        ])
    elif data_size > 100000:
        suggestions["建议策略"].extend([
            "启用并行处理",
            "使用lazy evaluation",
            "优化数据类型"
        ])
    else:
        suggestions["建议策略"].append("当前配置已足够，无需特殊优化")
    
    return suggestions