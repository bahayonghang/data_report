"""
性能和内存基准测试
"""

import pytest
import time
import psutil
import os
import gc
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import numpy as np
import threading
import requests


class TestPerformance:
    """性能基准测试"""

    def test_response_time_benchmarks(self, api_client, test_data_dir):
        """测试响应时间基准"""
        test_cases = [
            {"rows": 100, "cols": 3, "expected_time": 2.0},
            {"rows": 1000, "cols": 5, "expected_time": 3.0},
            {"rows": 10000, "cols": 10, "expected_time": 5.0},
            {"rows": 50000, "cols": 20, "expected_time": 10.0},
        ]

        for case in test_cases:
            # 创建测试数据
            data = {"DateTime": [datetime.now() + timedelta(hours=i) for i in range(case["rows"])]}
            for j in range(1, case["cols"] + 1):
                data[f"metric_{j}"] = np.random.normal(50, 15, case["rows"])
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"perf_{case['rows']}_{case['cols']}.csv"
            df.write_csv(file_path)
            
            # 测试响应时间
            start_time = time.time()
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"perf_{case['rows']}_{case['cols']}.csv"}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            
            # 打印性能指标
            print(f"Performance: {case['rows']} rows, {case['cols']} cols - {response_time:.2f}s")
            
            # 验证响应时间在预期范围内
            assert response_time < case["expected_time"], \
                f"Response time {response_time:.2f}s exceeds expected {case['expected_time']}s"

    def test_memory_usage_benchmarks(self, api_client, test_data_dir):
        """测试内存使用基准"""
        process = psutil.Process(os.getpid())
        
        test_cases = [
            {"rows": 1000, "expected_memory_mb": 50},
            {"rows": 10000, "expected_memory_mb": 100},
            {"rows": 50000, "expected_memory_mb": 300},
            {"rows": 100000, "expected_memory_mb": 500},
        ]

        for case in test_cases:
            # 清理内存
            gc.collect()
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # 创建测试数据
            data = {"DateTime": [datetime.now() + timedelta(hours=i) for i in range(case["rows"])]}
            for j in range(1, 6):  # 5列数据
                data[f"metric_{j}"] = np.random.normal(50, 15, case["rows"])
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"memory_{case['rows']}.csv"
            df.write_csv(file_path)
            
            # 测试内存使用
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"memory_{case['rows']}.csv"}
            )
            
            assert response.status_code == 200
            
            # 清理内存
            gc.collect()
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            print(f"Memory: {case['rows']} rows - {memory_increase:.1f}MB increase")
            
            # 验证内存使用在合理范围内
            assert memory_increase < case["expected_memory_mb"], \
                f"Memory increase {memory_increase:.1f}MB exceeds expected {case['expected_memory_mb']}MB"

    def test_concurrent_load_test(self, api_client, test_data_dir):
        """测试并发负载"""
        # 创建测试文件
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(1000)],
            "value1": np.random.normal(50, 15, 1000),
            "value2": np.random.normal(30, 10, 1000),
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "concurrent_test.csv"
        df.write_csv(file_path)
        
        # 并发测试参数
        concurrent_requests = 10
        total_requests = 50
        
        results = []
        errors = []
        response_times = []
        
        def worker():
            for _ in range(total_requests // concurrent_requests):
                start_time = time.time()
                try:
                    response = api_client.post(
                        "/api/analyze-server-file",
                        data={"filename": "concurrent_test.csv"}
                    )
                    end_time = time.time()
                    results.append(response.status_code)
                    response_times.append(end_time - start_time)
                except Exception as e:
                    errors.append(str(e))
        
        # 启动并发工作线程
        threads = []
        for _ in range(concurrent_requests):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"并发错误: {errors}"
        assert len(results) == total_requests
        assert all(status == 200 for status in results)
        
        # 验证平均响应时间
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 1.0  # 平均响应时间小于1秒
        
        print(f"Concurrent: {concurrent_requests} concurrent, {total_requests} total - avg: {avg_response_time:.3f}s")

    def test_api_rate_limiting(self, api_client, test_data_dir):
        """测试API速率限制"""
        # 创建测试文件
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(100)],
            "value": np.random.normal(50, 15, 100)
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "rate_limit_test.csv"
        df.write_csv(file_path)
        
        # 快速连续发送请求
        start_time = time.time()
        responses = []
        
        for i in range(100):
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": "rate_limit_test.csv"}
            )
            responses.append(response.status_code)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证所有请求成功
        assert all(status == 200 for status in responses)
        
        # 验证处理速度
        requests_per_second = len(responses) / total_time
        print(f"Rate limit: {requests_per_second:.1f} requests/second")
        
        # 应该能处理至少10个请求/秒
        assert requests_per_second > 10

    def test_data_processing_throughput(self, api_client, test_data_dir):
        """测试数据处理吞吐量"""
        test_sizes = [
            {"rows": 1000, "expected_throughput": 10000},
            {"rows": 10000, "expected_throughput": 5000},
            {"rows": 50000, "expected_throughput": 2000},
        ]

        for size in test_sizes:
            # 创建测试数据
            data = {
                "DateTime": [datetime.now() + timedelta(hours=i) for i in range(size["rows"])]
            }
            for j in range(1, 11):  # 10列数据
                data[f"metric_{j}"] = np.random.normal(50, 15, size["rows"])
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"throughput_{size['rows']}.csv"
            df.write_csv(file_path)
            
            # 测量处理时间
            start_time = time.time()
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"throughput_{size['rows']}.csv"}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            
            processing_time = end_time - start_time
            throughput = size["rows"] / processing_time
            
            print(f"Throughput: {size['rows']} rows - {throughput:.0f} rows/second")
            
            assert throughput > size["expected_throughput"], \
                f"Throughput {throughput:.0f} rows/s below expected {size['expected_throughput']} rows/s"

    def test_memory_leak_detection(self, api_client, test_data_dir):
        """测试内存泄漏检测"""
        process = psutil.Process(os.getpid())
        
        # 创建测试数据
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(1000)],
            "value1": np.random.normal(50, 15, 1000),
            "value2": np.random.normal(30, 10, 1000),
            "value3": np.random.normal(20, 5, 1000),
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "memory_leak_test.csv"
        df.write_csv(file_path)
        
        # 多次处理相同文件
        memory_readings = []
        for i in range(10):
            gc.collect()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": "memory_leak_test.csv"}
            )
            
            assert response.status_code == 200
            
            gc.collect()
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_after)
            
            print(f"Memory leak test {i+1}: {memory_after:.1f}MB")
        
        # 验证内存使用稳定（没有持续增长）
        memory_trend = np.polyfit(range(len(memory_readings)), memory_readings, 1)[0]
        assert abs(memory_trend) < 1.0  # 内存增长趋势小于1MB/次

    def test_large_dataset_chunking(self, api_client, test_data_dir):
        """测试大数据集分块处理"""
        # 创建100万行的数据集
        rows = 1000000
        chunk_size = 10000
        
        # 分批创建数据以避免内存问题
        all_data = []
        for chunk_start in range(0, rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, rows)
            chunk_dates = [datetime.now() + timedelta(hours=i) for i in range(chunk_start, chunk_end)]
            chunk_values = [i * 0.1 for i in range(chunk_start, chunk_end)]
            
            chunk_data = {
                "DateTime": chunk_dates,
                "value": chunk_values
            }
            all_data.append(pl.DataFrame(chunk_data))
        
        # 合并数据
        df = pl.concat(all_data)
        file_path = Path(test_data_dir) / "million_rows.csv"
        df.write_csv(file_path)
        
        # 测试处理时间
        start_time = time.time()
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "million_rows.csv"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["data"]["file_info"]["rows"] == rows
        
        processing_time = end_time - start_time
        print(f"Large dataset: {rows} rows processed in {processing_time:.1f}s")
        
        # 百万级数据应在30秒内处理完成
        assert processing_time < 30

    def test_cpu_usage_optimization(self, api_client, test_data_dir):
        """测试CPU使用优化"""
        process = psutil.Process(os.getpid())
        
        # 创建CPU密集型测试数据
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(10000)]
        }
        for j in range(1, 21):  # 20列数据
            data[f"metric_{j}"] = np.random.normal(50, 15, 10000)
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "cpu_test.csv"
        df.write_csv(file_path)
        
        # 测量CPU使用
        cpu_before = process.cpu_percent()
        
        start_time = time.time()
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "cpu_test.csv"}
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        cpu_after = process.cpu_percent()
        
        assert response.status_code == 200
        
        print(f"CPU usage: {cpu_after:.1f}%, processing time: {processing_time:.1f}s")
        
        # CPU使用率应在合理范围内
        assert processing_time < 5.0  # 5秒内完成

    def test_disk_io_performance(self, api_client, test_data_dir):
        """测试磁盘I/O性能"""
        # 创建不同大小的测试文件
        test_sizes = [1000, 10000, 50000]
        
        for rows in test_sizes:
            data = {
                "DateTime": [datetime.now() + timedelta(hours=i) for i in range(rows)],
                "value": np.random.normal(50, 15, rows)
            }
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"disk_io_{rows}.csv"
            
            # 测量写入时间
            start_time = time.time()
            df.write_csv(file_path)
            write_time = time.time() - start_time
            
            # 测量读取和处理时间
            start_time = time.time()
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"disk_io_{rows}.csv"}
            )
            read_process_time = time.time() - start_time
            
            assert response.status_code == 200
            
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            read_speed = file_size_mb / read_process_time
            
            print(f"Disk I/O: {rows} rows ({file_size_mb:.1f}MB) - write: {write_time:.2f}s, read/process: {read_process_time:.2f}s ({read_speed:.1f}MB/s)")
            
            # 磁盘I/O速度应在合理范围内
            assert read_speed > 1.0  # 至少1MB/s

    def test_scalability_analysis(self, api_client, test_data_dir):
        """测试可扩展性分析"""
        scalability_data = []
        
        test_sizes = [100, 1000, 5000, 10000, 50000]
        
        for rows in test_sizes:
            # 创建测试数据
            data = {
                "DateTime": [datetime.now() + timedelta(hours=i) for i in range(rows)],
                "value": np.random.normal(50, 15, rows)
            }
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / f"scalability_{rows}.csv"
            df.write_csv(file_path)
            
            # 测量处理时间
            start_time = time.time()
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": f"scalability_{rows}.csv"}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            
            processing_time = end_time - start_time
            scalability_data.append({
                "rows": rows,
                "time": processing_time,
                "throughput": rows / processing_time
            })
        
        # 分析可扩展性趋势
        import numpy as np
        
        rows = [d["rows"] for d in scalability_data]
        times = [d["time"] for d in scalability_data]
        
        # 计算线性回归
        coeffs = np.polyfit(rows, times, 1)
        
        print("Scalability analysis:")
        for data in scalability_data:
            print(f"  {data['rows']} rows: {data['time']:.2f}s ({data['throughput']:.0f} rows/s)")
        
        print(f"  Linear trend: time = {coeffs[0]:.6f} * rows + {coeffs[1]:.2f}")
        
        # 验证线性可扩展性（系数应接近线性）
        assert coeffs[0] < 0.001  # 每行处理时间应小于1ms


