#!/usr/bin/env python3
"""
数据报告生成器主入口

这是应用程序的主入口点，负责：n1. 初始化配置和日志
2. 解析命令行参数
3. 协调各个模块的工作
4. 处理错误和异常
"""

import sys
import argparse
import logging
import asyncio
from pathlib import Path

from .config import get_settings, config_manager
from .tasks.task_manager import TaskManager
from .logging_config import setup_logging


def setup_application() -> None:
    """初始化应用程序
    
    设置日志、配置和性能监控
    """
    try:
        # 获取设置并设置日志
        get_settings()
        setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("应用程序初始化完成")
        
    except Exception as e:
        print(f"应用程序初始化失败: {e}", file=sys.stderr)
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="数据报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s data.csv --output report.json
  %(prog)s data.xlsx --format yaml --charts
  %(prog)s data.parquet --config custom.json --parallel 8
        """
    )
    
    # 输入文件
    parser.add_argument(
        "input_file",
        type=str,
        help="输入数据文件路径 (支持 CSV, Excel, Parquet 格式)"
    )
    
    # 输出选项
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument(
        "-o", "--output",
        type=str,
        help="输出文件路径 (默认: 自动生成)"
    )
    output_group.add_argument(
        "-f", "--format",
        choices=["json", "yaml", "csv", "excel"],
        default="json",
        help="输出格式 (默认: json)"
    )
    output_group.add_argument(
        "--charts",
        action="store_true",
        help="生成图表"
    )
    output_group.add_argument(
        "--chart-format",
        choices=["png", "jpg", "svg", "pdf"],
        default="png",
        help="图表格式 (默认: png)"
    )
    
    # 分析选项
    analysis_group = parser.add_argument_group("分析选项")
    analysis_group.add_argument(
        "--correlation",
        action="store_true",
        help="启用相关性分析"
    )
    analysis_group.add_argument(
        "--time-series",
        action="store_true",
        help="启用时间序列分析"
    )
    analysis_group.add_argument(
        "--outliers",
        action="store_true",
        help="启用异常值检测"
    )
    analysis_group.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.7,
        help="相关性阈值 (默认: 0.7)"
    )
    
    # 性能选项
    performance_group = parser.add_argument_group("性能选项")
    performance_group.add_argument(
        "-p", "--parallel",
        type=int,
        help="并行工作进程数 (默认: 自动检测)"
    )
    performance_group.add_argument(
        "--chunk-size",
        type=int,
        help="数据块大小 (MB) (默认: 100)"
    )
    performance_group.add_argument(
        "--memory-limit",
        type=int,
        help="内存使用限制 (MB) (默认: 2048)"
    )
    performance_group.add_argument(
        "--profile",
        action="store_true",
        help="启用性能分析"
    )
    
    # 配置选项
    config_group = parser.add_argument_group("配置选项")
    config_group.add_argument(
        "-c", "--config",
        type=str,
        help="配置文件路径"
    )
    config_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="日志级别"
    )
    config_group.add_argument(
        "--cache",
        action="store_true",
        help="启用缓存"
    )
    config_group.add_argument(
        "--no-cache",
        action="store_true",
        help="禁用缓存"
    )
    
    # 其他选项
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """验证命令行参数
    
    Args:
        args: 解析后的参数
        
    Returns:
        参数是否有效
    """
    logger = logging.getLogger(__name__)
    
    # 检查输入文件
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        return False
    
    if not input_path.is_file():
        logger.error(f"输入路径不是文件: {input_path}")
        return False
    
    # 检查文件格式
    supported_extensions = {".csv", ".xlsx", ".xls", ".parquet", ".json"}
    if input_path.suffix.lower() not in supported_extensions:
        logger.error(f"不支持的文件格式: {input_path.suffix}")
        logger.error(f"支持的格式: {', '.join(supported_extensions)}")
        return False
    
    # 检查输出目录
    if args.output:
        output_path = Path(args.output)
        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建输出目录: {output_dir}")
            except Exception as e:
                logger.error(f"无法创建输出目录 {output_dir}: {e}")
                return False
    
    # 检查配置文件
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return False
    
    # 检查参数冲突
    if args.verbose and args.quiet:
        logger.error("--verbose 和 --quiet 不能同时使用")
        return False
    
    if args.cache and args.no_cache:
        logger.error("--cache 和 --no-cache 不能同时使用")
        return False
    
    # 检查数值参数
    if args.parallel and args.parallel <= 0:
        logger.error("并行进程数必须大于 0")
        return False
    
    if args.chunk_size and args.chunk_size <= 0:
        logger.error("数据块大小必须大于 0")
        return False
    
    if args.memory_limit and args.memory_limit <= 0:
        logger.error("内存限制必须大于 0")
        return False
    
    if args.correlation_threshold and not (0 <= args.correlation_threshold <= 1):
        logger.error("相关性阈值必须在 0 到 1 之间")
        return False
    
    return True


def apply_cli_overrides(args: argparse.Namespace) -> None:
    """应用命令行参数覆盖配置
    
    Args:
        args: 解析后的参数
    """
    logger = logging.getLogger(__name__)
    
    # 加载自定义配置文件
    if args.config:
        try:
            config_data = config_manager._load_config_file(Path(args.config))
            config_manager._merge_config(config_data)
            logger.info(f"加载配置文件: {args.config}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    # 应用命令行覆盖
    overrides = {}
    
    # 输出设置
    if args.format:
        overrides['output.format'] = args.format
    if args.charts:
        overrides['output.include_charts'] = True
    if args.chart_format:
        overrides['output.chart_format'] = args.chart_format
    
    # 分析设置
    if args.correlation:
        overrides['analysis.enable_correlation'] = True
    if args.time_series:
        overrides['analysis.enable_time_series'] = True
    if args.outliers:
        overrides['analysis.enable_outlier_detection'] = True
    if args.correlation_threshold:
        overrides['analysis.correlation_threshold'] = args.correlation_threshold
    
    # 性能设置
    if args.parallel:
        overrides['data_processing.parallel_workers'] = args.parallel
    if args.chunk_size:
        overrides['data_processing.chunk_size_mb'] = args.chunk_size
    if args.memory_limit:
        overrides['data_processing.max_memory_usage_mb'] = args.memory_limit
    if args.profile:
        overrides['performance.enable_profiling'] = True
    
    # 缓存设置
    if args.cache:
        overrides['data_processing.enable_caching'] = True
    elif args.no_cache:
        overrides['data_processing.enable_caching'] = False
    
    # 日志设置
    if args.log_level:
        overrides['logging.level'] = args.log_level
    elif args.verbose:
        overrides['logging.level'] = 'DEBUG'
    elif args.quiet:
        overrides['logging.level'] = 'WARNING'
    
    # 应用覆盖
    for key, value in overrides.items():
        config_manager.set(key, value)
        logger.debug(f"覆盖配置: {key} = {value}")


async def run_analysis(args: argparse.Namespace) -> bool:
    """运行数据分析
    
    Args:
        args: 解析后的参数
        
    Returns:
        是否成功
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化任务管理器
        logger.info(f"初始化任务管理器: {args.input_file}")
        task_manager = TaskManager()
        
        # 执行数据分析任务
        logger.info("开始数据分析")
        logger.info("开始创建分析任务")
        task_id = await task_manager.create_task(
            task_type="data_analysis",
            input_path=args.input_file,
            output_format=args.format
        )
        
        # 等待任务完成
        while True:
            task_info = await task_manager.get_task_info(task_id)
            if task_info and task_info.status.value in ['completed', 'failed', 'cancelled']:
                break
            await asyncio.sleep(1)
        
        if task_info.status.value != 'completed':
            logger.error(f"数据分析失败: {task_info.error_message}")
            return False
        
        results = task_info.result_path
        
        logger.info("数据分析完成")
        
        # 保存结果
        logger.info("开始保存结果")
        
        output_path = args.output
        if not output_path:
            # 生成默认输出路径
            input_path = Path(args.input_file)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{input_path.stem}_analysis_{timestamp}.{args.format}"
        
        # 简单保存结果
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_path}")
        
        logger.info("分析完成")
        return True
        
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        return False
    except Exception as e:
        logger.error(f"分析过程中发生错误: {e}", exc_info=True)
        return False


async def main() -> int:
    """主函数
    
    Returns:
        退出代码 (0: 成功, 1: 失败)
    """
    try:
        # 初始化应用程序
        setup_application()
        
        # 解析命令行参数
        args = parse_arguments()
        
        # 验证参数
        if not validate_arguments(args):
            return 1
        
        # 应用命令行覆盖
        apply_cli_overrides(args)
        
        # 运行分析
        success = await run_analysis(args)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"程序执行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))