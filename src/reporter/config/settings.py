from typing import Optional, Dict, Any
from dataclasses import dataclass
from .config_manager import config_manager

@dataclass
class DataProcessingSettings:
    """数据处理设置"""
    chunk_size_mb: int = 100
    max_memory_usage_mb: int = 2048
    parallel_workers: int = 4
    enable_caching: bool = True
    cache_dir: str = "cache"
    temp_dir: str = "temp"
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'DataProcessingSettings':
        """从配置字典创建设置"""
        return cls(
            chunk_size_mb=config.get('chunk_size_mb', 100),
            max_memory_usage_mb=config.get('max_memory_usage_mb', 2048),
            parallel_workers=config.get('parallel_workers', 4),
            enable_caching=config.get('enable_caching', True),
            cache_dir=config.get('cache_dir', 'cache'),
            temp_dir=config.get('temp_dir', 'temp')
        )

@dataclass
class AnalysisSettings:
    """分析设置"""
    correlation_threshold: float = 0.7
    significance_level: float = 0.05
    max_categories: int = 50
    sample_size_threshold: int = 10000
    enable_time_series: bool = True
    enable_correlation: bool = True
    enable_outlier_detection: bool = True
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AnalysisSettings':
        """从配置字典创建设置"""
        return cls(
            correlation_threshold=config.get('correlation_threshold', 0.7),
            significance_level=config.get('significance_level', 0.05),
            max_categories=config.get('max_categories', 50),
            sample_size_threshold=config.get('sample_size_threshold', 10000),
            enable_time_series=config.get('enable_time_series', True),
            enable_correlation=config.get('enable_correlation', True),
            enable_outlier_detection=config.get('enable_outlier_detection', True)
        )

@dataclass
class OutputSettings:
    """输出设置"""
    format: str = "json"
    include_charts: bool = True
    chart_format: str = "png"
    output_dir: str = "output"
    filename_template: str = "analysis_{timestamp}"
    compress_results: bool = False
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'OutputSettings':
        """从配置字典创建设置"""
        return cls(
            format=config.get('format', 'json'),
            include_charts=config.get('include_charts', True),
            chart_format=config.get('chart_format', 'png'),
            output_dir=config.get('output_dir', 'output'),
            filename_template=config.get('filename_template', 'analysis_{timestamp}'),
            compress_results=config.get('compress_results', False)
        )

@dataclass
class PerformanceSettings:
    """性能设置"""
    enable_profiling: bool = False
    memory_monitoring: bool = True
    gc_threshold: float = 0.8
    max_execution_time: int = 3600  # 1小时
    progress_update_interval: float = 1.0  # 秒
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'PerformanceSettings':
        """从配置字典创建设置"""
        return cls(
            enable_profiling=config.get('enable_profiling', False),
            memory_monitoring=config.get('memory_monitoring', True),
            gc_threshold=config.get('gc_threshold', 0.8),
            max_execution_time=config.get('max_execution_time', 3600),
            progress_update_interval=config.get('progress_update_interval', 1.0)
        )

@dataclass
class LoggingSettings:
    """日志设置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/app.log"
    max_size_mb: int = 10
    backup_count: int = 5
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'LoggingSettings':
        """从配置字典创建设置"""
        return cls(
            level=config.get('level', 'INFO'),
            format=config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file=config.get('file', 'logs/app.log'),
            max_size_mb=config.get('max_size_mb', 10),
            backup_count=config.get('backup_count', 5)
        )

@dataclass
class DatabaseSettings:
    """数据库设置"""
    enabled: bool = False
    url: Optional[str] = None
    pool_size: int = 5
    timeout: int = 30
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'DatabaseSettings':
        """从配置字典创建设置"""
        return cls(
            enabled=config.get('enabled', False),
            url=config.get('url'),
            pool_size=config.get('pool_size', 5),
            timeout=config.get('timeout', 30)
        )

@dataclass
class Settings:
    """应用设置
    
    包含所有配置模块的设置，提供类型安全的配置访问
    """
    data_processing: DataProcessingSettings
    analysis: AnalysisSettings
    output: OutputSettings
    performance: PerformanceSettings
    logging: LoggingSettings
    database: DatabaseSettings
    
    @classmethod
    def from_config_manager(cls) -> 'Settings':
        """从配置管理器创建设置"""
        return cls(
            data_processing=DataProcessingSettings.from_config(
                config_manager.get_section('data_processing')
            ),
            analysis=AnalysisSettings.from_config(
                config_manager.get_section('analysis')
            ),
            output=OutputSettings.from_config(
                config_manager.get_section('output')
            ),
            performance=PerformanceSettings.from_config(
                config_manager.get_section('performance')
            ),
            logging=LoggingSettings.from_config(
                config_manager.get_section('logging')
            ),
            database=DatabaseSettings.from_config(
                config_manager.get_section('database')
            )
        )
    
    def validate(self) -> bool:
        """验证设置
        
        Returns:
            设置是否有效
        """
        try:
            # 验证数据处理设置
            if self.data_processing.chunk_size_mb <= 0:
                return False
            if self.data_processing.max_memory_usage_mb <= 0:
                return False
            if self.data_processing.parallel_workers <= 0:
                return False
            
            # 验证分析设置
            if not (0 <= self.analysis.correlation_threshold <= 1):
                return False
            if not (0 < self.analysis.significance_level < 1):
                return False
            if self.analysis.max_categories <= 0:
                return False
            if self.analysis.sample_size_threshold <= 0:
                return False
            
            # 验证输出设置
            if self.output.format not in ['json', 'yaml', 'csv', 'excel']:
                return False
            if self.output.chart_format not in ['png', 'jpg', 'svg', 'pdf']:
                return False
            
            # 验证性能设置
            if not (0 < self.performance.gc_threshold <= 1):
                return False
            if self.performance.max_execution_time <= 0:
                return False
            if self.performance.progress_update_interval <= 0:
                return False
            
            # 验证日志设置
            if self.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                return False
            if self.logging.max_size_mb <= 0:
                return False
            if self.logging.backup_count < 0:
                return False
            
            # 验证数据库设置
            if self.database.enabled and not self.database.url:
                return False
            if self.database.pool_size <= 0:
                return False
            if self.database.timeout <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data_processing': self.data_processing.__dict__,
            'analysis': self.analysis.__dict__,
            'output': self.output.__dict__,
            'performance': self.performance.__dict__,
            'logging': self.logging.__dict__,
            'database': self.database.__dict__
        }

# 全局设置实例
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """获取全局设置实例
    
    Returns:
        Settings: 应用设置实例
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_config_manager()
        if not _settings.validate():
            raise ValueError("配置验证失败")
    return _settings

def reload_settings() -> Settings:
    """重新加载设置
    
    Returns:
        Settings: 新的设置实例
    """
    global _settings
    config_manager.reload()
    _settings = Settings.from_config_manager()
    if not _settings.validate():
        raise ValueError("配置验证失败")
    return _settings