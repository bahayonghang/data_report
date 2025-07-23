"""
日志配置和监控模块

负责：
- 结构化日志记录
- 性能指标收集
- 错误追踪
- 运行状态监控
"""

import logging
import logging.config
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os
import threading


@dataclass
class LogEntry:
    """日志条目数据结构"""
    timestamp: str
    level: str
    message: str
    operation: str
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    file_size: Optional[int] = None
    rows_processed: Optional[int] = None
    error_type: Optional[str] = None
    error_details: Optional[str] = None


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 配置日志
        self.setup_logging()
        
        # 性能指标存储
        self.metrics = []
        self._lock = threading.Lock()
    
    def setup_logging(self):
        """设置日志配置"""
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "json": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "detailed"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(self.log_dir / "app.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "performance": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": str(self.log_dir / "performance.log"),
                    "maxBytes": 10485760,
                    "backupCount": 3
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "INFO"
                },
                "performance": {
                    "handlers": ["performance"],
                    "level": "INFO",
                    "propagate": False
                }
            }
        }
        
        logging.config.dictConfig(log_config)
        self.logger = logging.getLogger(__name__)
        self.performance_logger = logging.getLogger("performance")
    
    def log_operation_start(self, operation: str, **kwargs) -> float:
        """记录操作开始"""
        start_time = time.time()
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            message=f"Starting {operation}",
            operation=operation,
            **kwargs
        )
        
        self.logger.info(json.dumps(asdict(entry)))
        return start_time
    
    def log_operation_end(self, operation: str, start_time: float, **kwargs) -> None:
        """记录操作结束"""
        duration = time.time() - start_time
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            message=f"Completed {operation}",
            operation=operation,
            duration=duration,
            **kwargs
        )
        
        self.performance_logger.info(json.dumps(asdict(entry)))
        
        # 记录性能指标
        with self._lock:
            self.metrics.append({
                "operation": operation,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            })
    
    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """记录错误"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="ERROR",
            message=str(error),
            operation=operation,
            error_type=type(error).__name__,
            error_details=str(error),
            **kwargs
        )
        
        self.logger.error(json.dumps(asdict(entry)))
    
    def log_warning(self, operation: str, message: str, **kwargs) -> None:
        """记录警告"""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="WARNING",
            message=message,
            operation=operation,
            **kwargs
        )
        
        self.logger.warning(json.dumps(asdict(entry)))
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        with self._lock:
            if not self.metrics:
                return {}
            
            operations = {}
            for metric in self.metrics:
                op = metric["operation"]
                if op not in operations:
                    operations[op] = []
                operations[op].append(metric)
            
            summary = {}
            for op, metrics in operations.items():
                durations = [m["duration"] for m in metrics]
                summary[op] = {
                    "count": len(metrics),
                    "total_time": sum(durations),
                    "avg_time": sum(durations) / len(durations),
                    "min_time": min(durations),
                    "max_time": max(durations),
                }
            
            return summary


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {
            "files_processed": 0,
            "total_rows_processed": 0,
            "total_columns_processed": 0,
            "errors": 0,
            "warnings": 0,
            "processing_times": [],
            "memory_usage": [],
        }
        self._lock = threading.Lock()
    
    def record_file_processed(self, filename: str, rows: int, cols: int, duration: float, memory_mb: float):
        """记录文件处理"""
        with self._lock:
            self.metrics["files_processed"] += 1
            self.metrics["total_rows_processed"] += rows
            self.metrics["total_columns_processed"] += cols
            self.metrics["processing_times"].append(duration)
            self.metrics["memory_usage"].append(memory_mb)
    
    def record_error(self):
        """记录错误"""
        with self._lock:
            self.metrics["errors"] += 1
    
    def record_warning(self):
        """记录警告"""
        with self._lock:
            self.metrics["warnings"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        with self._lock:
            metrics_copy = self.metrics.copy()
            
            if metrics_copy["processing_times"]:
                times = metrics_copy["processing_times"]
                metrics_copy["avg_processing_time"] = sum(times) / len(times)
                metrics_copy["min_processing_time"] = min(times)
                metrics_copy["max_processing_time"] = max(times)
            
            if metrics_copy["memory_usage"]:
                memory = metrics_copy["memory_usage"]
                metrics_copy["avg_memory_usage"] = sum(memory) / len(memory)
                metrics_copy["max_memory_usage"] = max(memory)
            
            return metrics_copy
    
    def save_metrics(self, filename: str = None) -> str:
        """保存指标到文件"""
        if filename is None:
            filename = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        metrics = self.get_metrics()
        
        filepath = Path("logs") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        return str(filepath)


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        import psutil
        
        # 系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        # 进程信息
        process = psutil.Process()
        memory_info = process.memory_info()
        
        uptime = datetime.now() - self.start_time
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / 1024 / 1024,
                "disk_percent": disk.percent,
            },
            "process": {
                "memory_rss_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
            }
        }


# 全局实例
performance_logger = PerformanceLogger()
metrics_collector = MetricsCollector()
health_checker = HealthChecker()


def setup_logging():
    """设置日志系统"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "app.log"),
        ]
    )


def log_performance(func):
    """性能日志装饰器"""
    def wrapper(*args, **kwargs):
        operation_name = func.__name__
        
        # 记录开始
        start_time = performance_logger.log_operation_start(operation_name)
        
        try:
            result = func(*args, **kwargs)
            
            # 记录成功结束
            performance_logger.log_operation_end(
                operation_name, 
                start_time,
                memory_usage=0  # 可以添加内存使用
            )
            
            return result
            
        except Exception as e:
            # 记录错误
            performance_logger.log_error(operation_name, e)
            raise
    
    return wrapper