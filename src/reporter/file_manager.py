"""文件存储管理模块

负责：
- 文件存储路径管理
- 文件保存和读取
- 分析结果存储
- 文件清理和维护
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging


class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime对象"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

logger = logging.getLogger(__name__)

# 存储目录配置
BASE_DATA_DIR = Path("data")
UPLOADS_DIR = BASE_DATA_DIR / "uploads"
ANALYSIS_RESULTS_DIR = BASE_DATA_DIR / "analysis_results"
DATABASE_DIR = BASE_DATA_DIR / "database"


class FileStorageManager:
    """文件存储管理器"""

    def __init__(self):
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        for directory in [UPLOADS_DIR, ANALYSIS_RESULTS_DIR, DATABASE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {directory}")

    def get_file_storage_path(self, file_hash: str, file_extension: str) -> Path:
        """获取文件存储路径
        
        使用年/月的目录结构组织文件
        
        Args:
            file_hash: 文件哈希值
            file_extension: 文件扩展名（包含点号）
            
        Returns:
            Path: 文件存储路径
        """
        now = datetime.now()
        year_month_dir = UPLOADS_DIR / str(now.year) / f"{now.month:02d}"
        year_month_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{file_hash}{file_extension}"
        return year_month_dir / filename

    def get_analysis_result_path(self, analysis_id: int) -> Path:
        """获取分析结果存储路径
        
        Args:
            analysis_id: 分析记录ID
            
        Returns:
            Path: 分析结果文件路径
        """
        now = datetime.now()
        year_month_dir = ANALYSIS_RESULTS_DIR / str(now.year) / f"{now.month:02d}"
        year_month_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"analysis_{analysis_id}.json"
        return year_month_dir / filename

    async def save_uploaded_file(self, file_content: bytes, file_hash: str, 
                               file_extension: str) -> Path:
        """保存上传的文件
        
        Args:
            file_content: 文件内容
            file_hash: 文件哈希值
            file_extension: 文件扩展名
            
        Returns:
            Path: 保存的文件路径
        """
        file_path = self.get_file_storage_path(file_hash, file_extension)
        
        # 如果文件已存在，直接返回路径
        if file_path.exists():
            logger.info(f"文件已存在，跳过保存: {file_path}")
            return file_path
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"文件保存成功: {file_path}")
        return file_path

    async def save_analysis_result(self, analysis_result: Dict[str, Any], 
                                 analysis_id: int) -> Path:
        """保存分析结果
        
        Args:
            analysis_result: 分析结果数据
            analysis_id: 分析记录ID
            
        Returns:
            Path: 分析结果文件路径
        """
        result_path = self.get_analysis_result_path(analysis_id)
        
        # 保存为JSON格式
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logger.info(f"分析结果保存成功: {result_path}")
        # 返回使用正斜杠的标准化路径字符串，确保跨平台兼容性
        return result_path

    async def load_analysis_result(self, result_file_path: str) -> Optional[Dict[str, Any]]:
        """加载分析结果
        
        Args:
            result_file_path: 分析结果文件路径
            
        Returns:
            Optional[Dict]: 分析结果数据，如果文件不存在则返回None
        """
        try:
            # 处理跨平台路径兼容性：将Windows风格的反斜杠转换为正斜杠
            normalized_path = result_file_path.replace('\\', '/')
            result_path = Path(normalized_path)
            
            # 如果路径不是绝对路径，则相对于项目根目录
            if not result_path.is_absolute():
                result_path = Path.cwd() / result_path
            
            if not result_path.exists():
                logger.warning(f"分析结果文件不存在: {result_path}")
                return None
            
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载分析结果失败: {e}")
            return None

    async def delete_analysis_result(self, result_file_path: str) -> bool:
        """删除分析结果文件
        
        Args:
            result_file_path: 分析结果文件路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            result_path = Path(result_file_path)
            if result_path.exists():
                result_path.unlink()
                logger.info(f"分析结果文件删除成功: {result_path}")
                return True
            else:
                logger.warning(f"分析结果文件不存在: {result_path}")
                return True  # 文件不存在也算删除成功
        except Exception as e:
            logger.error(f"删除分析结果文件失败: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件是否存在
        """
        return Path(file_path).exists()

    async def cleanup_old_files(self, days_old: int = 30) -> Tuple[int, int]:
        """清理旧文件
        
        Args:
            days_old: 清理多少天前的文件
            
        Returns:
            Tuple[int, int]: (清理的文件数, 清理的分析结果数)
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_old)
        cutoff_timestamp = cutoff_time.timestamp()
        
        files_cleaned = 0
        results_cleaned = 0
        
        # 清理上传文件
        for file_path in UPLOADS_DIR.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_timestamp:
                try:
                    file_path.unlink()
                    files_cleaned += 1
                    logger.debug(f"清理文件: {file_path}")
                except Exception as e:
                    logger.error(f"清理文件失败 {file_path}: {e}")
        
        # 清理分析结果
        for result_path in ANALYSIS_RESULTS_DIR.rglob("*.json"):
            if result_path.is_file() and result_path.stat().st_mtime < cutoff_timestamp:
                try:
                    result_path.unlink()
                    results_cleaned += 1
                    logger.debug(f"清理分析结果: {result_path}")
                except Exception as e:
                    logger.error(f"清理分析结果失败 {result_path}: {e}")
        
        # 清理空目录
        self._cleanup_empty_directories(UPLOADS_DIR)
        self._cleanup_empty_directories(ANALYSIS_RESULTS_DIR)
        
        logger.info(f"清理完成: {files_cleaned} 个文件, {results_cleaned} 个分析结果")
        return files_cleaned, results_cleaned

    def _cleanup_empty_directories(self, base_dir: Path) -> None:
        """清理空目录
        
        Args:
            base_dir: 基础目录
        """
        for dir_path in sorted(base_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and dir_path != base_dir:
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        logger.debug(f"清理空目录: {dir_path}")
                except Exception as e:
                    logger.debug(f"清理空目录失败 {dir_path}: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息
        
        Returns:
            Dict: 存储统计信息
        """
        def get_dir_size(directory: Path) -> int:
            """计算目录大小"""
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        
        def count_files(directory: Path, pattern: str = "*") -> int:
            """计算文件数量"""
            return len(list(directory.rglob(pattern)))
        
        stats: Dict[str, Any] = {
            'uploads': {
                'total_files': count_files(UPLOADS_DIR),
                'total_size_bytes': get_dir_size(UPLOADS_DIR),
                'csv_files': count_files(UPLOADS_DIR, "*.csv"),
                'parquet_files': count_files(UPLOADS_DIR, "*.parquet")
            },
            'analysis_results': {
                'total_results': count_files(ANALYSIS_RESULTS_DIR, "*.json"),
                'total_size_bytes': get_dir_size(ANALYSIS_RESULTS_DIR)
            },
            'database': {
                'db_size_bytes': int(DATABASE_DIR.stat().st_size) if DATABASE_DIR.exists() else 0
            }
        }
        
        # 添加人类可读的大小
        for category in ['uploads', 'analysis_results']:
            size_bytes = stats[category]['total_size_bytes']
            stats[category]['total_size_human'] = self._format_bytes(size_bytes)
        
        db_size = stats['database']['db_size_bytes']
        stats['database']['db_size_human'] = self._format_bytes(db_size)
        
        return stats

    def _format_bytes(self, bytes_size: int) -> str:
        """格式化字节大小为人类可读格式
        
        Args:
            bytes_size: 字节大小
            
        Returns:
            str: 格式化后的大小字符串
        """
        size_float = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} PB"


# 全局文件存储管理器实例
file_storage_manager = FileStorageManager()