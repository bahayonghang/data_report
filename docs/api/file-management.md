# 文件管理 API

本文档详细描述数据分析报告系统的文件管理相关API端点，包括文件上传、下载、删除和管理功能。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (可选)
- **内容类型**: `application/json` 或 `multipart/form-data`

## 文件上传

### 上传单个文件

```http
POST /files/upload
Content-Type: multipart/form-data
```

#### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file | File | 是 | 要上传的文件 |
| description | string | 否 | 文件描述 |
| tags | string | 否 | 文件标签，逗号分隔 |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.csv" \
  -F "description=Sales data for Q1 2024" \
  -F "tags=sales,quarterly,2024"
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "filename": "data.csv",
    "original_filename": "sales_data_q1.csv",
    "size": 1048576,
    "mime_type": "text/csv",
    "rows": 1500,
    "columns": 8,
    "column_info": {
      "date": "datetime",
      "product_id": "string",
      "quantity": "integer",
      "price": "float",
      "customer_id": "string",
      "region": "string",
      "sales_rep": "string",
      "total": "float"
    },
    "description": "Sales data for Q1 2024",
    "tags": ["sales", "quarterly", "2024"],
    "upload_time": "2024-01-15T10:30:00Z",
    "status": "ready",
    "hash": "sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
  }
}
```

### 批量上传文件

```http
POST /files/upload/batch
Content-Type: multipart/form-data
```

#### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| files | File[] | 是 | 要上传的文件数组 |
| batch_description | string | 否 | 批次描述 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "batch_id": "b47ac10b-58cc-4372-a567-0e02b2c3d480",
    "uploaded_files": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "filename": "data1.csv",
        "status": "success"
      },
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d481",
        "filename": "data2.csv",
        "status": "success"
      }
    ],
    "failed_files": [],
    "total_files": 2,
    "successful_uploads": 2,
    "failed_uploads": 0
  }
}
```

## 文件查询

### 获取文件列表

```http
GET /files
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 20 | 每页数量 |
| sort_by | string | 否 | upload_time | 排序字段 |
| sort_order | string | 否 | desc | 排序方向 (asc/desc) |
| search | string | 否 | - | 搜索关键词 |
| tags | string | 否 | - | 标签过滤，逗号分隔 |
| file_type | string | 否 | - | 文件类型过滤 |
| date_from | string | 否 | - | 开始日期 (ISO 8601) |
| date_to | string | 否 | - | 结束日期 (ISO 8601) |

#### 请求示例

```bash
curl "http://localhost:8000/api/v1/files?page=1&limit=10&search=sales&tags=quarterly"
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "filename": "data.csv",
        "original_filename": "sales_data_q1.csv",
        "size": 1048576,
        "mime_type": "text/csv",
        "rows": 1500,
        "columns": 8,
        "description": "Sales data for Q1 2024",
        "tags": ["sales", "quarterly", "2024"],
        "upload_time": "2024-01-15T10:30:00Z",
        "last_accessed": "2024-01-15T14:20:00Z",
        "status": "ready",
        "analysis_count": 3
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 5,
      "total_items": 87,
      "items_per_page": 20,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 获取文件详情

```http
GET /files/{file_id}
```

