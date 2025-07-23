# API 端点详细文档

本文档详细描述了数据分析报告系统的所有API端点。

## 文件管理 API

### 获取服务器文件列表

```http
GET /api/files
```

获取服务器上可用的数据文件列表。

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `path` | string | 否 | 指定目录路径，默认为根目录 |
| `extensions` | string | 否 | 文件扩展名过滤，多个用逗号分隔 |
| `limit` | integer | 否 | 返回文件数量限制，默认100 |

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "name": "sales_data.csv",
        "path": "/data/sales_data.csv",
        "size": 1048576,
        "modified": "2024-01-15T10:30:00Z",
        "type": "csv"
      },
      {
        "name": "user_behavior.parquet",
        "path": "/data/user_behavior.parquet",
        "size": 2097152,
        "modified": "2024-01-14T15:45:00Z",
        "type": "parquet"
      }
    ],
    "total": 2,
    "path": "/data"
  }
}
```

### 上传文件

```http
POST /api/upload
```

上传数据文件到服务器进行分析。

#### 请求体

- **Content-Type**: `multipart/form-data`
- **文件字段**: `file`
- **最大文件大小**: 100MB
- **支持格式**: CSV, Parquet

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "file_id": "upload_20240115_103000_abc123",
    "filename": "data.csv",
    "size": 1048576,
    "upload_time": "2024-01-15T10:30:00Z",
    "preview": {
      "columns": ["id", "name", "value", "date"],
      "rows": 1000,
      "sample_data": [
        {"id": 1, "name": "Product A", "value": 100.5, "date": "2024-01-01"},
        {"id": 2, "name": "Product B", "value": 200.3, "date": "2024-01-02"}
      ]
    }
  }
}
```

### 删除文件

```http
DELETE /api/files/{file_path}
```

删除服务器上的指定文件。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `file_path` | string | 要删除的文件路径 |

#### 响应示例

```json
{
  "status": "success",
  "message": "文件删除成功",
  "data": {
    "deleted_file": "/data/old_data.csv",
    "deleted_time": "2024-01-15T10:30:00Z"
  }
}
```

## 数据分析 API

### 开始数据分析

```http
POST /api/analyze
```

对指定的数据文件执行分析。

#### 请求体

```json
{
  "file_path": "/data/sales_data.csv",
  "analysis_type": "comprehensive",
  "options": {
    "include_visualization": true,
    "statistical_tests": ["normality", "correlation"],
    "chart_types": ["histogram", "scatter", "box"],
    "sample_size": 10000
  }
}
```

#### 请求参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `file_path` | string | 是 | 数据文件路径 |
| `analysis_type` | string | 否 | 分析类型：`basic`、`comprehensive`、`custom` |
| `options` | object | 否 | 分析选项配置 |

#### 分析选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `include_visualization` | boolean | true | 是否生成可视化图表 |
| `statistical_tests` | array | [] | 要执行的统计检验 |
| `chart_types` | array | ["histogram"] | 要生成的图表类型 |
| `sample_size` | integer | null | 数据采样大小 |
| `confidence_level` | float | 0.95 | 置信水平 |

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "analysis_id": "analysis_20240115_103000_xyz789",
    "file_info": {
      "name": "sales_data.csv",
      "size": 1048576,
      "rows": 1000,
      "columns": 5
    },
    "basic_stats": {
      "numeric_columns": {
        "sales_amount": {
          "count": 1000,
          "mean": 1250.75,
          "std": 450.32,
          "min": 100.0,
          "max": 5000.0,
          "q25": 800.0,
          "q50": 1200.0,
          "q75": 1600.0
        }
      },
      "categorical_columns": {
        "product_category": {
          "unique_count": 5,
          "most_frequent": "Electronics",
          "frequency": 350
        }
      }
    },
    "visualizations": [
      {
        "type": "histogram",
        "column": "sales_amount",
        "chart_data": {
          "x": [100, 200, 300, 400, 500],
          "y": [50, 120, 200, 180, 80],
          "title": "销售金额分布"
        }
      }
    ],
    "statistical_tests": {
      "normality_test": {
        "shapiro_wilk": {
          "statistic": 0.987,
          "p_value": 0.023,
          "is_normal": false
        }
      }
    },
    "insights": [
      "销售金额呈右偏分布",
      "电子产品类别占比最高（35%）",
      "存在异常值，建议进一步检查"
    ],
    "analysis_time": "2024-01-15T10:30:00Z",
    "processing_duration": 2.5
  }
}
```

### 获取分析结果

```http
GET /api/analysis/{analysis_id}
```

获取指定分析任务的结果。

#### 路径参数

| 参数 | 类型 | 描述 |
|------|------|------|
| `analysis_id` | string | 分析任务ID |

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `include_charts` | boolean | 否 | 是否包含图表数据 |
| `format` | string | 否 | 返回格式：`json`、`html` |

### 导出分析结果

```http
GET /api/analysis/{analysis_id}/export
```

导出分析结果为指定格式。

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `format` | string | 是 | 导出格式：`pdf`、`html`、`json` |
| `include_charts` | boolean | 否 | 是否包含图表 |
| `template` | string | 否 | 报告模板：`standard`、`detailed`、`summary` |

## 系统信息 API

### 获取系统状态

```http
GET /api/health
```

获取系统健康状态和基本信息。

#### 响应示例

```json
{
  "status": "healthy",
  "data": {
    "version": "0.1.0",
    "uptime": 86400,
    "memory_usage": {
      "used": 512,
      "total": 2048,
      "percentage": 25.0
    },
    "disk_usage": {
      "used": 10240,
      "total": 102400,
      "percentage": 10.0
    },
    "active_analyses": 3,
    "total_files": 150,
    "last_analysis": "2024-01-15T10:25:00Z"
  }
}
```

### 获取系统指标

```http
GET /api/metrics
```

获取详细的系统性能指标。

#### 响应示例

```json
{
  "status": "success",
  "data": {
    "performance": {
      "avg_analysis_time": 2.3,
      "requests_per_minute": 45,
      "error_rate": 0.02,
      "cache_hit_rate": 0.85
    },
    "usage_stats": {
      "total_analyses": 1250,
      "total_uploads": 890,
      "popular_file_types": {
        "csv": 65,
        "parquet": 35
      },
      "peak_usage_hour": 14
    },
    "resource_usage": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_io": {
        "read_mb_per_sec": 12.5,
        "write_mb_per_sec": 8.3
      }
    }
  }
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循统一的格式：

