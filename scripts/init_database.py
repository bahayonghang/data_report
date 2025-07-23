#!/usr/bin/env python3
"""数据库初始化脚本

用于初始化SQLite数据库和创建必要的表结构
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reporter.database import DatabaseManager
from src.reporter.file_manager import file_storage_manager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_database():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 初始化数据库
        await db_manager.init_database()
        
        logger.info("数据库初始化完成")
        
        # 显示存储统计信息
        stats = file_storage_manager.get_storage_stats()
        logger.info(f"存储统计信息: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


async def reset_database():
    """重置数据库（删除所有数据）"""
    try:
        logger.warning("开始重置数据库...")
        
        # 创建数据库管理器实例
        db_manager = DatabaseManager()
        
        # 删除数据库文件
        db_path = Path("data/database/data_report.db")
        if db_path.exists():
            db_path.unlink()
            logger.info(f"删除数据库文件: {db_path}")
        
        # 重新初始化
        await db_manager.init_database()
        
        logger.info("数据库重置完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库重置失败: {e}")
        return False


async def check_database():
    """检查数据库状态"""
    try:
        logger.info("检查数据库状态...")
        
        db_manager = DatabaseManager()
        
        # 检查数据库文件是否存在
        db_path = Path("data/database/data_report.db")
        if not db_path.exists():
            logger.warning("数据库文件不存在")
            return False
        
        # 尝试连接数据库
        await db_manager.init_database()
        
        # 获取统计信息
        # 这里可以添加更多的检查逻辑
        logger.info("数据库状态正常")
        
        # 显示存储统计
        stats = file_storage_manager.get_storage_stats()
        logger.info(f"存储统计: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库检查失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('action', choices=['init', 'reset', 'check'], 
                       help='要执行的操作')
    parser.add_argument('--force', action='store_true', 
                       help='强制执行操作（用于reset）')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        success = asyncio.run(init_database())
    elif args.action == 'reset':
        if not args.force:
            confirm = input("确定要重置数据库吗？这将删除所有数据！(y/N): ")
            if confirm.lower() != 'y':
                logger.info("操作已取消")
                return
        success = asyncio.run(reset_database())
    elif args.action == 'check':
        success = asyncio.run(check_database())
    else:
        logger.error(f"未知操作: {args.action}")
        success = False
    
    if success:
        logger.info("操作完成")
        sys.exit(0)
    else:
        logger.error("操作失败")
        sys.exit(1)


if __name__ == '__main__':
    main()