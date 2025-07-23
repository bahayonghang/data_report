"""
错误处理和边界条件测试
"""

import pytest
import tempfile
import json
import io
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import numpy as np


class TestErrorHandling:
    """错误处理测试"""

    def test_file_not_found_error(self, api_client):
        """测试文件未找到错误"""
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "nonexistent.csv"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert result["success"] is False
        assert result["error"]["code"] == "FILE_NOT_FOUND"
        assert "文件未找到" in result["error"]["message"]

    def test_path_traversal_attack(self, api_client):
        """测试路径遍历攻击防护"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "data/../../config.json",
            "./../sensitive.txt"
        ]
        
        for path in malicious_paths:
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": path}
            )
            
            assert response.status_code == 400
            result = response.json()
            assert result["success"] is False
            assert result["error"]["code"] == "INVALID_FILE"

    def test_invalid_file_type(self, api_client, test_data_dir):
        """测试无效文件类型"""
        invalid_files = [
            {"name": "test.txt", "content": "This is a text file"},
            {"name": "test.json", "content": '{"key": "value"}'},
            {"name": "test.xml", "content": "<root><item>test</item></root>"},
            {"name": "test.pdf", "content": "Not a real PDF content"},
            {"name": "test.jpg", "content": "Not a real image"},
        ]
        
        for file_info in invalid_files:
            file_path = Path(test_data_dir) / file_info["name"]
            file_path.write_text(file_info["content"])
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": file_info["name"]}
            )
            
            assert response.status_code == 400
            result = response.json()
            assert result["success"] is False
            assert result["error"]["code"] == "INVALID_FILE_TYPE"

    def test_malformed_csv(self, api_client, test_data_dir):
        """测试格式错误的CSV"""
        malformed_csvs = [
            # 不匹配的列数
            "DateTime,value1,value2\n2024-01-01,1.5",
            # 无效的日期格式
            "DateTime,value\ninvalid_date,1.5",
            # 空列名
            "DateTime,,value\n2024-01-01,1.5,2.5",
            # 特殊字符
            "DateTime,value\n2024-01-01,$%^&*",
            # 非常大的数字
            "DateTime,value\n2024-01-01,1e308",
            # 科学计数法
            "DateTime,value\n2024-01-01,1.23e-100",
        ]
        
        for i, csv_content in enumerate(malformed_csvs):
            file_path = Path(test_data_dir) / f"malformed_{i}.csv"
            file_path.write_text(csv_content)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"malformed_{i}.csv"}
            )
            
            # 应该返回成功，但可能包含警告
            assert response.status_code == 200
            result = response.json()
            # 允许成功或包含警告
            assert result["success"] is True or "warnings" in result

    def test_corrupted_parquet(self, api_client, test_data_dir):
        """测试损坏的Parquet文件"""
        # 创建损坏的Parquet文件
        file_path = Path(test_data_dir) / "corrupted.parquet"
        file_path.write_bytes(b"This is not a valid parquet file")
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "corrupted.parquet"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False
        assert "错误" in result["error"]["message"]

    def test_empty_file(self, api_client, test_data_dir):
        """测试空文件"""
        # 创建空文件
        file_path = Path(test_data_dir) / "empty.csv"
        file_path.write_text("")
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "empty.csv"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result["success"] is False

    def test_single_column_data(self, api_client, test_data_dir):
        """测试单列数据"""
        single_column_csv = "DateTime\n2024-01-01\n2024-01-02\n2024-01-03"
        
        file_path = Path(test_data_dir) / "single_column.csv"
        file_path.write_text(single_column_csv)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "single_column.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # 验证没有相关性分析
        visualizations = result["data"]["visualizations"]
        if "correlation_heatmap" in visualizations:
            assert "error" in visualizations["correlation_heatmap"]

    def test_large_file_upload(self, api_client):
        """测试大文件上传"""
        # 生成一个约1GB的测试文件
        oversized_content = 'x' * (1024 * 1024 * 1024)  # 1GB
        
        response = api_client.post(
            "/api/upload-and-analyze",
            files={"file": ("large.csv", oversized_content.encode(), "text/csv")}
        )
        
        assert response.status_code == 413  # 请求实体过大
        result = response.json()
        assert result["success"] is False
        assert result["error"]["code"] == "FILE_TOO_LARGE"

    def test_memory_limit_handling(self, api_client, test_data_dir):
        """测试内存限制处理"""
        # 创建可能触发内存限制的数据
        rows = 1000000  # 100万行
        dates = [datetime.now() + timedelta(hours=i) for i in range(rows)]
        
        data = {
            "DateTime": dates,
            "value1": [i * 0.1 for i in range(rows)],
            "value2": [i * 0.2 for i in range(rows)],
            "value3": [i * 0.3 for i in range(rows)],
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "memory_intensive.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "memory_intensive.csv"}
        )
        
        # 应该处理内存限制优雅
        assert response.status_code in [200, 500]
        if response.status_code == 500:
            result = response.json()
            assert "内存" in result["error"]["message"] or "Memory" in result["error"]["message"]

    def test_timeout_handling(self, api_client, test_data_dir):
        """测试超时处理"""
        # 创建复杂数据集，可能导致处理超时
        rows = 100000
        dates = [datetime.now() + timedelta(minutes=i) for i in range(rows)]
        
        # 创建大量列的复杂数据
        data = {"DateTime": dates}
        for i in range(50):  # 50列
            data[f"metric_{i}"] = [j * i * 0.1 for j in range(rows)]
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "complex_data.csv"
        df.write_csv(file_path)
        
        # 使用较短的超时时间
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "complex_data.csv"},
            timeout=30  # 30秒超时
        )
        
        # 应该返回超时错误或成功处理
        assert response.status_code in [200, 504]

    def test_invalid_api_parameters(self, api_client):
        """测试无效API参数"""
        invalid_params = [
            # 缺少必需参数
            {},
            {"filename": ""},
            {"filename": None},
            # 无效类型
            {"filename": 123},
            {"filename": ["test.csv"]},
            # 超长文件名
            {"filename": "a" * 1000 + ".csv"},
            # 特殊字符
            {"filename": "test\x00.csv"},
            {"filename": "test\n.csv"},
        ]
        
        for params in invalid_params:
            response = api_client.post(
                "/api/analyze-server-file",
                data=params
            )
            
            # 应该返回400错误
            assert response.status_code in [400, 422]

    def test_concurrent_error_handling(self, api_client, test_data_dir):
        """测试并发错误处理"""
        import threading
        import time
        
        # 创建测试文件
        file_path = Path(test_data_dir) / "concurrent_test.csv"
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(100)],
            "value": [i * 0.1 for i in range(100)]
        }
        df = pl.DataFrame(data)
        df.write_csv(file_path)
        
        errors = []
        results = []
        
        def make_request():
            try:
                response = api_client.post(
                    "/api/analyze-server-file",
                    data={"filename": "concurrent_test.csv"}
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # 创建多个并发请求
        threads = []
        for _ in range(20):  # 20个并发请求
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"并发请求出现错误: {errors}"
        assert all(status == 200 for status in results)

    def test_resource_cleanup(self, api_client, test_data_dir):
        """测试资源清理"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 创建并处理多个文件
        for i in range(10):
            data = {
                "DateTime": [datetime.now() + timedelta(hours=j) for j in range(1000)],
                f"value_{i}": [j * 0.1 for j in range(1000)]
            }
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"cleanup_test_{i}.csv"
            df.write_csv(file_path)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"cleanup_test_{i}.csv"}
            )
            assert response.status_code == 200
        
        # 强制垃圾回收并检查内存
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024  # 100MB