```json
{
  "status": "error",
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "指定的文件不存在",
    "details": {
      "file_path": "/data/missing_file.csv",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| `FILE_NOT_FOUND` | 404 | 文件不存在 |
| `FILE_TOO_LARGE` | 413 | 文件大小超过限制 |
| `INVALID_FILE_FORMAT` | 400 | 不支持的文件格式 |
| `ANALYSIS_FAILED` | 500 | 分析处理失败 |
| `INSUFFICIENT_MEMORY` | 503 | 内存不足 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `INVALID_PARAMETERS` | 400 | 请求参数无效 |

## API 使用示例

### Python 示例

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api"

def upload_and_analyze(file_path):
    """上传文件并执行分析"""
    
    # 1. 上传文件
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
        upload_result = response.json()
    
    if upload_result['status'] != 'success':
        print(f"上传失败: {upload_result['error']['message']}")
        return
    
    file_id = upload_result['data']['file_id']
    print(f"文件上传成功，ID: {file_id}")
    
    # 2. 开始分析
    analysis_request = {
        "file_path": f"/uploads/{file_id}",
        "analysis_type": "comprehensive",
        "options": {
            "include_visualization": True,
            "statistical_tests": ["normality", "correlation"],
            "chart_types": ["histogram", "scatter", "box"]
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=analysis_request,
        headers={'Content-Type': 'application/json'}
    )
    
    analysis_result = response.json()
    
    if analysis_result['status'] == 'success':
        print("分析完成！")
        print(f"分析ID: {analysis_result['data']['analysis_id']}")
        print(f"处理时间: {analysis_result['data']['processing_duration']}秒")
        
        # 打印洞察
        for insight in analysis_result['data']['insights']:
            print(f"- {insight}")
    else:
        print(f"分析失败: {analysis_result['error']['message']}")

# 使用示例
upload_and_analyze("data.csv")
```

### JavaScript 示例

