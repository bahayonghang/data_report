"""图表主题和样式配置模块"""

from typing import Dict, List, Any

# 统一颜色方案
COLOR_PALETTE = {
    "primary": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#8E44AD", "#27AE60"],
    "secondary": ["#85C1E9", "#F8BBD9", "#F9E79F", "#F5B7B1", "#D7BDE2", "#A9DFBF"],
    "background": "#FFFFFF",
    "grid": "#E5E5E5",
    "text": "#2C3E50",
    "accent": "#3498DB",
}

# 相关性热力图专用颜色
CORRELATION_COLORS = "RdBu"

# 图表字体配置
FONT_CONFIG = {
    "family": "Arial, sans-serif",
    "size": 12,
    "color": COLOR_PALETTE["text"],
}

# 标题字体配置
TITLE_FONT_CONFIG = {
    "family": "Arial, sans-serif",
    "size": 16,
    "color": COLOR_PALETTE["text"],
}

# 基础图表配置
BASE_LAYOUT_CONFIG = {
    "font": FONT_CONFIG,
    "plot_bgcolor": COLOR_PALETTE["background"],
    "paper_bgcolor": COLOR_PALETTE["background"],
    "margin": {"l": 60, "r": 60, "t": 70, "b": 50},  # 增加边距以适配更大的图表
    "showlegend": True,
    "legend": {
        "orientation": "h",  # 改为水平布局
        "yanchor": "top",
        "y": 1.02,  # 移到图表上方
        "xanchor": "center",
        "x": 0.5,  # 水平居中
        "font": {"family": "Arial, sans-serif", "size": 11, "color": COLOR_PALETTE["text"]},
    },
}

# 网格和坐标轴配置
AXIS_CONFIG = {
    "showgrid": True,
    "gridwidth": 1,
    "gridcolor": COLOR_PALETTE["grid"],
    "linecolor": COLOR_PALETTE["text"],
    "linewidth": 1,
    "tickfont": FONT_CONFIG,
    "title": {"font": FONT_CONFIG},
}

# 响应式尺寸配置
# 针对2列布局优化的尺寸设置
RESPONSIVE_CONFIG = {
    "small": {"width": 350, "height": 250},  # 移动端单列布局
    "medium": {"width": 450, "height": 320},  # 桌面端2列布局，放大尺寸
    "large": {"width": 700, "height": 450},   # 特殊大图，放大尺寸
    "dashboard": {"width": 1200, "height": 800},  # 仪表板
}

# 交互配置
INTERACTION_CONFIG = {
    "displayModeBar": True,
    "modeBarButtonsToRemove": ["pan2d", "select2d", "lasso2d", "autoScale2d"],
    "displaylogo": False,
    "responsive": True,
    "scrollZoom": True,
}


def get_chart_theme(
    chart_type: str = "default", size: str = "medium"
) -> Dict[str, Any]:
    """获取图表主题配置"""

    # 基础配置
    layout = BASE_LAYOUT_CONFIG.copy()

    # 添加尺寸配置
    layout.update(RESPONSIVE_CONFIG[size])

    # 添加标题字体
    layout["title"] = {"font": TITLE_FONT_CONFIG}

    # 添加坐标轴配置
    layout["xaxis"] = AXIS_CONFIG.copy()
    layout["yaxis"] = AXIS_CONFIG.copy()

    # 根据图表类型调整配置
    if chart_type == "time_series":
        layout["hovermode"] = "x unified"
        layout["xaxis"]["type"] = "date"
        # 时间序列图表特定配置
        layout["legend"]["y"] = -0.15  # 将图例移到图表下方
        layout["legend"]["x"] = 0.5
        layout["legend"]["yanchor"] = "top"
        layout["margin"]["b"] = 50  # 增加底部边距容纳图例

    elif chart_type == "heatmap":
        layout["xaxis"]["showgrid"] = False
        layout["yaxis"]["showgrid"] = False
        layout["showlegend"] = False

    elif chart_type == "histogram":
        layout["bargap"] = 0.1
        layout["showlegend"] = False

    elif chart_type == "box":
        layout["showlegend"] = False
        layout["yaxis"]["zeroline"] = False

    elif chart_type == "dashboard":
        layout["showlegend"] = True
        layout["legend"]["orientation"] = "h"
        layout["legend"]["y"] = -0.1
        layout["legend"]["x"] = 0.5
        layout["legend"]["xanchor"] = "center"

    return layout


def get_color_sequence(n_colors: int = 6) -> List[str]:
    """获取颜色序列"""
    colors = COLOR_PALETTE["primary"]
    if n_colors <= len(colors):
        return colors[:n_colors]

    # 如果需要更多颜色，循环使用
    extended_colors = []
    for i in range(n_colors):
        extended_colors.append(colors[i % len(colors)])
    return extended_colors


def get_single_color(index: int = 0) -> str:
    """获取单个颜色"""
    colors = COLOR_PALETTE["primary"]
    return colors[index % len(colors)]


def apply_responsive_sizing(layout: Dict, device_type: str = "desktop") -> Dict:
    """应用响应式尺寸设置"""

    if device_type == "mobile":
        layout["width"] = min(400, layout.get("width", 600))
        layout["height"] = min(300, layout.get("height", 400))
        layout["margin"] = {"l": 40, "r": 20, "t": 60, "b": 40}

    elif device_type == "tablet":
        layout["width"] = min(600, layout.get("width", 800))
        layout["height"] = min(450, layout.get("height", 500))
        layout["margin"] = {"l": 50, "r": 30, "t": 70, "b": 50}

    else:  # desktop
        # 保持原有尺寸
        pass

    return layout


def enhance_interactivity(fig_dict: Dict) -> Dict:
    """增强图表交互性"""

    # 添加配置选项
    if "config" not in fig_dict:
        fig_dict["config"] = {}

    fig_dict["config"].update(INTERACTION_CONFIG)

    # 为时序图添加范围选择器（已禁用，移除底部控件）
    if "layout" in fig_dict and "xaxis" in fig_dict["layout"]:
        if fig_dict["layout"]["xaxis"].get("type") == "date":
            # 禁用范围滑块和选择器，移除图表底部控件
            fig_dict["layout"]["xaxis"]["rangeslider"] = {"visible": False}
            fig_dict["layout"]["xaxis"]["rangeselector"] = {"visible": False}

    return fig_dict


def get_hover_template(chart_type: str, column_name: str = "") -> str:
    """获取悬停提示模板"""

    templates = {
        "time_series": f"<b>{column_name}</b><br>时间: %{{x}}<br>数值: %{{y:.2f}}<extra></extra>",
        "histogram": f"<b>{column_name}</b><br>区间: %{{x}}<br>频次: %{{y}}<extra></extra>",
        "box": f"<b>{column_name}</b><br>数值: %{{y:.2f}}<extra></extra>",
        "heatmap": "<b>%{y}</b> vs <b>%{x}</b><br>相关系数: %{z:.3f}<extra></extra>",
        "scatter": "<b>X</b>: %{x:.2f}<br><b>Y</b>: %{y:.2f}<extra></extra>",
    }

    return templates.get(chart_type, "<b>值</b>: %{y}<extra></extra>")


def apply_animation_config() -> Dict:
    """获取动画配置"""
    return {
        "transition": {"duration": 500, "easing": "cubic-in-out"},
        "frame": {"duration": 500, "redraw": True},
    }
