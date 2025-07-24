#!/usr/bin/env python3
"""
数据库路径分隔符修复脚本

将数据库中存储的Windows风格路径（使用反斜杠）转换为Unix风格路径（使用正斜杠）
这样可以确保在Linux系统上正确加载分析结果文件。
"""

import asyncio
import aiosqlite
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path("data/database/history.db")


async def fix_path_separators():
    """修复数据库中的路径分隔符"""
    if not DB_PATH.exists():
        logger.error(f"数据库文件不存在: {DB_PATH}")
        return
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # 查询所有包含反斜杠的分析记录
            cursor = await db.execute(
                "SELECT id, result_file_path FROM analysis_records WHERE result_file_path LIKE '%\\%'"
            )
            records = await cursor.fetchall()
            
            if not records:
                logger.info("没有找到需要修复的路径记录")
                return
            
            records_list = list(records)
            logger.info(f"找到 {len(records_list)} 条需要修复的记录")
            
            # 修复每条记录
            for record_id, old_path in records_list:
                # 将反斜杠替换为正斜杠
                new_path = old_path.replace('\\', '/')
                
                # 更新数据库记录
                await db.execute(
                    "UPDATE analysis_records SET result_file_path = ? WHERE id = ?",
                    (new_path, record_id)
                )
                
                logger.info(f"记录 {record_id}: {old_path} -> {new_path}")
            
            # 提交更改
            await db.commit()
            logger.info("所有路径分隔符修复完成")
            
    except Exception as e:
        logger.error(f"修复路径分隔符时出错: {e}")
        raise


async def verify_fixes():
    """验证修复结果"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # 检查是否还有反斜杠路径
            cursor = await db.execute(
                "SELECT COUNT(*) FROM analysis_records WHERE result_file_path LIKE '%\\%'"
            )
            count_result = await cursor.fetchone()
            
            if count_result and count_result[0] == 0:
                logger.info("✅ 验证通过：所有路径都已使用正确的分隔符")
            elif count_result:
                logger.warning(f"⚠️  仍有 {count_result[0]} 条记录使用反斜杠路径")
            else:
                logger.error("无法获取记录计数")
            
            # 显示所有分析记录的路径
            cursor = await db.execute(
                "SELECT id, result_file_path FROM analysis_records ORDER BY id"
            )
            records = await cursor.fetchall()
            
            logger.info("当前所有分析记录的路径:")
            for record_id, path in records:
                logger.info(f"  记录 {record_id}: {path}")
                
    except Exception as e:
        logger.error(f"验证修复结果时出错: {e}")


async def main():
    """主函数"""
    logger.info("开始修复数据库中的路径分隔符...")
    
    # 修复路径分隔符
    await fix_path_separators()
    
    # 验证修复结果
    await verify_fixes()
    
    logger.info("路径分隔符修复完成")


if __name__ == "__main__":
    asyncio.run(main())