```javascript
class DataAnalysisAPI {
    constructor(baseUrl = 'http://localhost:8000/api') {
        this.baseUrl = baseUrl;
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${this.baseUrl}/upload`, {
                method: 'POST',
                body: formData
            });
            
            return await response.json();
        } catch (error) {
            throw new Error(`上传失败: ${error.message}`);
        }
    }
    
    async analyzeData(filePath, options = {}) {
        const analysisRequest = {
            file_path: filePath,
            analysis_type: 'comprehensive',
            options: {
                include_visualization: true,
                statistical_tests: ['normality', 'correlation'],
                chart_types: ['histogram', 'scatter'],
                ...options
            }
        };
        
        try {
            const response = await fetch(`${this.baseUrl}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(analysisRequest)
            });
            
            return await response.json();
        } catch (error) {
            throw new Error(`分析失败: ${error.message}`);
        }
    }
    
    async getAnalysisResult(analysisId) {
        try {
            const response = await fetch(`${this.baseUrl}/analysis/${analysisId}`);
            return await response.json();
        } catch (error) {
            throw new Error(`获取结果失败: ${error.message}`);
        }
    }
}

// 使用示例
const api = new DataAnalysisAPI();

// 文件上传和分析
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        // 上传文件
        const uploadResult = await api.uploadFile(file);
        console.log('上传成功:', uploadResult);
        
        // 开始分析
        const analysisResult = await api.analyzeData(
            `/uploads/${uploadResult.data.file_id}`
        );
        console.log('分析完成:', analysisResult);
        
        // 显示结果
        displayAnalysisResults(analysisResult.data);
        
    } catch (error) {
        console.error('处理失败:', error.message);
    }
});

function displayAnalysisResults(data) {
    // 显示基本统计信息
    const statsContainer = document.getElementById('stats');
    statsContainer.innerHTML = `
        <h3>基本统计</h3>
        <p>数据行数: ${data.file_info.rows}</p>
        <p>列数: ${data.file_info.columns}</p>
        <p>处理时间: ${data.processing_duration}秒</p>
    `;
    
    // 显示洞察
    const insightsContainer = document.getElementById('insights');
    insightsContainer.innerHTML = `
        <h3>数据洞察</h3>
        <ul>
            ${data.insights.map(insight => `<li>${insight}</li>`).join('')}
        </ul>
    `;
}
```

### cURL 示例

```bash
# 上传文件
curl -X POST \
  http://localhost:8000/api/upload \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@data.csv'

# 开始分析
curl -X POST \
  http://localhost:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "file_path": "/uploads/upload_20240115_103000_abc123",
    "analysis_type": "comprehensive",
    "options": {
      "include_visualization": true,
      "statistical_tests": ["normality"],
      "chart_types": ["histogram"]
    }
  }'

# 获取分析结果
curl -X GET \
  http://localhost:8000/api/analysis/analysis_20240115_103000_xyz789

# 导出结果
curl -X GET \
  "http://localhost:8000/api/analysis/analysis_20240115_103000_xyz789/export?format=pdf" \
  -o analysis_report.pdf

# 获取系统状态
curl -X GET http://localhost:8000/api/health
```

## 最佳实践

### 1. 错误处理

```python
def safe_api_call(func, *args, **kwargs):
    """安全的API调用包装器"""
    try:
        response = func(*args, **kwargs)
        if response.status_code >= 400:
            error_data = response.json()
            raise APIError(
                error_data['error']['code'],
                error_data['error']['message']
            )
        return response.json()
    except requests.RequestException as e:
        raise ConnectionError(f"网络连接失败: {e}")
    except json.JSONDecodeError:
        raise ValueError("响应格式错误")
```

### 2. 异步处理

```python
import asyncio
import aiohttp

async def async_analyze_multiple_files(file_paths):
    """异步分析多个文件"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_path in file_paths:
            task = analyze_file_async(session, file_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def analyze_file_async(session, file_path):
    """异步分析单个文件"""
    analysis_request = {
        "file_path": file_path,
        "analysis_type": "basic"
    }
    
    async with session.post(
        f"{BASE_URL}/analyze",
        json=analysis_request
    ) as response:
        return await response.json()
```

### 3. 进度监控

```javascript
class AnalysisProgressMonitor {
    constructor(analysisId, onProgress, onComplete) {
        this.analysisId = analysisId;
        this.onProgress = onProgress;
        this.onComplete = onComplete;
        this.pollInterval = 1000; // 1秒
    }
    
    start() {
        this.poll();
    }
    
    async poll() {
        try {
            const response = await fetch(
                `/api/analysis/${this.analysisId}/status`
            );
            const data = await response.json();
            
            if (data.status === 'completed') {
                this.onComplete(data);
            } else if (data.status === 'failed') {
                throw new Error(data.error.message);
            } else {
                this.onProgress(data.progress);
                setTimeout(() => this.poll(), this.pollInterval);
            }
        } catch (error) {
            console.error('监控失败:', error);
        }
    }
}

// 使用示例
const monitor = new AnalysisProgressMonitor(
    'analysis_123',
    (progress) => {
        console.log(`分析进度: ${progress}%`);
        updateProgressBar(progress);
    },
    (result) => {
        console.log('分析完成:', result);
        displayResults(result);
    }
);

monitor.start();
```

## 性能优化建议

1. **批量处理**: 对于多个小文件，考虑使用批量分析API
2. **缓存结果**: 相同文件的分析结果会被缓存，避免重复计算
3. **分页查询**: 使用分页参数获取大量数据
4. **压缩传输**: 启用gzip压缩减少传输时间
5. **异步处理**: 对于大文件分析，使用异步模式避免超时

## 安全注意事项

1. **文件验证**: 上传前验证文件类型和大小
2. **路径安全**: 避免路径遍历攻击
3. **频率限制**: 遵守API调用频率限制
4. **数据清理**: 及时清理临时文件和分析结果
5. **错误信息**: 不要在客户端暴露敏感的错误信息