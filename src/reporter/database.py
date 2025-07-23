"""数据库模块

负责：
- SQLite数据库连接管理
- 文件和分析记录的数据模型
- 数据库操作（CRUD）
- 数据库初始化和迁移
"""

import aiosqlite
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = Path("data/database/history.db")


@dataclass
class FileRecord:
    """文件记录数据模型"""
    id: Optional[int] = None
    filename: str = ""
    original_filename: str = ""
    file_hash: str = ""
    file_size: int = 0
    file_type: str = ""
    upload_time: Optional[datetime] = None
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        if self.upload_time:
            data['upload_time'] = self.upload_time.isoformat()
        return data


@dataclass
class AnalysisRecord:
    """分析记录数据模型"""
    id: Optional[int] = None
    file_id: int = 0
    analysis_time: Optional[datetime] = None
    analysis_result: str = ""  # JSON字符串
    result_file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        if self.analysis_time:
            data['analysis_time'] = self.analysis_time.isoformat()
        # 解析JSON结果
        try:
            data['analysis_result'] = json.loads(self.analysis_result)
        except (json.JSONDecodeError, TypeError):
            data['analysis_result'] = {}
        return data


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def init_database(self) -> None:
        """初始化数据库表结构"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建文件信息表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL
                )
            """)

            # 创建分析记录表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analysis_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    analysis_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    analysis_result TEXT NOT NULL,
                    result_file_path TEXT NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files(id)
                )
            """)

            # 创建索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_files_upload_time ON files(upload_time)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_time ON analysis_records(analysis_time)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_analysis_file_id ON analysis_records(file_id)")

            await db.commit()
            logger.info("数据库初始化完成")

    async def add_file_record(self, file_record: FileRecord) -> int:
        """添加文件记录
        
        Args:
            file_record: 文件记录对象
            
        Returns:
            int: 新插入记录的ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO files (filename, original_filename, file_hash, file_size, file_type, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                file_record.filename,
                file_record.original_filename,
                file_record.file_hash,
                file_record.file_size,
                file_record.file_type,
                file_record.file_path
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_file_by_hash(self, file_hash: str) -> Optional[FileRecord]:
        """根据文件哈希查找文件记录
        
        Args:
            file_hash: 文件SHA256哈希值
            
        Returns:
            Optional[FileRecord]: 文件记录，如果不存在则返回None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM files WHERE file_hash = ?", (file_hash,)
            )
            row = await cursor.fetchone()
            if row:
                return FileRecord(
                    id=row['id'],
                    filename=row['filename'],
                    original_filename=row['original_filename'],
                    file_hash=row['file_hash'],
                    file_size=row['file_size'],
                    file_type=row['file_type'],
                    upload_time=datetime.fromisoformat(row['upload_time']),
                    file_path=row['file_path']
                )
            return None

    async def add_analysis_record(self, analysis_record: AnalysisRecord) -> int:
        """添加分析记录
        
        Args:
            analysis_record: 分析记录对象
            
        Returns:
            int: 新插入记录的ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO analysis_records (file_id, analysis_result, result_file_path)
                VALUES (?, ?, ?)
            """, (
                analysis_record.file_id,
                analysis_record.analysis_result,
                analysis_record.result_file_path
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_latest_analysis_by_file_id(self, file_id: int) -> Optional[AnalysisRecord]:
        """获取文件的最新分析记录
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[AnalysisRecord]: 最新的分析记录
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM analysis_records 
                WHERE file_id = ? 
                ORDER BY analysis_time DESC 
                LIMIT 1
            """, (file_id,))
            row = await cursor.fetchone()
            if row:
                     return AnalysisRecord(
                         id=row['id'],
                         file_id=row['file_id'],
                         analysis_time=datetime.fromisoformat(row['analysis_time']),
                         analysis_result=row['analysis_result'],
                         result_file_path=row['result_file_path']
                     )
            return None

    async def get_file_history(self, limit: int = 50, offset: int = 0, 
                              file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取文件历史记录
        
        Args:
            limit: 返回记录数限制
            offset: 偏移量
            file_type: 文件类型筛选（csv/parquet）
            
        Returns:
            List[Dict]: 文件历史记录列表
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # 构建查询条件
            where_clause = ""
            params = []
            if file_type:
                where_clause = "WHERE f.file_type = ?"
                params.append(file_type)
            
            query = f"""
                SELECT f.*, 
                       COUNT(ar.id) as analysis_count,
                       MAX(ar.analysis_time) as last_analysis_time
                FROM files f
                LEFT JOIN analysis_records ar ON f.id = ar.file_id
                {where_clause}
                GROUP BY f.id
                ORDER BY f.upload_time DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            result = []
            for row in rows:
                file_data = {
                    'id': row['id'],
                    'filename': row['filename'],
                    'original_filename': row['original_filename'],
                    'file_hash': row['file_hash'],
                    'file_size': row['file_size'],
                    'file_type': row['file_type'],
                    'upload_time': row['upload_time'],
                    'file_path': row['file_path'],
                    'analysis_count': row['analysis_count'],
                    'last_analysis_time': row['last_analysis_time']
                }
                result.append(file_data)
            
            return result

    async def search_files(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索文件
        
        Args:
            query: 搜索关键词
            limit: 返回记录数限制
            
        Returns:
            List[Dict]: 匹配的文件记录
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            search_pattern = f"%{query}%"
            cursor = await db.execute("""
                SELECT f.*, 
                       COUNT(ar.id) as analysis_count,
                       MAX(ar.analysis_time) as last_analysis_time
                FROM files f
                LEFT JOIN analysis_records ar ON f.id = ar.file_id
                WHERE f.original_filename LIKE ? OR f.filename LIKE ?
                GROUP BY f.id
                ORDER BY f.upload_time DESC
                LIMIT ?
            """, (search_pattern, search_pattern, limit))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_analysis_result_path(self, analysis_id: int, result_file_path: str) -> bool:
        """更新分析记录的结果文件路径
        
        Args:
            analysis_id: 分析ID
            result_file_path: 结果文件路径
            
        Returns:
            bool: 是否更新成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE analysis_records SET result_file_path = ? WHERE id = ?",
                    (result_file_path, analysis_id)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"更新分析结果路径失败: {e}")
            return False

    async def get_file_record(self, file_id: int) -> Optional[FileRecord]:
        """根据ID获取文件记录
        
        Args:
            file_id: 文件ID
            
        Returns:
            Optional[FileRecord]: 文件记录，如果不存在则返回None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM files WHERE id = ?",
                    (file_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return FileRecord(
                        id=row['id'],
                        filename=row['filename'],
                        original_filename=row['original_filename'],
                        file_hash=row['file_hash'],
                        file_size=row['file_size'],
                        file_type=row['file_type'],
                        upload_time=datetime.fromisoformat(row['upload_time']),
                        file_path=row['file_path']
                    )
                return None
        except Exception as e:
            logger.error(f"获取文件记录失败: {e}")
            return None

    async def get_file_record_by_filename(self, filename: str) -> Optional[FileRecord]:
        """根据文件名获取文件记录
        
        Args:
            filename: 文件名
            
        Returns:
            Optional[FileRecord]: 文件记录，如果不存在则返回None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM files WHERE filename = ? OR original_filename = ? ORDER BY upload_time DESC LIMIT 1",
                    (filename, filename)
                )
                row = await cursor.fetchone()
                
                if row:
                    return FileRecord(
                        id=row['id'],
                        filename=row['filename'],
                        original_filename=row['original_filename'],
                        file_hash=row['file_hash'],
                        file_size=row['file_size'],
                        file_type=row['file_type'],
                        upload_time=datetime.fromisoformat(row['upload_time']),
                        file_path=row['file_path']
                    )
                return None
        except Exception as e:
            logger.error(f"根据文件名获取文件记录失败: {e}")
            return None

    async def get_analysis_record(self, analysis_id: int) -> Optional[AnalysisRecord]:
        """根据ID获取分析记录
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            Optional[AnalysisRecord]: 分析记录，如果不存在则返回None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM analysis_records WHERE id = ?",
                    (analysis_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return AnalysisRecord(
                        id=row['id'],
                        file_id=row['file_id'],
                        analysis_time=datetime.fromisoformat(row['analysis_time']),
                        analysis_result=row['analysis_result'],
                        result_file_path=row['result_file_path']
                    )
                return None
        except Exception as e:
            logger.error(f"获取分析记录失败: {e}")
            return None

    async def get_file_analysis_history(self, file_id: int) -> List[Dict[str, Any]]:
        """获取文件的分析历史记录
        
        Args:
            file_id: 文件ID
            
        Returns:
            List[Dict]: 分析历史记录列表
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                     """
                     SELECT * FROM analysis_records 
                     WHERE file_id = ? 
                     ORDER BY analysis_time DESC
                     """,
                     (file_id,)
                 )
                rows = await cursor.fetchall()
                
                return [
                     {
                         'id': row['id'],
                         'file_id': row['file_id'],
                         'analysis_time': row['analysis_time'],
                         'analysis_result': row['analysis_result'],
                         'result_file_path': row['result_file_path']
                     }
                     for row in rows
                 ]
        except Exception as e:
            logger.error(f"获取文件分析历史失败: {e}")
            return []

    async def delete_file_record(self, file_id: int) -> bool:
        """删除文件记录及其相关分析记录
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 删除是否成功
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 删除相关分析记录
            await db.execute("DELETE FROM analysis_records WHERE file_id = ?", (file_id,))
            # 删除文件记录
            cursor = await db.execute("DELETE FROM files WHERE id = ?", (file_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def delete_analysis_record(self, analysis_id: int) -> bool:
        """删除分析记录
        
        Args:
            analysis_id: 分析ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM analysis_records WHERE id = ?",
                    (analysis_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"删除分析记录失败: {e}")
            return False


def calculate_file_hash(file_content: bytes) -> str:
    """计算文件的SHA256哈希值
    
    Args:
        file_content: 文件内容字节
        
    Returns:
        str: SHA256哈希值
    """
    return hashlib.sha256(file_content).hexdigest()


# 全局数据库管理器实例
db_manager = DatabaseManager()