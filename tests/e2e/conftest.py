"""
Pytest配置和fixture
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import numpy as np
import asyncio
import subprocess
import time
import requests


@pytest.fixture(scope="session")
def server_url():
    """启动测试服务器"""
    # 启动FastAPI测试服务器
    import subprocess
    import os
    
    # 设置测试环境
    test_dir = tempfile.mkdtemp()
    os.environ["DATA_DIRECTORY"] = test_dir
    
    # 启动服务器
    cmd = ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
    server_process = subprocess.Popen(cmd, cwd=Path(__file__).parent.parent.parent)
    
    # 等待服务器启动
    for _ in range(30):
        try:
            response = requests.get("http://localhost:8001/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        server_process.terminate()
        raise RuntimeError("测试服务器启动失败")
    
    yield "http://localhost:8001"
    
    # 清理
    server_process.terminate()
    server_process.wait()
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def test_data_dir():
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
def sample_csv_data():
    """生成示例CSV数据"""
    start_date = datetime.now() - timedelta(days=30)
    dates = [start_date + timedelta(hours=i) for i in range(720)]
    
    data = {
        "DateTime": dates,
        "temperature": 20 + 5 * np.sin(np.arange(720) * 2 * np.pi / 24) + np.random.normal(0, 0.5, 720),
        "humidity": 60 + 10 * np.sin(np.arange(720) * 2 * np.pi / 12) + np.random.normal(0, 1, 720),
        "pressure": 1013 + 5 * np.sin(np.arange(720) * 2 * np.pi / 48) + np.random.normal(0, 0.2, 720),
    }
    
    df = pl.DataFrame(data)
    return df


@pytest.fixture
def sample_parquet_data():
    """生成示例Parquet数据"""
    start_date = datetime.now() - timedelta(days=10)
    dates = [start_date + timedelta(minutes=i * 15) for i in range(960)]
    
    data = {
        "tagTime": dates,
        "sensor1": 100 + 50 * np.sin(np.arange(960) * 2 * np.pi / 96) + np.random.normal(0, 2, 960),
        "sensor2": 200 + 30 * np.sin(np.arange(960) * 2 * np.pi / 48) + np.random.normal(0, 1, 960),
        "sensor3": 50 + 25 * np.sin(np.arange(960) * 2 * np.pi / 24) + np.random.normal(0, 0.5, 960),
    }
    
    df = pl.DataFrame(data)
    return df


@pytest.fixture
def edge_case_data():
    """生成边界条件测试数据"""
    return {
        "empty": {
            "DateTime": [],
            "value": []
        },
        "single_row": {
            "DateTime": [datetime.now()],
            "value": [1.0]
        },
        "all_nulls": {
            "DateTime": [datetime.now(), datetime.now() + timedelta(hours=1)],
            "value": [None, None]
        },
        "mixed_types": {
            "DateTime": [datetime.now(), datetime.now() + timedelta(hours=1)],
            "numeric": [1.5, 2.5],
            "text": ["a", "b"]
        }
    }


@pytest.fixture
def performance_data():
    """生成性能测试数据"""
    def generate(rows: int, columns: int = 5):
        start_date = datetime.now() - timedelta(days=365)
        dates = [start_date + timedelta(minutes=i) for i in range(rows)]
        
        data = {"DateTime": dates}
        for i in range(1, columns + 1):
            data[f"metric{i}"] = np.random.normal(50, 15, rows)
        
        return pl.DataFrame(data)
    
    return generate


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def api_client():
    """创建API测试客户端"""
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app)


@pytest.fixture
def playwright_config():
    """Playwright配置"""
    return {
        "viewport": {"width": 1280, "height": 720},
        "screenshot": "only-on-failure",
        "video": "retain-on-failure",
        "trace": "on-first-retry",
    }