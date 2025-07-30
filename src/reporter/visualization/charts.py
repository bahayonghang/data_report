# 图表生成模块
# 使用 Plotly 生成交互式图表

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .theme import (
    get_chart_theme,
    get_color_sequence,
    get_single_color,
    apply_responsive_sizing,
    enhance_interactivity,
    get_hover_template,
    CORRELATION_COLORS,
)
from ..utils.performance import monitor_performance
from ..analysis.parallel_processor import AsyncVisualizationProcessor, optimize_dataframe_processing

# 配置日志
logger = logging.getLogger(__name__)


async def create_charts_parallel(df: pl.DataFrame, time_col: Optional[str], numeric_cols: List[str], 
                                correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
    """
    并行生成所有图表
    
    Args:
        df: 数据框
        time_col: 时间列名
        numeric_cols: 数值列列表
        correlation_matrix: 相关性矩阵
        
    Returns:
        包含所有图表的字典
    """
    logger.info("开始并行生成图表")
    
    # 优化数据框处理
    df_optimized = optimize_dataframe_processing(df)
    
    # 创建异步可视化处理器
    viz_processor = AsyncVisualizationProcessor()
    
    try:
        # 准备任务列表
        viz_tasks = []
        
        # 时间序列图 - 显示所有数值变量
        if time_col and len(numeric_cols) > 0:
            viz_tasks.append(('time_series', create_time_series_plot, (df_optimized, time_col, numeric_cols), {}))
        
        # 分布图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            viz_tasks.append(('distribution', create_distribution_plots, (df_optimized, numeric_cols), {}))
        
        # 箱形图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            viz_tasks.append(('box_plots', create_box_plots, (df_optimized, numeric_cols), {}))
        
        # 相关性热力图
        if correlation_matrix:
            viz_tasks.append(('correlation', create_correlation_heatmap, (correlation_matrix,), {}))
        
        # 并行执行任务
        results = await viz_processor.create_multiple_visualizations(viz_tasks)
        
        logger.info(f"并行图表生成完成，共生成 {len(results)} 个图表")
        return results
        
    except Exception as e:
        logger.error(f"并行图表生成失败: {e}")
        # 降级到串行处理
        return await _create_charts_fallback(df_optimized, time_col, numeric_cols, correlation_matrix)


async def _create_charts_fallback(df: pl.DataFrame, time_col: Optional[str], numeric_cols: List[str],
                                 correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
    """
    降级处理：串行生成图表
    
    Args:
        df: 数据框
        time_col: 时间列名
        numeric_cols: 数值列列表
        correlation_matrix: 相关性矩阵
        
    Returns:
        包含所有图表的字典
    """
    logger.warning("使用降级模式串行生成图表")
    
    results = {}
    
    try:
        # 时间序列图 - 显示所有数值变量
        if time_col and len(numeric_cols) > 0:
            results['time_series'] = create_time_series_plot(df, time_col, numeric_cols)
        
        # 分布图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            results['distribution'] = create_distribution_plots(df, numeric_cols)
        
        # 箱形图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            results['box_plots'] = create_box_plots(df, numeric_cols)
        
        # 相关性热力图
        if correlation_matrix and correlation_matrix.get("matrix"):
            try:
                corr_data = []
                matrix_data = correlation_matrix["matrix"]
                
                # 使用数值列名构建相关性矩阵
                for col1 in numeric_cols:
                    row: Dict[str, Any] = {"variable": col1}
                    for col2 in numeric_cols:
                        col1_data = matrix_data.get(col1, {})
                        if isinstance(col1_data, dict):
                            value = col1_data.get(col2, 0.0)
                            row[col2] = float(value) if value is not None else 0.0
                        else:
                            row[col2] = 0.0
                    corr_data.append(row)
                
                corr_df = pl.DataFrame(corr_data)
                results['correlation'] = create_correlation_heatmap(corr_df)
            except Exception as e:
                logger.error(f"转换相关性矩阵格式失败: {e}")
                results['correlation'] = {'error': f'相关性矩阵格式转换失败: {str(e)}'}
            
    except Exception as e:
        logger.error(f"降级图表生成也失败: {e}")
        results['error'] = str(e)
    
    return results


def create_charts_batch(df: pl.DataFrame, time_col: Optional[str], numeric_cols: List[str],
                       correlation_matrix: Optional[Dict[str, Any]] = None,
                       max_workers: int = 4) -> Dict[str, Any]:
    """
    批量并行生成图表（同步接口）
    
    Args:
        df: 数据框
        time_col: 时间列名
        numeric_cols: 数值列列表
        correlation_matrix: 相关性矩阵
        max_workers: 最大工作线程数
        
    Returns:
        包含所有图表的字典
    """
    logger.info(f"开始批量生成图表，使用 {max_workers} 个工作线程")
    
    # 优化数据框处理
    df_optimized = optimize_dataframe_processing(df)
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        future_to_chart = {}
        
        # 时间序列图 - 显示所有数值变量
        if time_col and len(numeric_cols) > 0:
            future = executor.submit(create_time_series_plot, df_optimized, time_col, numeric_cols)
            future_to_chart[future] = 'time_series'
        
        # 分布图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            future = executor.submit(create_distribution_plots, df_optimized, numeric_cols)
            future_to_chart[future] = 'distribution'
        
        # 箱形图 - 显示所有数值变量
        if len(numeric_cols) > 0:
            future = executor.submit(create_box_plots, df_optimized, numeric_cols)
            future_to_chart[future] = 'box_plots'
        
        # 相关性热力图
        if correlation_matrix and correlation_matrix.get("matrix"):
            # 将字典格式的相关性矩阵转换为DataFrame格式
            try:
                corr_data = []
                matrix_data = correlation_matrix["matrix"]
                
                # 使用数值列名构建相关性矩阵
                for col1 in numeric_cols:
                    row: Dict[str, Any] = {"variable": col1}
                    for col2 in numeric_cols:
                        col1_data = matrix_data.get(col1, {})
                        if isinstance(col1_data, dict):
                            value = col1_data.get(col2, 0.0)
                            row[col2] = float(value) if value is not None else 0.0
                        else:
                            row[col2] = 0.0
                    corr_data.append(row)
                
                corr_df = pl.DataFrame(corr_data)
                future = executor.submit(create_correlation_heatmap, corr_df)
                future_to_chart[future] = 'correlation'
            except Exception as e:
                logger.error(f"转换相关性矩阵格式失败: {e}")
                results['correlation'] = {'error': f'相关性矩阵格式转换失败: {str(e)}'}
        
        # 收集结果
        for future in as_completed(future_to_chart):
            chart_type = future_to_chart[future]
            try:
                result = future.result(timeout=30)  # 30秒超时
                results[chart_type] = result
                logger.info(f"{chart_type} 图表生成完成")
            except Exception as e:
                logger.error(f"{chart_type} 图表生成失败: {e}")
                results[chart_type] = {'error': str(e)}
    
    logger.info(f"批量图表生成完成，成功生成 {len([r for r in results.values() if 'error' not in r])} 个图表")
    return results

# 可视化配置常量
MAX_POINTS_FOR_VISUALIZATION = 10000  # 最大可视化点数
MAX_COLUMNS_FOR_HEATMAP = 50  # 热力图最大列数
SAMPLE_SIZE_LARGE_DATA = 5000  # 大数据集采样大小


def _sample_data_for_visualization(df: pl.DataFrame, max_points: int = MAX_POINTS_FOR_VISUALIZATION) -> pl.DataFrame:
    """为可视化采样数据以提高性能"""
    try:
        if df.height <= max_points:
            return df
        
        # 计算采样步长
        step = max(1, df.height // max_points)
        logger.info(f"数据量过大({df.height}行)，采样每{step}行用于可视化")
        
        # 使用简单的等间隔采样
        sample_count = min(max_points, (df.height + step - 1) // step)
        
        # 生成采样索引
        indices = list(range(0, df.height, step))[:sample_count]
        sampled_df = df[indices]
        
        # 如果采样结果太少，确保至少有一些数据
        if sampled_df.height < min(100, max_points // 10):
            sampled_df = df.head(max_points)
            
        logger.info(f"采样完成，从{df.height}行采样到{sampled_df.height}行")
        return sampled_df
    except Exception as e:
        logger.warning(f"数据采样失败: {e}，使用前{max_points}行数据")
        return df.head(max_points)


@monitor_performance
def create_time_series_plot(
    df: pl.DataFrame,
    time_col: str,
    value_cols: List[str],
    device_type: str = "desktop",
    size: str = "large",
) -> List[Dict]:
    """创建时序图表 - 为每个变量创建单独的图表"""
    plots = []
    
    try:
        # 输入验证
        if not value_cols:
            logger.warning("没有可用的数值列")
            return plots
        
        if time_col not in df.columns:
            logger.error(f"时间列 '{time_col}' 不存在")
            return plots
        
        # 过滤有效的数值列
        valid_cols = [col for col in value_cols if col in df.columns and col != time_col]
        if not valid_cols:
            logger.warning("没有有效的数值列")
            return plots
        
        # 数据采样以提高性能
        sampled_df = _sample_data_for_visualization(df)
        
        # 检查数据是否为空
        if sampled_df.height == 0:
            logger.warning("数据为空")
            return plots
        
        # 获取时间数据
        time_data = sampled_df[time_col].to_list()
        colors = get_color_sequence(len(valid_cols))
        
        # 调试信息：检查时间数据
        logger.info(f"时间数据样本: {time_data[:5] if len(time_data) > 0 else '空'}")
        logger.info(f"时间数据类型: {type(time_data[0]) if len(time_data) > 0 else '无'}")
        logger.info(f"采样后数据行数: {sampled_df.height}")
        
        # 为每个数值列创建单独的图表
        for i, col in enumerate(valid_cols):
            try:
                y_data = sampled_df[col].to_list()
                
                # 调试信息：检查数值数据
                logger.info(f"列 '{col}' 数据样本: {y_data[:5] if len(y_data) > 0 else '空'}")
                logger.info(f"列 '{col}' 非空值数量: {sum(1 for val in y_data if val is not None)}")
                
                # 检查数据有效性
                if not y_data or all(val is None for val in y_data):
                    logger.warning(f"列 '{col}' 数据为空，跳过")
                    continue
                
                # 创建单独的图表
                fig = go.Figure()
                
                fig.add_trace(
                    go.Scatter(
                        x=time_data,
                        y=y_data,
                        mode="lines+markers",
                        name=col,
                        line=dict(width=2.5, color=colors[i % len(colors)]),
                        marker=dict(size=4, color=colors[i % len(colors)]),
                        hovertemplate=get_hover_template("time_series", col),
                        showlegend=True
                    )
                )
                
                # 应用主题配置
                layout = get_chart_theme("time_series", "medium")  # 使用medium尺寸适配2列布局
                layout["title"]["text"] = f"{col}"  # 简化标题
                layout["yaxis"]["title"] = col
                layout["xaxis"]["title"] = "时间"
                layout["title"]["font"]["size"] = 14  # 减小标题字体
                
                # 应用响应式尺寸
                layout = apply_responsive_sizing(layout, device_type)
                
                fig.update_layout(layout)
                
                # 增强交互性
                fig_dict = fig.to_dict()
                fig_dict = enhance_interactivity(fig_dict)
                
                plots.append(fig_dict)
                
            except Exception as e:
                logger.warning(f"处理列 '{col}' 时出错: {e}")
                continue
        
        logger.info(f"成功创建 {len(plots)} 个时间序列图表")
        return plots
        
    except Exception as e:
        logger.error(f"创建时序图表失败: {e}")
        return plots


@monitor_performance
def create_correlation_heatmap(
    corr_matrix: pl.DataFrame, device_type: str = "desktop", size: str = "medium"
) -> Dict:
    """创建相关性热力图"""
    try:
        # 输入验证
        if corr_matrix.height == 0 or corr_matrix.width <= 1:
            return {"error": "相关性矩阵数据为空或无效"}
        
        # 检查矩阵大小，避免过大的热力图
        if corr_matrix.height > MAX_COLUMNS_FOR_HEATMAP:
            logger.warning(f"相关性矩阵过大({corr_matrix.height}x{corr_matrix.width})，截取前{MAX_COLUMNS_FOR_HEATMAP}列")
            corr_matrix = corr_matrix.head(MAX_COLUMNS_FOR_HEATMAP)
        
        # 将 Polars DataFrame 转换为 numpy 数组
        try:
            corr_values = corr_matrix.select(pl.exclude("variable")).to_numpy()
            column_names = corr_matrix.columns[1:]  # 排除第一列 variable
            variable_names = corr_matrix["variable"].to_list()
        except Exception as e:
            logger.error(f"转换相关性矩阵数据失败: {e}")
            return {"error": "相关性矩阵数据格式错误"}
        
        # 检查数据有效性
        if corr_values.size == 0:
            return {"error": "相关性矩阵数据为空"}
        
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_values,
                x=column_names,
                y=variable_names,
                colorscale=CORRELATION_COLORS,
                zmid=0,
                zmin=-1,
                zmax=1,
                colorbar=dict(title="相关系数", title_font=dict(size=12)),
                hovertemplate=get_hover_template("heatmap"),
                showscale=True,
            )
        )
        
        # 应用主题配置
        layout = get_chart_theme("heatmap", size)
        layout["title"]["text"] = "变量相关性热力图"
        
        # 应用响应式尺寸
        layout = apply_responsive_sizing(layout, device_type)
        
        fig.update_layout(layout)
        
        # 增强交互性
        fig_dict = fig.to_dict()
        fig_dict = enhance_interactivity(fig_dict)
        
        return fig_dict
        
    except Exception as e:
        logger.error(f"创建相关性热力图失败: {e}")
        return {"error": f"创建相关性热力图失败: {str(e)}"}


@monitor_performance
def create_distribution_plots(
    df: pl.DataFrame,
    columns: List[str],
    device_type: str = "desktop",
    size: str = "medium",
) -> List[Dict]:
    """创建分布直方图"""
    plots = []
    
    try:
        # 输入验证
        if not columns:
            logger.warning("没有提供列名")
            return plots
        
        # 数据采样以提高性能
        sampled_df = _sample_data_for_visualization(df)
        
        for i, col in enumerate(columns):
            try:
                # 检查列是否存在
                if col not in sampled_df.columns:
                    logger.warning(f"列 '{col}' 不存在，跳过")
                    continue
                
                # 获取非空数据
                data = sampled_df[col].drop_nulls().to_list()
                
                # 检查数据有效性
                if len(data) == 0:
                    logger.warning(f"列 '{col}' 没有有效数据，跳过")
                    continue
                
                # 检查数据类型（应该是数值型）
                if not all(isinstance(x, (int, float)) for x in data[:100]):  # 检查前100个值
                    logger.warning(f"列 '{col}' 包含非数值数据，跳过")
                    continue
                
                color = get_single_color(i)
                
                # 动态调整bin数量
                nbins = min(30, max(10, len(data) // 100))
                
                fig = go.Figure(
                    data=[
                        go.Histogram(
                            x=data,
                            nbinsx=nbins,
                            name=col,
                            marker_color=color,
                            opacity=0.8,
                            marker_line=dict(width=1, color="white"),
                            hovertemplate=get_hover_template("histogram", col),
                        )
                    ]
                )
                
                # 应用主题配置
                layout = get_chart_theme("histogram", size)
                layout["title"]["text"] = f"{col} 分布直方图"
                layout["xaxis"]["title"] = col
                layout["yaxis"]["title"] = "频次"
                
                # 应用响应式尺寸
                layout = apply_responsive_sizing(layout, device_type)
                
                fig.update_layout(layout)
                
                # 增强交互性
                fig_dict = fig.to_dict()
                fig_dict = enhance_interactivity(fig_dict)
                
                plots.append(fig_dict)
                
            except Exception as e:
                logger.warning(f"创建列 '{col}' 的分布图失败: {e}")
                continue
        
        return plots
        
    except Exception as e:
        logger.error(f"创建分布图失败: {e}")
        return plots


@monitor_performance
def create_box_plots(
    df: pl.DataFrame,
    columns: List[str],
    device_type: str = "desktop",
    size: str = "medium",
) -> List[Dict]:
    """创建箱形图"""
    plots = []
    
    try:
        # 输入验证
        if not columns:
            logger.warning("没有提供列名")
            return plots
        
        # 数据采样以提高性能
        sampled_df = _sample_data_for_visualization(df)
        
        for i, col in enumerate(columns):
            try:
                # 检查列是否存在
                if col not in sampled_df.columns:
                    logger.warning(f"列 '{col}' 不存在，跳过")
                    continue
                
                # 获取非空数据
                data = sampled_df[col].drop_nulls().to_list()
                
                # 检查数据有效性
                if len(data) == 0:
                    logger.warning(f"列 '{col}' 没有有效数据，跳过")
                    continue
                
                # 检查数据类型（应该是数值型）
                if not all(isinstance(x, (int, float)) for x in data[:100]):  # 检查前100个值
                    logger.warning(f"列 '{col}' 包含非数值数据，跳过")
                    continue
                
                # 检查数据量是否足够绘制箱形图
                if len(data) < 5:
                    logger.warning(f"列 '{col}' 数据量不足({len(data)}个)，跳过")
                    continue
                
                color = get_single_color(i)
                
                fig = go.Figure(
                    data=[
                        go.Box(
                            y=data,
                            name=col,
                            marker_color=color,
                            boxpoints="outliers",  # 显示异常值点
                            boxmean=True,  # 显示均值
                            hovertemplate=get_hover_template("box", col),
                            fillcolor=color,
                            line=dict(color=color, width=2),
                        )
                    ]
                )
                
                # 应用主题配置
                layout = get_chart_theme("box", size)
                layout["title"]["text"] = f"{col} 箱形图"
                layout["yaxis"]["title"] = col
                
                # 应用响应式尺寸
                layout = apply_responsive_sizing(layout, device_type)
                
                fig.update_layout(layout)
                
                # 增强交互性
                fig_dict = fig.to_dict()
                fig_dict = enhance_interactivity(fig_dict)
                
                plots.append(fig_dict)
                
            except Exception as e:
                logger.warning(f"创建列 '{col}' 的箱形图失败: {e}")
                continue
        
        return plots
        
    except Exception as e:
        logger.error(f"创建箱形图失败: {e}")
        return plots


def create_summary_dashboard(
    df: pl.DataFrame,
    time_col: str,
    numeric_cols: List[str],
    corr_matrix: pl.DataFrame,
    device_type: str = "desktop",
) -> Dict:
    """创建综合仪表板"""
    # 创建子图布局
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("时间序列概览", "相关性热力图", "数据分布概览", "异常值检测"),
        specs=[
            [{"secondary_y": False}, {"type": "heatmap"}],
            [{"type": "histogram"}, {"type": "box"}],
        ],
        horizontal_spacing=0.1,
        vertical_spacing=0.15,
    )

    colors = get_color_sequence(len(numeric_cols))

    # 时间序列 (只显示前3个变量以避免过于拥挤)
    display_cols = numeric_cols[:3] if len(numeric_cols) > 3 else numeric_cols
    time_data = df[time_col].to_list()  # 改为to_list()

    for i, col in enumerate(display_cols):
        fig.add_trace(
            go.Scatter(
                x=time_data,
                y=df[col].to_list(),  # 改为to_list()
                name=col,
                mode="lines",
                line=dict(width=2, color=colors[i % len(colors)]),
                hovertemplate=get_hover_template("time_series", col),
            ),
            row=1,
            col=1,
        )

    # 相关性热力图
    if corr_matrix.shape[0] > 1:
        corr_values = corr_matrix.select(pl.exclude("variable")).to_numpy()
        column_names = corr_matrix.columns[1:]

        fig.add_trace(
            go.Heatmap(
                z=corr_values,
                x=column_names,
                y=corr_matrix["variable"].to_list(),
                colorscale=CORRELATION_COLORS,
                zmid=0,
                zmin=-1,
                zmax=1,
                showscale=False,
                hovertemplate=get_hover_template("heatmap"),
            ),
            row=1,
            col=2,
        )

    # 数据分布 (第一个数值列)
    if numeric_cols:
        first_col = numeric_cols[0]
        data = df[first_col].drop_nulls().to_list()  # 改为to_list()
        fig.add_trace(
            go.Histogram(
                x=data,
                name=f"{first_col}分布",
                marker_color=colors[0],
                opacity=0.8,
                showlegend=False,
                hovertemplate=get_hover_template("histogram", first_col),
            ),
            row=2,
            col=1,
        )

    # 箱形图 (第一个数值列)
    if numeric_cols:
        first_col = numeric_cols[0]
        data = df[first_col].drop_nulls().to_list()  # 改为to_list()
        fig.add_trace(
            go.Box(
                y=data,
                name=f"{first_col}异常值",
                marker_color=colors[0],
                boxpoints="outliers",
                showlegend=False,
                hovertemplate=get_hover_template("box", first_col),
            ),
            row=2,
            col=2,
        )

    # 应用主题配置
    layout = get_chart_theme("dashboard", "dashboard")
    layout["title"]["text"] = "数据分析仪表板"

    # 应用响应式尺寸
    layout = apply_responsive_sizing(layout, device_type)

    fig.update_layout(layout)

    # 增强交互性
    fig_dict = fig.to_dict()
    fig_dict = enhance_interactivity(fig_dict)

    return fig_dict


def create_advanced_time_series(
    df: pl.DataFrame,
    time_col: str,
    value_cols: List[str],
    show_trend: bool = True,
    device_type: str = "desktop",
) -> Dict:
    """创建高级时序图表（包含趋势线）"""
    if not value_cols:
        return {"error": "没有可用的数值列"}

    fig = go.Figure()
    time_data = df[time_col].to_list()  # 改为to_list()
    colors = get_color_sequence(len(value_cols))

    for i, col in enumerate(value_cols):
        if col != time_col:
            y_data = df[col].to_list()  # 改为to_list()

            # 主要数据线
            fig.add_trace(
                go.Scatter(
                    x=time_data,
                    y=y_data,
                    mode="lines+markers",
                    name=col,
                    line=dict(width=2.5, color=colors[i % len(colors)]),
                    marker=dict(size=4),
                    hovertemplate=get_hover_template("time_series", col),
                )
            )

            # 可选的趋势线
            if show_trend and len(y_data) > 10:
                # 简单移动平均线
                window_size = min(30, len(y_data) // 10)
                if window_size > 2:
                    trend_data = df.select(
                        pl.col(col).rolling_mean(window_size).alias("trend")
                    )["trend"].to_list()  # 改为to_list()

                    fig.add_trace(
                        go.Scatter(
                            x=time_data,
                            y=trend_data,
                            mode="lines",
                            name=f"{col} 趋势",
                            line=dict(
                                width=3, color=colors[i % len(colors)], dash="dash"
                            ),
                            opacity=0.7,
                            hovertemplate=f"<b>{col} 趋势</b><br>时间: %{{x}}<br>数值: %{{y:.2f}}<extra></extra>",
                        )
                    )

    # 应用主题配置
    layout = get_chart_theme("time_series", "large")
    layout["title"]["text"] = "高级时间序列分析"

    # 应用响应式尺寸
    layout = apply_responsive_sizing(layout, device_type)

    fig.update_layout(layout)

    # 增强交互性
    fig_dict = fig.to_dict()
    fig_dict = enhance_interactivity(fig_dict)

    return fig_dict