class TestBoundaryConditions:
    """边界条件测试"""

    def test_edge_case_values(self, api_client, test_data_dir):
        """测试边界值"""
        edge_cases = [
            # 浮点数边界
            {"values": [1e-308, 1e308, -1e308, np.inf, -np.inf, np.nan]},
            # 整数边界
            {"values": [np.iinfo(np.int64).max, np.iinfo(np.int64).min, 0]},
            # 零值
            {"values": [0.0, -0.0, 0.0000001, -0.0000001]},
            # 重复值
            {"values": [1.0] * 100},
            # 递增序列
            {"values": list(range(1000))},
            # 递减序列
            {"values": list(range(1000, 0, -1))},
        ]
        
        for i, case in enumerate(edge_cases):
            data = {
                "DateTime": [datetime.now() + timedelta(hours=j) for j in range(len(case["values"]))],
                "values": case["values"]
            }
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"edge_case_{i}.csv"
            df.write_csv(file_path)
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"edge_case_{i}.csv"}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True

    def test_zero_variance_data(self, api_client, test_data_dir):
        """测试零方差数据"""
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(10)],
            "constant": [5.0] * 10,
            "zero": [0.0] * 10,
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "zero_variance.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "zero_variance.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # 验证零方差处理
        stats = result["data"]["statistics"]
        assert stats["constant"]["std"] == 0
        assert stats["zero"]["std"] == 0

    def test_single_row_data(self, api_client, test_data_dir):
        """测试单行数据"""
        data = {
            "DateTime": [datetime.now()],
            "value": [1.5],
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "single_row.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "single_row.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["file_info"]["rows"] == 1

    def test_max_columns_limit(self, api_client, test_data_dir):
        """测试最大列数限制"""
        # 创建100列的数据
        rows = 100
        data = {"DateTime": [datetime.now() + timedelta(hours=i) for i in range(rows)]}
        
        for i in range(100):
            data[f"col_{i}"] = [i * j * 0.1 for j in range(rows)]
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "max_columns.csv"
        df.write_csv(file_path)
        
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "max_columns.csv"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["file_info"]["columns"] == 101  # 时间列 + 100数据列