class TestMemoryProfiling:
    """内存分析测试"""

    def test_memory_profile_detailed(self, api_client, test_data_dir):
        """详细内存分析"""
        try:
            import tracemalloc
            tracemalloc.start()
            
            # 创建测试数据
            data = {
                "DateTime": [datetime.now() + timedelta(hours=i) for i in range(10000)],
                "value1": np.random.normal(50, 15, 10000),
                "value2": np.random.normal(30, 10, 10000),
                "value3": np.random.normal(20, 5, 10000),
            }
            
            df = pl.DataFrame(data)
            file_path = Path(test_data_dir) / "memory_profile.csv"
            df.write_csv(file_path)
            
            # 测量内存快照
            snapshot1 = tracemalloc.take_snapshot()
            
            response = api_client.post(
                "/api/analyze-server-file",
                data={"filename": "memory_profile.csv"}
            )
            
            snapshot2 = tracemalloc.take_snapshot()
            
            assert response.status_code == 200
            
            # 分析内存差异
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            print("Memory profiling results:")
            for stat in top_stats[:10]:
                print(f"  {stat}")
            
            tracemalloc.stop()
            
        except ImportError:
            pytest.skip("tracemalloc not available")

    def test_garbage_collection_efficiency(self, api_client, test_data_dir):
        """测试垃圾回收效率"""
        import gc
        
        # 创建测试数据
        data = {
            "DateTime": [datetime.now() + timedelta(hours=i) for i in range(5000)],
            "value": np.random.normal(50, 15, 5000)
        }
        
        df = pl.DataFrame(data)
        file_path = Path(test_data_dir) / "gc_test.csv"
        df.write_csv(file_path)
        
        # 强制垃圾回收
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # 处理数据
        response = api_client.post(
            "/api/analyze-server-file",
            data={"filename": "gc_test.csv"}
        )
        
        assert response.status_code == 200
        
        # 强制垃圾回收
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # 验证对象数量没有显著增加
        object_increase = final_objects - initial_objects
        assert abs(object_increase) < 1000  # 对象增加应小于1000个