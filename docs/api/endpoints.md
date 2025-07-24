# API 端点详解

本文档详细描述了数据分析报告系统中可用的每个 API 端点，包括其功能、请求参数、响应格式和使用示例。

## 文件上传与分析

### `POST /api/upload-and-analyze`

上传一个数据文件（CSV 或 Parquet），系统将对其进行分析。如果文件内容之前已被分析过，将直接返回缓存的历史结果。

**请求体**

- **Content-Type**: `multipart/form-data`
- **参数**:
    - `file`: 要上传的数据文件。

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "file_info": {
      "name": "sample_data.csv",
      "rows": 1000,
      "columns": 5
    },
    "statistics": { ... },
    "missing_values": { ... },
    "correlation_matrix": { ... },
    "stationarity_tests": { ... },
    "visualizations": { ... },
    "from_history": false,
    "file_id": 1,
    "analysis_id": 1
  }
}
```

**失败响应**

- `400 Bad Request`: 不支持的文件类型。
- `413 Payload Too Large`: 文件大小超过限制。
- `500 Internal Server Error`: 分析过程中发生未知错误。

**cURL 示例**

```bash
curl -X POST -F "file=@/path/to/your/data.csv" http://localhost:8000/api/upload-and-analyze
```

---

## 历史记录查询

### `GET /api/file-history`

获取已上传文件的历史记录列表，支持分页和过滤。

**查询参数**

- `filter` (string, optional): 按文件类型过滤，可选值为 `csv` 或 `parquet`。默认为 `all`。
- `limit` (integer, optional): 每页返回的记录数。默认为 `20`。
- `offset` (integer, optional): 查询结果的偏移量。默认为 `0`。
- `page` (integer, optional): 页码，如果提供，将覆盖 `offset`。

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 1,
        "filename": "sample_data.csv",
        "file_type": "csv",
        "file_size": 10240,
        "created_at": "2023-10-27T10:00:00Z",
        "status": "completed"
      }
    ],
    "has_more": true
  }
}
```

**cURL 示例**

```bash
curl "http://localhost:8000/api/file-history?filter=csv&limit=10&page=1"
```

---

### `GET /api/files/{file_id}/analysis`

获取特定文件的所有分析历史记录。

**路径参数**

- `file_id` (integer, required): 文件的唯一 ID。

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "file_id": 1,
    "analyses": [
      {
        "id": 1,
        "analysis_time": "2023-10-27T10:05:00Z",
        "result_file_path": "/path/to/result.json"
      }
    ]
  }
}
```

**cURL 示例**

```bash
curl http://localhost:8000/api/files/1/analysis
```

---

### `GET /api/analysis/{analysis_id}/result`

获取某次特定分析的详细结果。

**路径参数**

- `analysis_id` (integer, required): 分析记录的唯一 ID。

**成功响应 (200 OK)**

返回与 `POST /api/upload-and-analyze` 相同的分析结果结构。

```json
{
  "success": true,
  "data": { ... },
  "from_history": true,
  "analysis_id": 1,
  "file_id": 1
}
```

**失败响应**

- `404 Not Found`: 分析记录或结果文件不存在。

**cURL 示例**

```bash
curl http://localhost:8000/api/analysis/1/result
```

---

### `GET /api/history/{history_id}`

获取指定历史记录（文件）的最新分析结果。

**路径参数**

- `history_id` (integer, required): 历史记录的唯一 ID（即 `file_id`）。

**成功响应 (200 OK)**

返回与 `POST /api/upload-and-analyze` 相同的分析结果结构。

**失败响应**

- `404 Not Found`: 文件记录或分析结果不存在。

**cURL 示例**

```bash
curl http://localhost:8000/api/history/1
```

---

### `DELETE /api/history/{history_id}`

删除一个历史记录及其关联的分析结果和文件。

**路径参数**

- `history_id` (integer, required): 要删除的历史记录的唯一 ID。

**成功响应 (200 OK)**

```json
{
  "success": true,
  "message": "历史记录删除成功"
}
```

**失败响应**

- `404 Not Found`: 要删除的历史记录不存在。
- `500 Internal Server Error`: 删除过程中发生错误。

**cURL 示例**

```bash
curl -X DELETE http://localhost:8000/api/history/1
```

---

## 文件搜索

### `POST /api/search`

根据关键词搜索已上传的文件。

**请求体**

```json
{
  "query": "your_search_keyword"
}
```

**成功响应 (200 OK)**

```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "filename": "sample_data.csv",
      "file_type": "csv",
      "file_size": 10240,
      "created_at": "2023-10-27T10:00:00Z",
      "relevance": 1.0,
      "snippet": "文件大小: 10240 字节"
    }
  ]
}
```

**cURL 示例**

```bash
curl -X POST -H "Content-Type: application/json" \
-d '{"query": "sample"}' http://localhost:8000/api/search
```

---

## 存储管理

### `GET /api/storage/stats`

获取文件存储的统计信息。

**成功响应 (200 OK)**

```json
{
  "success": true,
  "data": {
    "total_files": 10,
    "total_size_mb": 50.5,
    "file_types": {
      "csv": 8,
      "parquet": 2
    },
    "latest_upload": "2023-10-27T12:00:00Z"
  }
}
```

**cURL 示例**

```bash
curl http://localhost:8000/api/storage/stats
```