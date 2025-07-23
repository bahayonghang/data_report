"""
文件格式和数据类型测试
"""

import pytest
import tempfile
import json
import io
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import numpy as np


class TestFileFormats:
    """文件格式兼容性测试"""

    def test_csv_formats(self, api_client, test_data_dir):
        """测试各种CSV格式"""
        test_cases = [
            # 标准CSV
            {
                "name": "standard.csv",
                "content": "DateTime,value1,value2\n2024-01-01,1.5,2.5\n2024-01-02,2.0,3.0",
                "expected_success": True
            },
            # 带引号的CSV
            {
                "name": "quoted.csv",
                "content": '"DateTime","value1","value2"\n"2024-01-01","1.5","2.5"',
                "expected_success": True
            },
            # 不同分隔符
            {
                "name": "semicolon.csv",
                "content": "DateTime;value1;value2\n2024-01-01;1.5;2.5",
                "expected_success": True
            },
            # 包含空值
            {
                "name": "with_nulls.csv",
                "content": "DateTime,value1,value2\n2024-01-01,1.5,\n2024-01-02,,3.0",
                "expected_success": True
            },
            # UTF-8编码
            {
                "name": "utf8.csv",
                "content": "时间,数值\n2024-01-01,1.5\n2024-01-02,2.0",
                "expected_success": True
            }
        ]

        for case in test_cases:
            file_path = Path(test_data_dir) / case["name"]
            file_path.write_text(case["content"], encoding="utf-8")
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": case["name"]}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] == case["expected_success"]

    def test_parquet_formats(self, api_client, test_data_dir):
        """测试Parquet格式"""
        # 创建各种Parquet测试数据
        test_cases = [
            # 基本Parquet
            {
                "name": "basic.parquet",
                "data": {
                    "tagTime": [datetime.now(), datetime.now() + timedelta(hours=1)],
                    "value1": [1.5, 2.0],
                    "value2": [2.5, 3.0]
                }
            },
            # 包含空值
            {
                "name": "with_nulls.parquet",
                "data": {
                    "tagTime": [datetime.now(), datetime.now() + timedelta(hours=1)],
                    "value1": [1.5, None],
                    "value2": [None, 3.0]
                }
            },
            # 大数据类型
            {
                "name": "types.parquet",
                "data": {
                    "tagTime": [datetime.now()] * 100,
                    "int_col": list(range(100)),
                    "float_col": [float(i) for i in range(100)],
                    "string_col": [f"str_{i}" for i in range(100)],
                    "bool_col": [i % 2 == 0 for i in range(100)]
                }
            }
        ]

        for case in test_cases:
            df = pl.DataFrame(case["data"])
            file_path = Path(test_data_dir) / case["name"]
            df.write_parquet(file_path)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": case["name"]}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True

    def test_data_types(self, api_client, test_data_dir):
        """测试各种数据类型"""
        # 测试数值类型
        numeric_data = {
            "DateTime": [datetime.now(), datetime.now() + timedelta(hours=1)],
            "int_col": [1, 2],
            "float_col": [1.5, 2.5],
            "negative": [-1.0, -2.0],
            "zero": [0.0, 0.0],
        }
        
        df = pl.DataFrame(numeric_data)
        file_path = Path(test_data_dir) / "numeric_types.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "numeric_types.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # 验证统计结果
        stats = result["data"]["statistics"]
        for col in ["int_col", "float_col", "negative"]:
            assert col in stats
            assert "mean" in stats[col]
            assert "std" in stats[col]

    def test_date_formats(self, api_client, test_data_dir):
        """测试各种日期格式"""
        date_formats = [
            "2024-01-01",
            "2024-01-01 10:00:00",
            "2024-01-01T10:00:00",
            "2024/01/01",
            "01/01/2024",
            "2024-01-01 10:00:00.123456",
        ]

        for date_str in date_formats:
            content = f"DateTime,value\n{date_str},1.5\n"
            filename = f"date_format_{date_str.replace(':', '').replace('/', '').replace(' ', '_')}.csv"
            
            file_path = Path(test_data_dir) / filename
            file_path.write_text(content)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": filename}
            )
            
            assert response.status_code == 200
            result = response.json()
            # 至少应该成功解析
            assert result["success"] is True

    def test_column_name_variations(self, api_client, test_data_dir):
        """测试列名变体"""
        column_names = [
            "timestamp",
            "time",
            "date",
            "datetime",
            "tagTime",
            "created_at",
            "recorded_at"
        ]

        for col_name in column_names:
            content = f"{col_name},value\n2024-01-01,1.5\n2024-01-02,2.0\n"
            filename = f"col_{col_name}.csv"
            
            file_path = Path(test_data_dir) / filename
            file_path.write_text(content)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": filename}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True

    def test_large_file_handling(self, api_client, test_data_dir):
        """测试大文件处理"""
        # 创建大文件
        rows = 50000  # 5万行
        dates = [datetime.now() + timedelta(hours=i) for i in range(rows)]
        
        data = {
            "DateTime": dates,
            "value1": [i * 0.1 for i in range(rows)],
            "value2": [i * 0.2 for i in range(rows)],
            "value3": [i * 0.3 for i in range(rows)],
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "large_file.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "large_file.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["file_info"]["rows"] == rows

    def test_encoding_support(self, api_client, test_data_dir):
        """测试编码支持"""
        encodings = [
            ("utf-8", "标准UTF-8"),
            ("gb2312", "简体中文"),
            ("gbk", "GBK编码"),
            ("big5", "繁体中文"),
        ]

        for encoding, description in encodings:
            content = f"时间,数值\n2024-01-01,1.5\n2024-01-02,2.0\n"
            filename = f"encoding_{encoding}.csv"
            
            file_path = Path(test_data_dir) / filename
            file_path.write_text(content, encoding=encoding)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": filename}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True


class TestDataQuality:
    """数据质量测试"""

    def test_missing_data_handling(self, api_client, test_data_dir):
        """测试缺失数据处理"""
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(10)],
            "complete": [1.0] * 10,
            "partial": [1.0, None, 2.0, None, 3.0, 4.0, None, 5.0, 6.0, None],
            "mostly_missing": [1.0] + [None] * 9,
            "all_missing": [None] * 10,
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "missing_data.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "missing_data.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        missing_values = result["data"]["missing_values"]
        assert "partial" in missing_values
        assert missing_values["partial"]["missing_count"] == 4
        assert missing_values["mostly_missing"]["missing_ratio"] > 0.9

    def test_outlier_detection(self, api_client, test_data_dir):
        """测试异常值检测"""
        np.random.seed(42)
        normal_data = np.random.normal(50, 5, 100)
        outliers = [200, 300, -200]  # 明显的异常值
        
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(103)],
            "values": list(normal_data) + outliers,
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "outliers.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "outliers.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        stats = result["data"]["statistics"]["values"]
        assert stats["max"] > 200  # 应该检测到异常值

    def test_stationarity_tests(self, api_client, test_data_dir):
        """测试时间序列平稳性检验"""
        # 创建非平稳数据
        np.random.seed(42)
        trend = np.linspace(0, 10, 100)
        noise = np.random.normal(0, 1, 100)
        
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(100)],
            "non_stationary": trend + noise,
            "stationary": noise,
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "stationarity_test.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "stationarity_test.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        
        stationarity_tests = result["data"]["stationarity_tests"]
        assert "non_stationary" in stationarity_tests
        assert "stationary" in stationarity_tests