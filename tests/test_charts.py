"""测试图表生成模块"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import polars as pl
import pytest
from datetime import datetime, timedelta
from src.reporter.visualization.charts import (
    create_time_series_plot,
    create_correlation_heatmap,
    create_distribution_plots,
    create_box_plots,
    create_summary_dashboard,
    create_advanced_time_series,
)
from src.reporter.visualization.theme import (
    get_chart_theme,
    get_color_sequence,
    apply_responsive_sizing,
    enhance_interactivity,
)


@pytest.fixture
def sample_data():
    """创建测试数据"""
    # 生成时间序列数据
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(100)]

    data = {
        "DateTime": dates,
        "temperature": [20 + 5 * (i % 10) for i in range(100)],
        "humidity": [50 + 10 * ((i + 5) % 8) for i in range(100)],
        "pressure": [1000 + 20 * ((i + 3) % 6) for i in range(100)],
    }

    return pl.DataFrame(data)


@pytest.fixture
def correlation_matrix():
    """创建相关性矩阵测试数据"""
    return pl.DataFrame(
        {
            "variable": ["temperature", "humidity", "pressure"],
            "temperature": [1.0, -0.5, 0.3],
            "humidity": [-0.5, 1.0, -0.2],
            "pressure": [0.3, -0.2, 1.0],
        }
    )


def test_create_time_series_plot(sample_data):
    """测试时序图表生成"""
    result = create_time_series_plot(
        sample_data, "DateTime", ["temperature", "humidity", "pressure"]
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "layout" in result
    assert "config" in result  # 新增的配置项
    assert result["layout"]["title"]["text"] == "时间序列趋势图"
    assert len(result["data"]) == 3  # 三条线

    # 测试响应式功能
    mobile_result = create_time_series_plot(
        sample_data, "DateTime", ["temperature"], device_type="mobile"
    )
    assert mobile_result["layout"]["width"] <= 400


def test_create_correlation_heatmap(correlation_matrix):
    """测试相关性热力图生成"""
    result = create_correlation_heatmap(correlation_matrix)

    assert isinstance(result, dict)
    assert "data" in result
    assert "layout" in result
    assert "config" in result
    assert result["layout"]["title"]["text"] == "变量相关性热力图"


def test_create_distribution_plots(sample_data):
    """测试分布直方图生成"""
    result = create_distribution_plots(sample_data, ["temperature", "humidity"])

    assert isinstance(result, list)
    assert len(result) == 2
    for plot in result:
        assert isinstance(plot, dict)
        assert "data" in plot
        assert "layout" in plot
        assert "config" in plot


def test_create_box_plots(sample_data):
    """测试箱形图生成"""
    result = create_box_plots(sample_data, ["temperature", "humidity"])

    assert isinstance(result, list)
    assert len(result) == 2
    for plot in result:
        assert isinstance(plot, dict)
        assert "data" in plot
        assert "layout" in plot
        assert "config" in plot


def test_create_summary_dashboard(sample_data, correlation_matrix):
    """测试综合仪表板生成"""
    result = create_summary_dashboard(
        sample_data,
        "DateTime",
        ["temperature", "humidity", "pressure"],
        correlation_matrix,
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "layout" in result
    assert "config" in result
    assert result["layout"]["title"]["text"] == "数据分析仪表板"


def test_create_advanced_time_series(sample_data):
    """测试高级时序图表生成"""
    result = create_advanced_time_series(
        sample_data, "DateTime", ["temperature", "humidity"], show_trend=True
    )

    assert isinstance(result, dict)
    assert "data" in result
    assert "layout" in result
    assert "config" in result
    assert result["layout"]["title"]["text"] == "高级时间序列分析"


def test_theme_functions():
    """测试主题函数"""
    # 测试主题配置
    theme = get_chart_theme("time_series", "medium")
    assert isinstance(theme, dict)
    assert "width" in theme
    assert "height" in theme
    assert "title" in theme

    # 测试颜色序列
    colors = get_color_sequence(5)
    assert len(colors) == 5
    assert all(isinstance(color, str) for color in colors)

    # 测试响应式尺寸
    layout = {"width": 800, "height": 600}
    mobile_layout = apply_responsive_sizing(layout, "mobile")
    assert mobile_layout["width"] <= 400

    # 测试交互性增强
    fig_dict = {"layout": {"xaxis": {"type": "date"}}}
    enhanced = enhance_interactivity(fig_dict)
    assert "config" in enhanced


def test_device_responsiveness():
    """测试设备响应式功能"""
    sample_df = pl.DataFrame({"DateTime": [datetime(2023, 1, 1)], "value": [10]})

    # 测试不同设备类型
    desktop_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], device_type="desktop"
    )
    tablet_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], device_type="tablet"
    )
    mobile_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], device_type="mobile"
    )

    # 验证尺寸递减
    assert (
        desktop_result["layout"]["width"]
        >= tablet_result["layout"]["width"]
        >= mobile_result["layout"]["width"]
    )


def test_size_options():
    """测试尺寸选项"""
    sample_df = pl.DataFrame({"DateTime": [datetime(2023, 1, 1)], "value": [10]})

    # 测试不同尺寸
    small_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], size="small"
    )
    medium_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], size="medium"
    )
    large_result = create_time_series_plot(
        sample_df, "DateTime", ["value"], size="large"
    )

    # 验证尺寸递增
    assert (
        small_result["layout"]["width"]
        <= medium_result["layout"]["width"]
        <= large_result["layout"]["width"]
    )


def test_enhanced_interactivity():
    """测试增强交互功能"""
    sample_df = pl.DataFrame(
        {"DateTime": [datetime(2023, 1, 1), datetime(2023, 1, 2)], "value": [10, 20]}
    )

    result = create_time_series_plot(sample_df, "DateTime", ["value"])

    # 验证配置存在
    assert "config" in result
    config = result["config"]

    # 验证交互配置
    assert config["responsive"] is True
    assert config["scrollZoom"] is True
    assert "modeBarButtonsToRemove" in config

    # 验证时序图特有的范围选择器
    assert "rangeslider" in result["layout"]["xaxis"]
    assert "rangeselector" in result["layout"]["xaxis"]


def test_empty_data_handling():
    """测试空数据处理"""
    empty_df = pl.DataFrame({"col1": []})

    # 测试分布图表
    result = create_distribution_plots(empty_df, ["col1"])
    assert result == []

    # 测试箱形图
    result = create_box_plots(empty_df, ["col1"])
    assert result == []


def test_time_series_no_value_cols(sample_data):
    """测试时序图表无数值列情况"""
    result = create_time_series_plot(sample_data, "DateTime", [])

    assert "error" in result
    assert result["error"] == "没有可用的数值列"


def test_color_consistency():
    """测试颜色一致性"""
    sample_df = pl.DataFrame(
        {
            "DateTime": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
            "temp1": [10, 20],
            "temp2": [15, 25],
        }
    )

    # 创建多个图表，验证颜色一致性
    time_series = create_time_series_plot(sample_df, "DateTime", ["temp1", "temp2"])
    distributions = create_distribution_plots(sample_df, ["temp1", "temp2"])

    # 时序图表应该有2条线
    assert len(time_series["data"]) == 2

    # 分布图表应该有2个图
    assert len(distributions) == 2

    # 验证颜色来自预定义的调色板
    assert all("color" in trace["line"] for trace in time_series["data"])


def test_hover_templates():
    """测试悬停提示模板"""
    sample_df = pl.DataFrame(
        {"DateTime": [datetime(2023, 1, 1)], "temperature": [25.5]}
    )

    result = create_time_series_plot(sample_df, "DateTime", ["temperature"])

    # 验证悬停模板存在且包含预期内容
    trace = result["data"][0]
    assert "hovertemplate" in trace
    assert "temperature" in trace["hovertemplate"]
    assert "时间" in trace["hovertemplate"]
    assert "数值" in trace["hovertemplate"]
