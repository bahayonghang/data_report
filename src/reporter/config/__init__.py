"""配置管理模块

提供统一的配置管理功能，包括：
- 应用配置加载和验证
- 环境变量处理
- 配置文件解析
- 默认配置管理
"""

from .config_manager import ConfigManager, config_manager
from .settings import Settings, get_settings

__all__ = [
    "ConfigManager",
    "config_manager",
    "Settings",
    "get_settings"
]