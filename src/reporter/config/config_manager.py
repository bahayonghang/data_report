import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Union
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ConfigManager:
    """配置管理器
    
    负责加载、验证和管理应用配置，支持：
    - 多种配置文件格式（JSON、YAML、环境变量）
    - 配置验证和默认值
    - 环境特定配置
    - 配置热重载
    """
    
    config_dir: Path = field(default_factory=lambda: Path("config"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    _config: Dict[str, Any] = field(default_factory=dict, init=False)
    _config_files: Dict[str, Path] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """初始化配置管理器"""
        self.config_dir = Path(self.config_dir)
        self._load_default_config()
        self._load_environment_config()
        self._load_env_variables()
        
    def _load_default_config(self) -> None:
        """加载默认配置"""
        default_config = {
            # 数据处理配置
            "data_processing": {
                "chunk_size_mb": 100,
                "max_memory_usage_mb": 2048,
                "parallel_workers": 4,
                "enable_caching": True,
                "cache_dir": "cache",
                "temp_dir": "temp"
            },
            
            # 分析配置
            "analysis": {
                "correlation_threshold": 0.7,
                "significance_level": 0.05,
                "max_categories": 50,
                "sample_size_threshold": 10000,
                "enable_time_series": True,
                "enable_correlation": True,
                "enable_outlier_detection": True
            },
            
            # 输出配置
            "output": {
                "format": "json",
                "include_charts": True,
                "chart_format": "png",
                "output_dir": "output",
                "filename_template": "analysis_{timestamp}",
                "compress_results": False
            },
            
            # 性能配置
            "performance": {
                "enable_profiling": False,
                "memory_monitoring": True,
                "gc_threshold": 0.8,
                "max_execution_time": 3600,  # 1小时
                "progress_update_interval": 1.0  # 秒
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/app.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            
            # 数据库配置（如果需要）
            "database": {
                "enabled": False,
                "url": None,
                "pool_size": 5,
                "timeout": 30
            }
        }
        
        self._config.update(default_config)
        logger.info("默认配置已加载")
    
    def _load_environment_config(self) -> None:
        """加载环境特定配置文件"""
        config_files = [
            self.config_dir / "config.json",
            self.config_dir / "config.yaml",
            self.config_dir / "config.yml",
            self.config_dir / f"config.{self.environment}.json",
            self.config_dir / f"config.{self.environment}.yaml",
            self.config_dir / f"config.{self.environment}.yml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    config_data = self._load_config_file(config_file)
                    self._merge_config(config_data)
                    self._config_files[config_file.name] = config_file
                    logger.info(f"配置文件已加载: {config_file}")
                except Exception as e:
                    logger.error(f"加载配置文件失败 {config_file}: {e}")
    
    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.suffix.lower() == '.json':
                return json.load(f)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f) or {}
            else:
                raise ValueError(f"不支持的配置文件格式: {file_path.suffix}")
    
    def _load_env_variables(self) -> None:
        """从环境变量加载配置"""
        env_mappings = {
            # 数据处理
            "DATA_CHUNK_SIZE_MB": "data_processing.chunk_size_mb",
            "MAX_MEMORY_MB": "data_processing.max_memory_usage_mb",
            "PARALLEL_WORKERS": "data_processing.parallel_workers",
            "ENABLE_CACHING": "data_processing.enable_caching",
            "CACHE_DIR": "data_processing.cache_dir",
            "TEMP_DIR": "data_processing.temp_dir",
            
            # 分析
            "CORRELATION_THRESHOLD": "analysis.correlation_threshold",
            "SIGNIFICANCE_LEVEL": "analysis.significance_level",
            "SAMPLE_SIZE_THRESHOLD": "analysis.sample_size_threshold",
            
            # 输出
            "OUTPUT_FORMAT": "output.format",
            "OUTPUT_DIR": "output.output_dir",
            "CHART_FORMAT": "output.chart_format",
            
            # 性能
            "ENABLE_PROFILING": "performance.enable_profiling",
            "MAX_EXECUTION_TIME": "performance.max_execution_time",
            
            # 日志
            "LOG_LEVEL": "logging.level",
            "LOG_FILE": "logging.file"
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # 类型转换
                    converted_value = self._convert_env_value(env_value, config_path)
                    self._set_nested_config(config_path, converted_value)
                    logger.debug(f"环境变量已加载: {env_var} -> {config_path}")
                except Exception as e:
                    logger.warning(f"环境变量转换失败 {env_var}: {e}")
    
    def _convert_env_value(self, value: str, config_path: str) -> Any:
        """转换环境变量值到适当的类型"""
        # 布尔值转换
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # 数字转换
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # 字符串值
        return value
    
    def _set_nested_config(self, path: str, value: Any) -> None:
        """设置嵌套配置值"""
        keys = path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """合并配置"""
        def merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> None:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self._config, new_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键（如 'data_processing.chunk_size_mb'）
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        self._set_nested_config(key, value)
        logger.debug(f"配置已更新: {key} = {value}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        return self._config.get(section, {})
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            配置是否有效
        """
        try:
            # 验证必需的配置项
            required_sections = ['data_processing', 'analysis', 'output', 'performance']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"缺少必需的配置段: {section}")
                    return False
            
            # 验证数值范围
            validations = [
                ('data_processing.chunk_size_mb', lambda x: x > 0),
                ('data_processing.max_memory_usage_mb', lambda x: x > 0),
                ('data_processing.parallel_workers', lambda x: x > 0),
                ('analysis.correlation_threshold', lambda x: 0 <= x <= 1),
                ('analysis.significance_level', lambda x: 0 < x < 1),
                ('performance.max_execution_time', lambda x: x > 0)
            ]
            
            for key, validator in validations:
                value = self.get(key)
                if value is not None and not validator(value):
                    logger.error(f"配置值无效: {key} = {value}")
                    return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def reload(self) -> None:
        """重新加载配置"""
        logger.info("重新加载配置...")
        self._config.clear()
        self._config_files.clear()
        
        self._load_default_config()
        self._load_environment_config()
        self._load_env_variables()
        
        if self.validate_config():
            logger.info("配置重新加载完成")
        else:
            logger.error("配置重新加载失败")
    
    def to_dict(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()
    
    def save_config(self, file_path: Union[str, Path], format: str = "json") -> None:
        """保存当前配置到文件
        
        Args:
            file_path: 文件路径
            format: 文件格式（json 或 yaml）
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if format.lower() == 'json':
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            elif format.lower() in ['yaml', 'yml']:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的格式: {format}")
        
        logger.info(f"配置已保存到: {file_path}")

# 全局配置管理器实例
config_manager = ConfigManager()