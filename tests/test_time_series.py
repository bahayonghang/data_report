"""
时间序列分析模块单元测试
"""

import pytest
import polars as pl
import numpy as np
from datetime import datetime, timedelta

from src.reporter.analysis.time_series import (
    calculate_time_range,
    perform_adf_test,
    analyze_time_series,
)


class TestCalculateTimeRange:
    """时间范围计算测试"""

    def test_daily_frequency(self):
        """测试日频数据"""
        dates = pl.Series(
            [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
            ]
        )

        result = calculate_time_range(dates)

        assert result["start"] == "2023-01-01 00:00:00"
        assert result["end"] == "2023-01-04 00:00:00"
        assert result["duration_days"] == 3
        assert result["frequency"] == "daily"
        assert result["total_points"] == 4

    def test_weekly_frequency(self):
        """测试周频数据"""
        dates = pl.Series(
            [
                datetime(2023, 1, 1),
                datetime(2023, 1, 8),
                datetime(2023, 1, 15),
                datetime(2023, 1, 22),
            ]
        )

        result = calculate_time_range(dates)

        assert result["frequency"] == "weekly"
        assert result["duration_days"] == 21

    def test_empty_series(self):
        """测试空时间序列"""
        dates = pl.Series([], dtype=pl.Datetime)

        result = calculate_time_range(dates)

        assert result["total_points"] == 0
        assert result["start"] is None
        assert result["end"] is None

    def test_single_point(self):
        """测试单个时间点"""
        dates = pl.Series([datetime(2023, 1, 1)])

        result = calculate_time_range(dates)

        assert result["total_points"] == 1
        assert result["frequency"] == "single_point"
        assert result["duration_days"] == 0

    def test_gaps_detection(self):
        """测试间隔检测"""
        dates = pl.Series(
            [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 5),  # 跳过3、4日
                datetime(2023, 1, 6),
            ]
        )

        result = calculate_time_range(dates)

        assert len(result["gaps"]) > 0
        assert result["gaps"][0]["duration_days"] == 3


class TestPerformADFTest:
    """ADF检验测试"""

    def test_stationary_series(self):
        """测试平稳序列"""
        # 生成平稳序列（白噪声）
        np.random.seed(42)
        values = pl.Series(np.random.normal(0, 1, 100))

        result = perform_adf_test(values)

        assert result["adf_statistic"] is not None
        assert result["p_value"] is not None
        assert "critical_values" in result
        assert "interpretation" in result

    def test_non_stationary_series(self):
        """测试非平稳序列"""
        # 生成随机游走（非平稳）
        np.random.seed(42)
        random_walk = np.cumsum(np.random.normal(0, 1, 100))
        values = pl.Series(random_walk)

        result = perform_adf_test(values)

        assert result["adf_statistic"] is not None
        assert result["p_value"] is not None

    def test_insufficient_data(self):
        """测试数据不足"""
        values = pl.Series([1, 2, 3])

        result = perform_adf_test(values)

        assert result["adf_statistic"] is None
        assert "数据不足" in result["interpretation"]

    def test_empty_series(self):
        """测试空序列"""
        values = pl.Series([])

        result = perform_adf_test(values)

        assert result["adf_statistic"] is None

    def test_with_nulls(self):
        """测试包含空值"""
        values = pl.Series([1.0, 2.0, None, 4.0, 5.0])

        result = perform_adf_test(values)

        assert result["adf_statistic"] is not None


class TestAnalyzeTimeSeries:
    """时间序列综合分析测试"""

    def test_complete_analysis(self):
        """测试完整分析"""
        # 创建测试数据
        df = pl.DataFrame(
            {
                "date": [
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 2),
                    datetime(2023, 1, 3),
                    datetime(2023, 1, 4),
                    datetime(2023, 1, 5),
                ],
                "temperature": [20.0, 21.0, 19.5, 22.0, 20.5],
            }
        )

        result = analyze_time_series(df, "date", "temperature")

        assert "time_analysis" in result
        assert "adf_test" in result
        assert "basic_stats" in result

        assert result["time_analysis"]["total_points"] == 5
        assert result["basic_stats"]["count"] == 5

    def test_invalid_columns(self):
        """测试无效列名"""
        df = pl.DataFrame({"date": [datetime(2023, 1, 1)], "temperature": [20.0]})

        result = analyze_time_series(df, "invalid_date", "temperature")
        assert result == {}

        result = analyze_time_series(df, "date", "invalid_temp")
        assert result == {}

    def test_with_nulls_in_data(self):
        """测试数据中的空值"""
        df = pl.DataFrame(
            {
                "date": [
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 2),
                    None,
                    datetime(2023, 1, 4),
                ],
                "temperature": [20.0, None, 21.0, 22.0],
            }
        )

        result = analyze_time_series(df, "date", "temperature")

        assert result["basic_stats"]["count"] == 2  # 只有2个有效数据点


@pytest.fixture
def sample_time_series():
    """创建测试时间序列数据"""
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(30)]
    values = [20 + 0.1 * i + np.random.normal(0, 0.5) for i in range(30)]

    return pl.DataFrame({"date": dates, "value": values})


class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self, sample_time_series):
        """测试完整流程"""
        result = analyze_time_series(sample_time_series, "date", "value")

        assert isinstance(result, dict)
        assert result["time_analysis"]["total_points"] == 30
        assert result["time_analysis"]["frequency"] == "daily"
        assert "adf_statistic" in result["adf_test"]
        assert "p_value" in result["adf_test"]
