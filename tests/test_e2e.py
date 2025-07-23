"""
端到端测试
测试完整的用户工作流程，包括API端点、数据分析和可视化功能
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import json
import os
import shutil
from pathlib import Path
import polars as pl
from datetime import datetime, timedelta
import io

from main import app


class TestE2E:
    """端到端测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def test_data_dir(self):
        """创建临时测试数据目录"""
        test_dir = tempfile.mkdtemp()
        original_data_dir = os.environ.get("DATA_DIRECTORY")
        os.environ["DATA_DIRECTORY"] = test_dir
        
        yield test_dir
        
        # 清理
        shutil.rmtree(test_dir, ignore_errors=True)
        if original_data_dir:
            os.environ["DATA_DIRECTORY"] = original_data_dir
        elif "DATA_DIRECTORY" in os.environ:
            del os.environ["DATA_DIRECTORY"]

    @pytest.fixture
    def sample_csv_data(self):
        """创建示例CSV数据"""
        # 生成时间序列数据
        start_date = datetime.now() - timedelta(days=30)
        dates = [start_date + timedelta(hours=i) for i in range(720)]  # 30天，每小时一个点
        
        data = {
            "DateTime": dates,
            "temperature": [20 + 5 * (i % 24) / 24 + (i % 7) for i in range(720)],
            "humidity": [50 + 20 * (i % 12) / 12 + (i % 3) for i in range(720)],
            "pressure": [1013 + 10 * (i % 6) / 6 for i in range(720)],
        }
        
        df = pl.DataFrame(data)
        return df

    @pytest.fixture
    def sample_parquet_data(self):
        """创建示例Parquet数据"""
        # 生成不同类型的时间序列数据
        start_date = datetime.now() - timedelta(days=10)
        dates = [start_date + timedelta(minutes=i*15) for i in range(960)]  # 10天，15分钟间隔
        
        data = {
            "tagTime": dates,
            "sensor1": [100 + 50 * (i % 96) / 96 for i in range(960)],
            "sensor2": [200 + 30 * (i % 48) / 48 for i in range(960)],
            "sensor3": [50 + 25 * (i % 24) / 24 for i in range(960)],
        }
        
        df = pl.DataFrame(data)
        return df

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "data_directory" in data
        assert "data_directory_exists" in data

    def test_main_page(self, client):
        """测试主页面"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_list_files_empty_directory(self, client, test_data_dir):
        """测试空目录的文件列表"""
        response = client.get("/api/list-files")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["files"] == []

    def test_complete_csv_workflow(self, client, test_data_dir, sample_csv_data):
        """测试完整的CSV文件工作流"""
        # 1. 创建测试CSV文件
        csv_file = Path(test_data_dir) / "test_data.csv"
        sample_csv_data.write_csv(csv_file)
        
        # 2. 列出文件
        response = client.get("/api/list-files")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "test_data.csv"
        assert data["files"][0]["size"] > 0
        
        # 3. 分析服务器文件
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "test_data.csv"}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        assert analysis_result["success"] is True
        
        # 验证分析结果结构
        data = analysis_result["data"]
        assert "file_info" in data
        assert "time_info" in data
        assert "statistics" in data
        assert "missing_values" in data
        assert "correlation_matrix" in data
        assert "stationarity_tests" in data
        assert "visualizations" in data
        
        # 验证文件信息
        file_info = data["file_info"]
        assert file_info["name"] == "test_data.csv"
        assert file_info["rows"] == 720
        assert file_info["columns"] == 4
        
        # 验证时间信息
        time_info = data["time_info"]
        assert time_info["time_column"] == "DateTime"
        assert "time_range" in time_info
        
        # 验证统计信息
        statistics = data["statistics"]
        expected_numeric_columns = ["temperature", "humidity", "pressure"]
        for col in expected_numeric_columns:
            assert col in statistics
            assert "mean" in statistics[col]
            assert "std" in statistics[col]
            assert "min" in statistics[col]
            assert "max" in statistics[col]
        
        # 验证可视化
        visualizations = data["visualizations"]
        assert "time_series" in visualizations
        assert "correlation_heatmap" in visualizations
        assert "distributions" in visualizations
        assert "box_plots" in visualizations

    def test_complete_parquet_workflow(self, client, test_data_dir, sample_parquet_data):
        """测试完整的Parquet文件工作流"""
        # 1. 创建测试Parquet文件
        parquet_file = Path(test_data_dir) / "sensor_data.parquet"
        sample_parquet_data.write_parquet(parquet_file)
        
        # 2. 列出文件
        response = client.get("/api/list-files")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "sensor_data.parquet"
        
        # 3. 分析服务器文件
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "sensor_data.parquet"}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        assert analysis_result["success"] is True
        
        # 验证时间列识别
        data = analysis_result["data"]
        time_info = data["time_info"]
        assert time_info["time_column"] == "tagTime"
        
        # 验证传感器数据分析
        statistics = data["statistics"]
        expected_sensors = ["sensor1", "sensor2", "sensor3"]
        for sensor in expected_sensors:
            assert sensor in statistics
            assert statistics[sensor]["count"] == 960

    def test_file_upload_workflow(self, client, sample_csv_data):
        """测试文件上传工作流"""
        # 1. 准备上传文件
        csv_content = io.StringIO()
        sample_csv_data.write_csv(csv_content)
        csv_bytes = csv_content.getvalue().encode('utf-8')
        
        # 2. 上传并分析文件
        response = client.post(
            "/api/upload-and-analyze",
            files={"file": ("uploaded_data.csv", csv_bytes, "text/csv")}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        assert analysis_result["success"] is True
        
        # 验证分析结果
        data = analysis_result["data"]
        assert data["file_info"]["name"] == "uploaded_data.csv"
        assert data["file_info"]["rows"] == 720
        assert data["time_info"]["time_column"] == "DateTime"

    def test_error_scenarios(self, client, test_data_dir):
        """测试各种错误场景"""
        # 1. 分析不存在的文件
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "nonexistent.csv"}
        )
        assert response.status_code == 404
        
        error_data = response.json()
        assert error_data["success"] is False
        assert error_data["error"]["code"] == "FILE_NOT_FOUND"
        
        # 2. 路径遍历攻击测试
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "../../../etc/passwd"}
        )
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data["success"] is False
        assert error_data["error"]["code"] == "INVALID_FILE"
        
        # 3. 上传不支持的文件类型
        response = client.post(
            "/api/upload-and-analyze",
            files={"file": ("test.txt", b"some text content", "text/plain")}
        )
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data["success"] is False
        assert error_data["error"]["code"] == "INVALID_FILE_TYPE"
        
        # 4. 上传过大文件
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        response = client.post(
            "/api/upload-and-analyze",
            files={"file": ("large.csv", large_content, "text/csv")}
        )
        assert response.status_code == 413
        
        error_data = response.json()
        assert error_data["success"] is False
        assert error_data["error"]["code"] == "FILE_TOO_LARGE"

    def test_data_with_missing_values(self, client, test_data_dir):
        """测试包含缺失值的数据"""
        # 创建包含缺失值的数据
        dates = [datetime.now() - timedelta(hours=i) for i in range(100)]
        
        data = {
            "DateTime": dates,
            "value1": [i if i % 10 != 0 else None for i in range(100)],
            "value2": [i * 2 if i % 5 != 0 else None for i in range(100)],
        }
        
        df = pl.DataFrame(data)
        csv_file = Path(test_data_dir) / "missing_data.csv"
        df.write_csv(csv_file)
        
        # 分析文件
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "missing_data.csv"}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        data = analysis_result["data"]
        
        # 验证缺失值分析
        missing_values = data["missing_values"]
        assert "value1" in missing_values
        assert "value2" in missing_values
        assert missing_values["value1"]["missing_count"] == 10
        assert missing_values["value2"]["missing_count"] == 20

    def test_single_column_data(self, client, test_data_dir):
        """测试单列数据"""
        dates = [datetime.now() - timedelta(hours=i) for i in range(50)]
        
        data = {
            "DateTime": dates,
            "single_value": [i for i in range(50)],
        }
        
        df = pl.DataFrame(data)
        csv_file = Path(test_data_dir) / "single_column.csv"
        df.write_csv(csv_file)
        
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "single_column.csv"}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        data = analysis_result["data"]
        
        # 单列数据不应该有相关性热力图
        visualizations = data["visualizations"]
        assert "correlation_heatmap" not in visualizations or "error" in visualizations.get("correlation_heatmap", {})

    def test_no_time_column_data(self, client, test_data_dir):
        """测试没有时间列的数据"""
        data = {
            "feature1": [i for i in range(100)],
            "feature2": [i * 2 for i in range(100)],
            "feature3": [i * 3 for i in range(100)],
        }
        
        df = pl.DataFrame(data)
        csv_file = Path(test_data_dir) / "no_time_column.csv"
        df.write_csv(csv_file)
        
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "no_time_column.csv"}
        )
        assert response.status_code == 200
        
        analysis_result = response.json()
        data = analysis_result["data"]
        
        # 应该没有时间列和时序图表
        time_info = data["time_info"]
        assert time_info["time_column"] is None
        
        visualizations = data["visualizations"]
        assert "time_series" not in visualizations or "error" in visualizations.get("time_series", {})

    def test_concurrent_requests(self, client, test_data_dir, sample_csv_data):
        """测试并发请求处理"""
        import threading
        import time
        
        # 创建测试文件
        csv_file = Path(test_data_dir) / "concurrent_test.csv"
        sample_csv_data.write_csv(csv_file)
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.post(
                    "/api/analyze-server-file",
                    data={"filename": "concurrent_test.csv"}
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # 创建5个并发请求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)

    def test_memory_usage_with_large_dataset(self, client, test_data_dir):
        """测试大数据集的内存使用"""
        import psutil
        import os
        
        # 记录初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建相对较大的数据集
        dates = [datetime.now() - timedelta(minutes=i) for i in range(10000)]
        
        data = {
            "DateTime": dates,
            "sensor1": [i + (i % 100) for i in range(10000)],
            "sensor2": [i * 2 + (i % 50) for i in range(10000)],
            "sensor3": [i * 3 + (i % 25) for i in range(10000)],
            "sensor4": [i * 0.5 + (i % 10) for i in range(10000)],
        }
        
        df = pl.DataFrame(data)
        csv_file = Path(test_data_dir) / "large_dataset.csv"
        df.write_csv(csv_file)
        
        # 分析文件
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "large_dataset.csv"}
        )
        assert response.status_code == 200
        
        # 检查内存使用增长
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该合理（小于500MB）
        assert memory_increase < 500, f"Memory usage increased too much: {memory_increase}MB"
        
        # 验证分析结果
        analysis_result = response.json()
        assert analysis_result["success"] is True
        
        data = analysis_result["data"]
        assert data["file_info"]["rows"] == 10000
        assert data["file_info"]["columns"] == 5

    def test_performance_benchmark(self, client, test_data_dir, sample_csv_data):
        """测试性能基准"""
        import time
        
        # 创建测试文件
        csv_file = Path(test_data_dir) / "performance_test.csv"
        sample_csv_data.write_csv(csv_file)
        
        # 测试分析时间
        start_time = time.time()
        
        response = client.post(
            "/api/analyze-server-file",
            data={"filename": "performance_test.csv"}
        )
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        assert response.status_code == 200
        
        # 分析时间应该在合理范围内（10秒内）
        assert analysis_time < 10, f"Analysis took too long: {analysis_time}s"
        
        # 验证响应大小合理
        response_size = len(response.content)
        assert response_size < 10 * 1024 * 1024, f"Response too large: {response_size} bytes"