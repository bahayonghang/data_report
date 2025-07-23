# 安全模块
"""
路径遍历保护、文件类型验证

负责：
- 防止路径遍历攻击
- 文件类型和大小验证
- 安全目录限制
"""

import os
from pathlib import Path
from typing import List


# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.csv', '.parquet'}

# 默认文件大小限制 (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


def validate_path(file_path: str, base_directory: str) -> bool:
    """
    验证文件路径是否在安全目录内，防止路径遍历攻击
    
    Args:
        file_path: 要验证的文件路径
        base_directory: 基础安全目录
        
    Returns:
        bool: 路径是否安全
    """
    try:
        # 规范化路径，解析所有 .. 和 .
        base_path = Path(base_directory).resolve()
        target_path = Path(base_directory) / file_path
        target_path = target_path.resolve()
        
        # 检查目标路径是否在基础目录内
        return target_path.is_file() and str(target_path).startswith(str(base_path))
    except (ValueError, OSError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的安全文件名
    """
    import re
    
    # 移除路径分隔符和特殊字符
    safe_chars = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]', '', filename)
    
    # 移除前导和尾随的点和空格
    safe_chars = safe_chars.strip('. ')
    
    # 如果文件名为空，返回默认文件名
    if not safe_chars:
        return 'uploaded_file'
    
    # 限制文件名长度
    max_length = 255
    if len(safe_chars) > max_length:
        name, ext = os.path.splitext(safe_chars)
        safe_chars = name[:max_length-len(ext)] + ext
    
    return safe_chars


def is_allowed_file_type(filename: str) -> bool:
    """
    检查文件类型是否被允许（CSV/Parquet）
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 文件类型是否被允许
    """
    if not filename:
        return False
    
    file_path = Path(filename)
    return file_path.suffix.lower() in ALLOWED_EXTENSIONS


def check_file_size(file_path: str, max_size: int = MAX_FILE_SIZE) -> bool:
    """
    检查文件大小是否在限制内
    
    Args:
        file_path: 文件路径
        max_size: 最大文件大小（字节）
        
    Returns:
        bool: 文件大小是否符合要求
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists() or not file_path_obj.is_file():
            return False
        
        return file_path_obj.stat().st_size <= max_size
    except (OSError, ValueError):
        return False


def get_safe_file_path(filename: str, base_directory: str) -> str:
    """
    获取安全的完整文件路径
    
    Args:
        filename: 文件名
        base_directory: 基础目录
        
    Returns:
        str: 安全的完整文件路径
    """
    sanitized = sanitize_filename(filename)
    safe_path = Path(base_directory) / sanitized
    return str(safe_path.resolve())


def validate_file_operation(filename: str, base_directory: str) -> tuple[bool, str]:
    """
    综合验证文件操作的安全性
    
    Args:
        filename: 文件名
        base_directory: 基础目录
        
    Returns:
        tuple[bool, str]: (是否安全, 错误信息)
    """
    if not filename:
        return False, "文件名为空"
    
    if not is_allowed_file_type(filename):
        return False, f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
    
    safe_path = get_safe_file_path(filename, base_directory)
    
    if not validate_path(filename, base_directory):
        return False, "文件路径不安全"
    
    if Path(safe_path).exists() and not check_file_size(safe_path):
        return False, f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"
    
    return True, ""