"""
测试工具函数和数据生成器
"""

import tempfile
import json
import csv
import os
import io
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import numpy as np
from typing import Dict, Any, List, Union


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_csv_data(
        rows: int = 100,
        columns: int = 3,
        start_date: datetime = None,
        missing_ratio: float = 0.0,
        noise_level: float = 0.1
    ) -> str:
        """生成CSV格式的测试数据"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        
        # 生成时间序列
        dates = [start_date + timedelta(hours=i) for i in range(rows)]
        
        # 生成数据
        data = {"DateTime": [d.isoformat() for d in dates]}
        
        for i in range(1, columns + 1):
            base_values = np.linspace(0, 100, rows)
            noise = np.random.normal(0, noise_level * 100, rows)
            values = base_values + noise
            
            # 添加缺失值
            if missing_ratio > 0:
                mask = np.random.random(rows) < missing_ratio
                values = np.where(mask, None, values)
            
            data[f"value{i}"] = values
        
        # 转换为CSV字符串
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        
        for i in range(rows):
            row = {key: data[key][i] for key in data.keys()}
            writer.writerow(row)
        
        return output.getvalue()

    @staticmethod
    def generate_parquet_data(
        rows: int = 100,
        columns: int = 3,
        start_date: datetime = None,
        missing_ratio: float = 0.0
    ) -> bytes:
        """生成Parquet格式的测试数据"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        
        dates = [start_date + timedelta(minutes=i * 15) for i in range(rows)]
        
        data = {"tagTime": dates}
        
        for i in range(1, columns + 1):
            values = np.random.normal(50, 10, rows)
            
            if missing_ratio > 0:
                mask = np.random.random(rows) < missing_ratio
                values = np.where(mask, None, values)
            
            data[f"sensor{i}"] = values
        
        df = pl.DataFrame(data)
        
        # 保存为Parquet格式
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            df.write_parquet(f.name)
            f.seek(0)
            return f.read()

    @staticmethod
    def generate_edge_cases() -> Dict[str, str]:
        """生成边界条件测试数据"""
        test_cases = {}
        
        # 空数据
        test_cases["empty"] = "DateTime,value\n"
        
        # 单列数据
        test_cases["single_column"] = "DateTime\n2024-01-01\n2024-01-02\n"
        
        # 无时间列数据
        test_cases["no_time"] = "feature1,feature2\n1.0,2.0\n3.0,4.0\n"
        
        # 所有值都相同
        test_cases["same_values"] = "DateTime,value\n2024-01-01,1.0\n2024-01-02,1.0\n"
        
        # 极值数据
        test_cases["extreme_values"] = "DateTime,value\n2024-01-01,1e308\n2024-01-02,-1e308\n"
        
        # 特殊字符
        test_cases["special_chars"] = "DateTime,value\n2024-01-01,NaN\n2024-01-02,inf\n"
        
        return test_cases

    @staticmethod
    def generate_performance_data(rows: int = 10000, columns: int = 10) -> str:
        """生成性能测试数据"""
        start_date = datetime.now() - timedelta(days=365)
        dates = [start_date + timedelta(minutes=i) for i in range(rows)]
        
        data = {"DateTime": [d.isoformat() for d in dates]}
        
        for i in range(1, columns + 1):
            data[f"metric{i}"] = np.random.normal(50, 15, rows)
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        
        for i in range(rows):
            row = {key: data[key][i] for key in data.keys()}
            writer.writerow(row)
        
        return output.getvalue()


class TestValidator:
    """测试验证工具"""

    @staticmethod
    def validate_analysis_response(response_data: Dict[str, Any]) -> bool:
        """验证分析响应格式"""
        required_keys = ["success", "data"]
        if not all(key in response_data for key in required_keys):
            return False
        
        if not response_data["success"]:
            return False
        
        data = response_data["data"]
        required_data_keys = [
            "file_info", "time_info", "statistics", 
            "missing_values", "correlation_matrix", "visualizations"
        ]
        
        return all(key in data for key in required_data_keys)

    @staticmethod
    def validate_file_info(file_info: Dict[str, Any]) -> bool:
        """验证文件信息格式"""
        required_keys = ["name", "rows", "columns", "size"]
        return all(key in file_info for key in required_keys)

    @staticmethod
    def validate_visualizations(visualizations: Dict[str, Any]) -> bool:
        """验证可视化数据格式"""
        expected_charts = [
            "time_series", "correlation_heatmap", 
            "distributions", "box_plots"
        ]
        
        for chart in expected_charts:
            if chart in visualizations:
                chart_data = visualizations[chart]
                if isinstance(chart_data, dict) and "error" in chart_data:
                    continue  # 跳过有错误的图表
                if not isinstance(chart_data, str):
                    return False
        
        return True


class PerformanceMonitor:
    """性能监控工具"""

    def __init__(self):
        self.metrics = {}

    def start_measurement(self, name: str):
        """开始性能测量"""
        import time
        self.metrics[name] = {"start": time.time()}

    def end_measurement(self, name: str):
        """结束性能测量"""
        import time
        if name in self.metrics:
            self.metrics[name]["end"] = time.time()
            self.metrics[name]["duration"] = (
                self.metrics[name]["end"] - self.metrics[name]["start"]
            )

    def get_metrics(self) -> Dict[str, float]:
        """获取性能指标"""
        return {
            name: data["duration"] 
            for name, data in self.metrics.items() 
            if "duration" in data
        }

    def check_memory_usage(self) -> Dict[str, float]:
        """检查内存使用情况"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}


class TestEnvironment:
    """测试环境管理"""

    def __init__(self):
        self.temp_dir = None

    def setup(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        os.environ["DATA_DIRECTORY"] = self.temp_dir
        return self.temp_dir

    def teardown(self):
        """清理测试环境"""
        import shutil
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        if "DATA_DIRECTORY" in os.environ:
            del os.environ["DATA_DIRECTORY"]

    def create_test_file(self, filename: str, content: str) -> str:
        """创建测试文件"""
        if not self.temp_dir:
            self.setup()
        
        file_path = Path(self.temp_dir) / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return str(file_path)

    def create_test_csv(self, filename: str, rows: int = 100) -> str:
        """创建测试CSV文件"""
        content = TestDataGenerator.generate_csv_data(rows=rows)
        return self.create_test_file(filename, content)

    def create_test_parquet(self, filename: str, rows: int = 100) -> str:
        """创建测试Parquet文件"""
        if not self.temp_dir:
            self.setup()
        
        parquet_data = TestDataGenerator.generate_parquet_data(rows=rows)
        file_path = Path(self.temp_dir) / filename
        
        with open(file_path, "wb") as f:
            f.write(parquet_data)
        
        return str(file_path)