"""
数据加载模块单元测试
"""

import tempfile
import pytest
import polars as pl
from pathlib import Path
from datetime import datetime

from src.reporter.data_loader import (
    load_data_file,
    detect_time_column,
    prepare_analysis_data,
)


class TestLoadDataFile:
    """文件加载测试"""

    def test_load_csv_file(self):
        """测试加载CSV文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            tmp.write("date,value1,value2\n2023-01-01,10,20\n2023-01-02,15,25")
            tmp.flush()

            df = load_data_file(tmp.name)
            assert len(df) == 2
            assert df.columns == ["date", "value1", "value2"]

        Path(tmp.name).unlink()

    def test_load_parquet_file(self):
        """测试加载Parquet文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"

            test_data = pl.DataFrame(
                {
                    "timestamp": ["2023-01-01", "2023-01-02"],
                    "temperature": [20.5, 21.0],
                    "humidity": [65, 68],
                }
            )
            test_data.write_parquet(parquet_path)

            df = load_data_file(str(parquet_path))
            assert len(df) == 2
            assert len(df.columns) == 3

    def test_unsupported_format(self):
        """测试不支持的文件格式"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("some text")
            tmp.flush()

            with pytest.raises(ValueError, match="不支持的文件格式"):
                load_data_file(tmp.name)

        Path(tmp.name).unlink()

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            load_data_file("/nonexistent/file.csv")


class TestDetectTimeColumn:
    """时间列检测测试"""

    def test_detect_by_column_name(self):
        """测试通过列名检测"""
        df = pl.DataFrame({"datetime": ["2023-01-01", "2023-01-02"], "value": [10, 20]})

        result = detect_time_column(df)
        assert result == "datetime"

    def test_detect_by_datetime_type(self):
        """测试通过数据类型检测"""
        df = pl.DataFrame(
            {
                "time_col": [datetime(2023, 1, 1), datetime(2023, 1, 2)],
                "value": [10, 20],
            }
        )

        result = detect_time_column(df)
        assert result == "time_col"

    def test_detect_by_tagtime_name(self):
        """测试检测tagTime列"""
        df = pl.DataFrame({"tagTime": ["2023-01-01", "2023-01-02"], "value": [10, 20]})

        result = detect_time_column(df)
        assert result == "tagTime"

    def test_detect_chinese_date_name(self):
        """测试检测中文日期列名"""
        df = pl.DataFrame({"日期": ["2023-01-01", "2023-01-02"], "数值": [10, 20]})

        result = detect_time_column(df)
        assert result == "日期"

    def test_no_time_column(self):
        """测试无时序列"""
        df = pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        result = detect_time_column(df)
        assert result is None

    def test_empty_dataframe(self):
        """测试空数据框"""
        df = pl.DataFrame()
        result = detect_time_column(df)
        assert result is None


class TestPrepareAnalysisData:
    """数据预处理测试"""

    def test_time_series_data(self):
        """测试时序数据预处理"""
        df = pl.DataFrame(
            {
                "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "temperature": [20.5, 21.0, 21.5],
                "humidity": [65, 68, 70],
            }
        )

        result = prepare_analysis_data(df)

        assert result["time_column"] == "date"
        assert "temperature" in result["numeric_columns"]
        assert "humidity" in result["numeric_columns"]
        assert result["total_rows"] == 3
        assert result["total_columns"] == 3
        assert "date" in result["missing_values"]

    def test_non_time_series_data(self):
        """测试非时序数据预处理"""
        df = pl.DataFrame(
            {
                "col1": [1, 2, 3],
                "col2": [4.5, 5.5, 6.5],
                "col3": ["a", "b", "c"],  # 非数值列
            }
        )

        result = prepare_analysis_data(df)

        assert result["time_column"] is None
        assert result["numeric_columns"] == ["col1", "col2"]
        assert len(result["numeric_columns"]) == 2

    def test_missing_values_detection(self):
        """测试缺失值检测"""
        df = pl.DataFrame(
            {"date": ["2023-01-01", None, "2023-01-03"], "value": [10, None, 30]}
        )

        result = prepare_analysis_data(df)

        assert result["missing_values"]["date"] == 1
        assert result["missing_values"]["value"] == 1

    def test_empty_dataframe_error(self):
        """测试空数据框错误"""
        df = pl.DataFrame()

        with pytest.raises(ValueError, match="数据框为空"):
            prepare_analysis_data(df)

    def test_no_numeric_columns_error(self):
        """测试无数值列错误"""
        df = pl.DataFrame(
            {
                "text_col": ["a", "b", "c"],
                "date_col": ["2023-01-01", "2023-01-02", "2023-01-03"],
            }
        )

        with pytest.raises(ValueError, match="没有找到数值列进行分析"):
            prepare_analysis_data(df)

    def test_datetime_conversion(self):
        """测试日期时间转换"""
        df = pl.DataFrame(
            {
                "timestamp": ["2023-01-01 10:00:00", "2023-01-02 11:00:00"],
                "value": [100, 200],
            }
        )

        result = prepare_analysis_data(df)

        assert result["time_column"] == "timestamp"
        assert result["total_rows"] == 2
        assert len(result["processed_df"]) == 2


@pytest.fixture
def sample_csv_file():
    """创建测试CSV文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
        tmp.write("date,temperature,humidity\n")
        tmp.write("2023-01-01,20.5,65\n")
        tmp.write("2023-01-02,21.0,68\n")
        tmp.write("2023-01-03,21.5,70\n")
        tmp.flush()

        yield tmp.name

    Path(tmp.name).unlink()


class TestIntegration:
    """集成测试"""

    def test_full_pipeline(self, sample_csv_file):
        """测试完整数据加载流程"""
        # 加载文件
        df = load_data_file(sample_csv_file)
        assert len(df) == 3

        # 检测时间列
        time_col = detect_time_column(df)
        assert time_col == "date"

        # 准备分析数据
        analysis_data = prepare_analysis_data(df)

        assert analysis_data["time_column"] == "date"
        assert "temperature" in analysis_data["numeric_columns"]
        assert "humidity" in analysis_data["numeric_columns"]
        assert analysis_data["total_rows"] == 3
        assert all(missing == 0 for missing in analysis_data["missing_values"].values())
