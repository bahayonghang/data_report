"""
内存管理和资源清理模块

负责：
- 内存使用监控
- 垃圾回收优化
- 资源清理
- 内存限制处理
"""

import gc
import psutil
import os
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager
import threading
import time


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_mb: int = 1024):
        """
        初始化内存管理器
        
        Args:
            max_memory_mb: 最大内存使用限制（MB）
        """
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())
        self._lock = threading.Lock()
        self._memory_usage_history = []
        
    def get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况"""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024,
        }
    
    def check_memory_limit(self) -> bool:
        """检查是否超过内存限制"""
        current_usage = self.get_memory_usage()
        return current_usage["rss_mb"] <= self.max_memory_mb
    
    def force_garbage_collection(self) -> None:
        """强制垃圾回收"""
        gc.collect()
    
    def log_memory_usage(self, operation: str) -> None:
        """记录内存使用情况"""
        memory_info = self.get_memory_usage()
        logging.info(
            f"[{operation}] Memory usage: "
            f"{memory_info['rss_mb']:.1f}MB ({memory_info['percent']:.1f}%)"
        )
        
        # 记录历史
        with self._lock:
            self._memory_usage_history.append({
                "timestamp": time.time(),
                "operation": operation,
                "memory_mb": memory_info["rss_mb"]
            })
    
    def cleanup_large_objects(self) -> None:
        """清理大对象"""
        gc.collect()
        
        # 强制清理未引用的对象
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)
    
    def get_memory_trend(self, last_n: int = 10) -> Optional[Dict[str, float]]:
        """获取内存使用趋势"""
        with self._lock:
            if len(self._memory_usage_history) < last_n:
                return None
            
            recent_data = self._memory_usage_history[-last_n:]
            memory_values = [d["memory_mb"] for d in recent_data]
            
            if len(memory_values) < 2:
                return None
            
            # 计算趋势
            import numpy as np
            x = np.arange(len(memory_values))
            y = np.array(memory_values)
            
            # 线性回归
            coeffs = np.polyfit(x, y, 1)
            
            return {
                "trend_slope": coeffs[0],
                "trend_intercept": coeffs[1],
                "average_memory": np.mean(memory_values),
                "max_memory": np.max(memory_values),
                "min_memory": np.min(memory_values),
            }


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "cpu_percent": cpu_percent,
            "memory_total_mb": memory.total / 1024 / 1024,
            "memory_available_mb": memory.available / 1024 / 1024,
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            "disk_percent": disk.percent,
            "uptime_seconds": time.time() - self.start_time,
        }
    
    def get_process_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        memory_info = self.process.memory_info()
        cpu_times = self.process.cpu_times()
        
        return {
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "cpu_percent": self.process.cpu_percent(),
            "cpu_user_seconds": cpu_times.user,
            "cpu_system_seconds": cpu_times.system,
            "threads": self.process.num_threads(),
            "open_files": len(self.process.open_files()),
        }


class MemoryLimiter:
    """内存限制器"""
    
    def __init__(self, max_memory_mb: int = 1024):
        """
        初始化内存限制器
        
        Args:
            max_memory_mb: 最大内存使用限制（MB）
        """
        self.max_memory_mb = max_memory_mb
        self.memory_manager = MemoryManager(max_memory_mb)
    
    @contextmanager
    def memory_limit(self, operation: str):
        """内存限制上下文管理器"""
        start_memory = self.memory_manager.get_memory_usage()
        
        try:
            self.memory_manager.log_memory_usage(f"{operation}_start")
            yield
            
        except Exception as e:
            self.memory_manager.log_memory_usage(f"{operation}_error")
            raise
        
        finally:
            self.memory_manager.cleanup_large_objects()
            end_memory = self.memory_manager.get_memory_usage()
            
            # 检查内存使用
            if end_memory["rss_mb"] > self.max_memory_mb:
                logging.warning(
                    f"Memory limit exceeded: {end_memory['rss_mb']:.1f}MB > {self.max_memory_mb}MB"
                )
            
            self.memory_manager.log_memory_usage(f"{operation}_end")
    
    def check_and_cleanup(self, threshold_mb: int = 800) -> bool:
        """检查内存并清理"""
        current_memory = self.memory_manager.get_memory_usage()
        
        if current_memory["rss_mb"] > threshold_mb:
            logging.info(f"High memory usage detected: {current_memory['rss_mb']:.1f}MB")
            self.memory_manager.cleanup_large_objects()
            
            # 重新检查
            new_memory = self.memory_manager.get_memory_usage()
            memory_reduction = current_memory["rss_mb"] - new_memory["rss_mb"]
            
            if memory_reduction > 0:
                logging.info(f"Memory cleaned up: {memory_reduction:.1f}MB")
            
            return new_memory["rss_mb"] <= self.max_memory_mb
        
        return True


# 全局实例
memory_manager = MemoryManager(max_memory_mb=1024)
resource_monitor = ResourceMonitor()
memory_limiter = MemoryLimiter(max_memory_mb=1024)


def get_memory_report() -> Dict[str, Any]:
    """获取内存使用报告"""
    return {
        "memory_usage": memory_manager.get_memory_usage(),
        "system_info": resource_monitor.get_system_info(),
        "process_info": resource_monitor.get_process_info(),
        "memory_trend": memory_manager.get_memory_trend(),
    }


def monitor_memory_usage(func):
    """内存使用监控装饰器"""
    def wrapper(*args, **kwargs):
        operation_name = func.__name__
        
        with memory_limiter.memory_limit(operation_name):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                memory_manager.log_memory_usage(f"{operation_name}_exception")
                raise
    
    return wrapper


# 配置文件清理
class Config:
    """配置类"""
    MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "1024"))
    MEMORY_WARNING_THRESHOLD_MB = int(os.getenv("MEMORY_WARNING_THRESHOLD_MB", "800"))
    GC_COLLECT_INTERVAL = int(os.getenv("GC_COLLECT_INTERVAL", "10"))
    ENABLE_MEMORY_PROFILING = os.getenv("ENABLE_MEMORY_PROFILING", "false").lower() == "true"