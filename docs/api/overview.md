# API 文档概览

数据分析报告系统提供RESTful API接口，支持文件管理和数据分析功能。所有API都遵循OpenAPI 3.0规范，并提供自动生成的交互式文档。

## API 基础信息

### 基础URL
```
开发环境: http://localhost:8000
生产环境: https://your-domain.com
```

### API版本
- **当前版本**: v1
- **API前缀**: `/api`
- **文档地址**: `/docs` (Swagger UI)
- **ReDoc地址**: `/redoc`

### 认证方式
当前版本暂不需要认证，未来版本将支持：
- API Key认证
- JWT Token认证
- OAuth 2.0认证

## API 端点概览

### 文件管理 API

| 方法 | 端点 | 描述 | 状态 |
|------|------|------|------|
| GET | `/api/list-files` | 获取服务器文件列表 | ✅ 已实现 |
| POST | `/api/upload` | 上传文件到服务器 | 🚧 计划中 |
| DELETE | `/api/files/{filename}` | 删除服务器文件 | 🚧 计划中 |

### 数据分析 API

| 方法 | 端点 | 描述 | 状态 |
|------|------|------|------|
| POST | `/api/analyze-server-file` | 分析服务器文件 | ✅ 已实现 |
| POST | `/api/upload-and-analyze` | 上传并分析文件 | ✅ 已实现 |
| GET | `/api/analysis/{analysis_id}` | 获取分析结果 | 🚧 计划中 |
| GET | `/api/analysis/{analysis_id}/export` | 导出分析结果 | 🚧 计划中 |

### 系统信息 API

| 方法 | 端点 | 描述 | 状态 |
|------|------|------|------|
| GET | `/api/health` | 系统健康检查 | 🚧 计划中 |
| GET | `/api/metrics` | 系统指标 | 🚧 计划中 |
| GET | `/api/version` | 系统版本信息 | 🚧 计划中 |

## 数据格式

### 请求格式
- **Content-Type**: `application/json` 或 `multipart/form-data`
- **字符编码**: UTF-8
- **日期格式**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)

### 响应格式
所有API响应都使用统一的JSON格式：

```json
{
  "success": true,
  "data": {
    // 具体数据内容
  },
  "message": "操作成功",
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

### 错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "输入数据验证失败",
    "details": {
      "field": "file_path",
      "reason": "文件路径不能为空"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

## HTTP状态码

### 成功状态码
| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 202 | Accepted | 请求已接受，正在处理 |
| 204 | No Content | 请求成功，无返回内容 |

### 客户端错误状态码
| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未授权访问 |
| 403 | Forbidden | 禁止访问 |
| 404 | Not Found | 资源不存在 |
| 413 | Payload Too Large | 文件过大 |
| 415 | Unsupported Media Type | 不支持的文件类型 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 429 | Too Many Requests | 请求频率过高 |

### 服务器错误状态码
| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 500 | Internal Server Error | 服务器内部错误 |
| 502 | Bad Gateway | 网关错误 |
| 503 | Service Unavailable | 服务不可用 |
| 504 | Gateway Timeout | 网关超时 |

## 请求限制

### 文件上传限制
- **最大文件大小**: 100MB
- **支持格式**: CSV, Parquet
- **并发上传**: 最多5个文件同时上传
- **超时时间**: 300秒

### 请求频率限制
- **每分钟**: 100次请求
- **每小时**: 1000次请求
- **每天**: 10000次请求

### 数据处理限制
- **最大行数**: 1,000,000行
- **最大列数**: 1,000列
- **内存限制**: 2GB per request
- **处理超时**: 600秒

## 数据模型

### 文件信息模型
```json
{
  "name": "sample_data.csv",
  "path": "/data/sample_data.csv",
  "size": 1048576,
  "modified_time": "2024-01-01T12:00:00Z",
  "file_type": "csv",
  "is_readable": true
}
```

### 分析请求模型
```json
{
  "file_path": "/data/sample_data.csv",
  "analysis_options": {
    "include_statistics": true,
    "include_charts": true,
    "time_column": "DateTime",
    "target_columns": ["value1", "value2"]
  }
}
```

### 分析结果模型
```json
{
  "file_info": {
    "name": "sample_data.csv",
    "rows": 1000,
    "columns": 5,
    "size_mb": 1.5
  },
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "duration_days": 31
  },
  "statistics": {
    "descriptive": {
      "value1": {
        "count": 1000,
        "mean": 10.5,
        "std": 2.3,
        "min": 5.2,
        "max": 18.7,
        "median": 10.2
      }
    },
    "correlation_matrix": {
      "value1": {"value1": 1.0, "value2": 0.75},
      "value2": {"value1": 0.75, "value2": 1.0}
    },
    "missing_values": {
      "value1": 5,
      "value2": 3
    }
  },
  "time_series_analysis": {
    "stationarity_test": {
      "adf_statistic": -3.45,
      "p_value": 0.01,
      "is_stationary": true
    }
  },
  "charts": {
    "time_series": {
      "type": "line",
      "data": {...},
      "layout": {...}
    },
    "correlation_heatmap": {
      "type": "heatmap",
      "data": {...},
      "layout": {...}
    }
  }
}
```

## 错误代码

### 文件相关错误
| 错误代码 | 描述 | HTTP状态码 |
|----------|------|------------|
| FILE_NOT_FOUND | 文件不存在 | 404 |
| FILE_TOO_LARGE | 文件过大 | 413 |
| INVALID_FILE_TYPE | 不支持的文件类型 | 415 |
| FILE_CORRUPTED | 文件损坏 | 422 |
| PATH_TRAVERSAL | 路径遍历攻击 | 403 |

### 数据处理错误
| 错误代码 | 描述 | HTTP状态码 |
|----------|------|------------|
| PARSING_ERROR | 数据解析失败 | 422 |
| MEMORY_EXCEEDED | 内存超限 | 413 |
| PROCESSING_TIMEOUT | 处理超时 | 504 |
| INVALID_DATA_FORMAT | 数据格式错误 | 422 |
| MISSING_TIME_COLUMN | 缺少时间列 | 422 |

### 系统错误
| 错误代码 | 描述 | HTTP状态码 |
|----------|------|------------|
| INTERNAL_ERROR | 内部服务器错误 | 500 |
| SERVICE_UNAVAILABLE | 服务不可用 | 503 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 |
| VALIDATION_ERROR | 输入验证失败 | 400 |

## API使用示例

### Python客户端示例
```python
import requests
import json

class DataReportClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def list_files(self):
        """获取文件列表"""
        response = self.session.get(f"{self.base_url}/api/list-files")
        response.raise_for_status()
        return response.json()
    
    def analyze_file(self, file_path, options=None):
        """分析服务器文件"""
        data = {"file_path": file_path}
        if options:
            data["analysis_options"] = options
        
        response = self.session.post(
            f"{self.base_url}/api/analyze-server-file",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def upload_and_analyze(self, file_path, options=None):
        """上传并分析文件"""
        files = {"file": open(file_path, "rb")}
        data = {}
        if options:
            data["analysis_options"] = json.dumps(options)
        
        response = self.session.post(
            f"{self.base_url}/api/upload-and-analyze",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()

# 使用示例
client = DataReportClient()

# 获取文件列表
files = client.list_files()
print(f"可用文件: {len(files['data'])}个")

# 分析文件
result = client.analyze_file("/data/sample_data.csv")
print(f"分析完成，包含{len(result['data']['charts'])}个图表")
```

### JavaScript客户端示例
```javascript
class DataReportClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async listFiles() {
        const response = await fetch(`${this.baseUrl}/api/list-files`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
    
    async analyzeFile(filePath, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/analyze-server-file`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_path: filePath,
                analysis_options: options
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
    
    async uploadAndAnalyze(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        if (Object.keys(options).length > 0) {
            formData.append('analysis_options', JSON.stringify(options));
        }
        
        const response = await fetch(`${this.baseUrl}/api/upload-and-analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// 使用示例
const client = new DataReportClient();

// 获取文件列表
client.listFiles()
    .then(result => {
        console.log(`可用文件: ${result.data.length}个`);
    })
    .catch(error => {
        console.error('获取文件列表失败:', error);
    });
```

### cURL示例
```bash
# 获取文件列表
curl -X GET "http://localhost:8000/api/list-files" \
     -H "Accept: application/json"

# 分析服务器文件
curl -X POST "http://localhost:8000/api/analyze-server-file" \
     -H "Content-Type: application/json" \
     -d '{
       "file_path": "/data/sample_data.csv",
       "analysis_options": {
         "include_statistics": true,
         "include_charts": true
       }
     }'

# 上传并分析文件
curl -X POST "http://localhost:8000/api/upload-and-analyze" \
     -F "file=@sample_data.csv" \
     -F 'analysis_options={"include_statistics": true}'
```

## 最佳实践

### 错误处理
```python
try:
    result = client.analyze_file("/data/sample.csv")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("文件不存在")
    elif e.response.status_code == 413:
        print("文件过大")
    else:
        print(f"请求失败: {e.response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"网络错误: {e}")
```

### 异步处理
```python
import asyncio
import aiohttp

async def analyze_multiple_files(file_paths):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for file_path in file_paths:
            task = analyze_file_async(session, file_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### 进度监控
```javascript
// 使用Server-Sent Events监控长时间运行的分析任务
const eventSource = new EventSource('/api/analysis/progress/123');
eventSource.onmessage = function(event) {
    const progress = JSON.parse(event.data);
    console.log(`分析进度: ${progress.percentage}%`);
};
```

## 下一步

- 查看[文件管理API](file-management.md)详细文档
- 了解[数据分析API](data-analysis.md)使用方法
- 阅读[错误处理指南](error-handling.md)
- 参考[API测试指南](../development/testing.md)