#### 路径参数

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file_id | string | 是 | 文件ID |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "filename": "data.csv",
    "original_filename": "sales_data_q1.csv",
    "size": 1048576,
    "mime_type": "text/csv",
    "rows": 1500,
    "columns": 8,
    "column_info": {
      "date": {
        "type": "datetime",
        "nullable": false,
        "unique_values": 90,
        "sample_values": ["2024-01-01", "2024-01-02", "2024-01-03"]
      },
      "product_id": {
        "type": "string",
        "nullable": false,
        "unique_values": 25,
        "sample_values": ["PROD001", "PROD002", "PROD003"]
      },
      "quantity": {
        "type": "integer",
        "nullable": false,
        "min_value": 1,
        "max_value": 100,
        "mean": 15.5
      },
      "price": {
        "type": "float",
        "nullable": false,
        "min_value": 9.99,
        "max_value": 999.99,
        "mean": 125.75
      }
    },
    "description": "Sales data for Q1 2024",
    "tags": ["sales", "quarterly", "2024"],
    "upload_time": "2024-01-15T10:30:00Z",
    "last_accessed": "2024-01-15T14:20:00Z",
    "last_modified": "2024-01-15T10:30:00Z",
    "status": "ready",
    "hash": "sha256:a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "analysis_history": [
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
        "analysis_type": "basic_stats",
        "created_at": "2024-01-15T11:00:00Z",
        "status": "completed"
      }
    ],
    "data_quality": {
      "completeness": 0.98,
      "consistency": 0.95,
      "validity": 0.99,
      "missing_values": 30,
      "duplicate_rows": 5
    }
  }
}
```

### 获取文件预览

```http
GET /files/{file_id}/preview
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| rows | integer | 否 | 10 | 预览行数 |
| columns | string | 否 | - | 指定列名，逗号分隔 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "preview_data": [
      {
        "date": "2024-01-01",
        "product_id": "PROD001",
        "quantity": 10,
        "price": 99.99,
        "customer_id": "CUST001",
        "region": "North",
        "sales_rep": "John Doe",
        "total": 999.90
      },
      {
        "date": "2024-01-01",
        "product_id": "PROD002",
        "quantity": 5,
        "price": 149.99,
        "customer_id": "CUST002",
        "region": "South",
        "sales_rep": "Jane Smith",
        "total": 749.95
      }
    ],
    "total_rows": 1500,
    "preview_rows": 10,
    "columns": ["date", "product_id", "quantity", "price", "customer_id", "region", "sales_rep", "total"]
  }
}
```

## 文件下载

### 下载原始文件

```http
GET /files/{file_id}/download
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| format | string | 否 | original | 下载格式 (original/csv/parquet/excel) |

#### 请求示例

```bash
curl -O "http://localhost:8000/api/v1/files/f47ac10b-58cc-4372-a567-0e02b2c3d479/download"
```

#### 响应

- **成功**: 返回文件内容，Content-Type根据文件类型设置
- **失败**: 返回JSON错误信息

### 下载处理后的数据

```http
GET /files/{file_id}/export
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| format | string | 否 | csv | 导出格式 (csv/parquet/excel/json) |
| columns | string | 否 | - | 指定列名，逗号分隔 |
| filters | string | 否 | - | 数据过滤条件 (JSON格式) |
| limit | integer | 否 | - | 限制行数 |

#### 请求示例

```bash
curl "http://localhost:8000/api/v1/files/f47ac10b-58cc-4372-a567-0e02b2c3d479/export?format=excel&columns=date,product_id,total&limit=1000"
```

## 文件管理

### 更新文件信息

```http
PUT /files/{file_id}
Content-Type: application/json
```

#### 请求体

```json
{
  "description": "Updated sales data for Q1 2024",
  "tags": ["sales", "quarterly", "2024", "updated"]
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "description": "Updated sales data for Q1 2024",
    "tags": ["sales", "quarterly", "2024", "updated"],
    "last_modified": "2024-01-15T15:30:00Z"
  }
}
```

### 删除文件

```http
DELETE /files/{file_id}
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| force | boolean | 否 | false | 强制删除（忽略依赖检查） |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "message": "File deleted successfully",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "deleted_at": "2024-01-15T16:00:00Z"
  }
}
```

### 批量删除文件

```http
DELETE /files/batch
Content-Type: application/json
```

#### 请求体

```json
{
  "file_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "f47ac10b-58cc-4372-a567-0e02b2c3d481"
  ],
  "force": false
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "deleted_files": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "status": "deleted"
      },
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d481",
        "status": "deleted"
      }
    ],
    "failed_deletions": [],
    "total_requested": 2,
    "successful_deletions": 2,
    "failed_deletions_count": 0
  }
}
```

## 文件统计

### 获取文件统计信息

```http
GET /files/stats
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| period | string | 否 | 30d | 统计周期 (7d/30d/90d/1y) |
| group_by | string | 否 | day | 分组方式 (day/week/month) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_files": 156,
      "total_size": 2147483648,
      "total_rows": 1250000,
      "avg_file_size": 13765248,
      "most_common_type": "csv",
      "upload_trend": "increasing"
    },
    "by_type": {
      "csv": {
        "count": 89,
        "total_size": 1073741824,
        "percentage": 57.1
      },
      "parquet": {
        "count": 45,
        "total_size": 805306368,
        "percentage": 28.8
      },
      "excel": {
        "count": 22,
        "total_size": 268435456,
        "percentage": 14.1
      }
    },
    "upload_timeline": [
      {
        "date": "2024-01-01",
        "count": 5,
        "size": 52428800
      },
      {
        "date": "2024-01-02",
        "count": 8,
        "size": 83886080
      }
    ],
    "top_tags": [
      {
        "tag": "sales",
        "count": 45
      },
      {
        "tag": "quarterly",
        "count": 32
      },
      {
        "tag": "2024",
        "count": 89
      }
    ]
  }
}
```

## 文件搜索

### 高级搜索

```http
POST /files/search
Content-Type: application/json
```

#### 请求体

```json
{
  "query": {
    "text": "sales data",
    "tags": ["quarterly", "2024"],
    "file_types": ["csv", "excel"],
    "size_range": {
      "min": 1048576,
      "max": 104857600
    },
    "date_range": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-12-31T23:59:59Z"
    },
    "columns": ["date", "product_id", "total"],
    "row_count_range": {
      "min": 100,
      "max": 10000
    }
  },
  "sort": {
    "field": "upload_time",
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "limit": 20
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "filename": "data.csv",
        "relevance_score": 0.95,
        "match_highlights": {
          "description": "<mark>Sales data</mark> for Q1 2024",
          "tags": ["sales", "<mark>quarterly</mark>", "<mark>2024</mark>"]
        }
      }
    ],
    "total_results": 23,
    "search_time_ms": 45,
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## 错误响应

