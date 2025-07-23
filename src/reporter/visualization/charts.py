# 图表生成模块
# 使用 Plotly 生成交互式图表

import polars as pl
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List
from .theme import (
    get_chart_theme,
    get_color_sequence,
    get_single_color,
    apply_responsive_sizing,
    enhance_interactivity,
    get_hover_template,
    CORRELATION_COLORS,
)


def create_time_series_plot(
    df: pl.DataFrame,
    time_col: str,
    value_cols: List[str],
    device_type: str = "desktop",
    size: str = "large",
) -> Dict:
    """创建时序图表"""
    if not value_cols:
        return {"error": "没有可用的数值列"}

    fig = go.Figure()

    # 获取时间数据
    time_data = df[time_col].to_numpy()
    colors = get_color_sequence(len(value_cols))

    # 为每个数值列添加一条线
    for i, col in enumerate(value_cols):
        if col != time_col:  # 确保不包含时间列本身
            y_data = df[col].to_numpy()
            fig.add_trace(
                go.Scatter(
                    x=time_data,
                    y=y_data,
                    mode="lines+markers",
                    name=col,
                    line=dict(width=2.5, color=colors[i % len(colors)]),
                    marker=dict(size=4, color=colors[i % len(colors)]),
                    hovertemplate=get_hover_template("time_series", col),
                )
            )

    # 应用主题配置
    layout = get_chart_theme("time_series", size)
    layout["title"]["text"] = "时间序列趋势图"

    # 应用响应式尺寸
    layout = apply_responsive_sizing(layout, device_type)

    fig.update_layout(layout)

    # 增强交互性
    fig_dict = fig.to_dict()
    fig_dict = enhance_interactivity(fig_dict)

    return fig_dict


def create_correlation_heatmap(
    corr_matrix: pl.DataFrame, device_type: str = "desktop", size: str = "medium"
) -> Dict:
    """创建相关性热力图"""
    # 将 Polars DataFrame 转换为 numpy 数组
    corr_values = corr_matrix.select(pl.exclude("variable")).to_numpy()
    column_names = corr_matrix.columns[1:]  # 排除第一列 variable

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_values,
            x=column_names,
            y=corr_matrix["variable"].to_list(),
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


def create_distribution_plots(
    df: pl.DataFrame,
    columns: List[str],
    device_type: str = "desktop",
    size: str = "medium",
) -> List[Dict]:
    """创建分布直方图"""
    plots = []

    for i, col in enumerate(columns):
        # 获取非空数据
        data = df[col].drop_nulls().to_numpy()

        if len(data) == 0:
            continue

        color = get_single_color(i)

        fig = go.Figure(
            data=[
                go.Histogram(
                    x=data,
                    nbinsx=30,
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

    return plots


def create_box_plots(
    df: pl.DataFrame,
    columns: List[str],
    device_type: str = "desktop",
    size: str = "medium",
) -> List[Dict]:
    """创建箱形图"""
    plots = []

    for i, col in enumerate(columns):
        # 获取非空数据
        data = df[col].drop_nulls().to_numpy()

        if len(data) == 0:
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
    time_data = df[time_col].to_numpy()

    for i, col in enumerate(display_cols):
        fig.add_trace(
            go.Scatter(
                x=time_data,
                y=df[col].to_numpy(),
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
        data = df[first_col].drop_nulls().to_numpy()
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
        data = df[first_col].drop_nulls().to_numpy()
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
    time_data = df[time_col].to_numpy()
    colors = get_color_sequence(len(value_cols))

    for i, col in enumerate(value_cols):
        if col != time_col:
            y_data = df[col].to_numpy()

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
                    )["trend"].to_numpy()

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