### 错误格式

```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "The specified file was not found",
    "details": {
      "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    },
    "timestamp": "2024-01-15T16:30:00Z"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| FILE_NOT_FOUND | 404 | 文件不存在 |
| FILE_TOO_LARGE | 413 | 文件大小超过限制 |
| INVALID_FILE_TYPE | 400 | 不支持的文件类型 |
| UPLOAD_FAILED | 500 | 文件上传失败 |
| PERMISSION_DENIED | 403 | 权限不足 |
| QUOTA_EXCEEDED | 429 | 存储配额超限 |
| INVALID_PARAMETERS | 400 | 请求参数无效 |
| SERVER_ERROR | 500 | 服务器内部错误 |

## 限制和配额

### 文件限制

| 限制类型 | 值 | 描述 |
|----------|----|----- |
| 最大文件大小 | 500MB | 单个文件最大大小 |
| 支持格式 | CSV, Parquet, Excel, JSON | 支持的文件格式 |
| 最大列数 | 1000 | 单个文件最大列数 |
| 最大行数 | 1,000,000 | 单个文件最大行数 |
| 并发上传 | 5 | 同时上传文件数量 |

### 存储配额

| 用户类型 | 存储空间 | 文件数量 | 保留期限 |
|----------|----------|----------|----------|
| 免费用户 | 1GB | 100 | 30天 |
| 基础用户 | 10GB | 1000 | 90天 |
| 高级用户 | 100GB | 10000 | 365天 |
| 企业用户 | 无限制 | 无限制 | 自定义 |

## SDK 示例

### Python SDK

```python
from data_report_client import DataReportClient

# 初始化客户端
client = DataReportClient(base_url="http://localhost:8000/api/v1")

# 上传文件
with open("data.csv", "rb") as f:
    result = client.files.upload(
        file=f,
        description="Sales data for Q1 2024",
        tags=["sales", "quarterly", "2024"]
    )
    file_id = result.data.file_id

# 获取文件信息
file_info = client.files.get(file_id)
print(f"File has {file_info.data.rows} rows and {file_info.data.columns} columns")

# 下载文件
client.files.download(file_id, "downloaded_data.csv")

# 删除文件
client.files.delete(file_id)
```

### JavaScript SDK

```javascript
import { DataReportClient } from '@data-report/client';

// 初始化客户端
const client = new DataReportClient({
  baseURL: 'http://localhost:8000/api/v1'
});

// 上传文件
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const uploadResult = await client.files.upload({
  file: file,
  description: 'Sales data for Q1 2024',
  tags: ['sales', 'quarterly', '2024']
});

const fileId = uploadResult.data.file_id;

// 获取文件列表
const fileList = await client.files.list({
  page: 1,
  limit: 10,
  search: 'sales'
});

console.log(`Found ${fileList.data.pagination.total_items} files`);

// 删除文件
await client.files.delete(fileId);
```

通过这些API端点，您可以完整地管理数据分析报告系统中的文件，包括上传、查询、下载和删除等操作。