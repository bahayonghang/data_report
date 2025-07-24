# API 数据模型

本文档定义了在数据分析报告系统的 API 中使用的核心数据结构。了解这些模型有助于您更好地理解 API 的请求和响应格式。

## 核心模型

### `FileRecord`

代表一个已上传的文件记录。

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `id` | integer | 文件的唯一标识符。 |
| `filename` | string | 用户上传时的原始文件名。 |
| `file_type` | string | 文件的类型（例如，`csv`, `parquet`）。 |
| `file_size` | integer | 文件大小（以字节为单位）。 |
| `file_hash` | string | 文件的 SHA256 哈希值，用于识别重复文件。 |
| `file_path` | string | 文件在服务器上的存储路径。 |
| `created_at` | string | 文件上传的时间戳 (ISO 8601)。 |
| `status` | string | 文件的状态（例如，`completed`, `failed`）。 |

**示例**

```json
{
  "id": 1,
  "filename": "sales_data_2023.csv",
  "file_type": "csv",
  "file_size": 20480,
  "file_hash": "a1b2c3d4...",
  "file_path": "/data/uploads/a1b2c3d4...csv",
  "created_at": "2023-10-27T10:00:00Z",
  "status": "completed"
}
```

---

### `AnalysisRecord`

代表一次分析任务的记录。

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `id` | integer | 分析记录的唯一标识符。 |
| `file_id` | integer | 关联的 `FileRecord` 的 ID。 |
| `analysis_time` | string | 分析完成的时间戳 (ISO 8601)。 |
| `result_file_path` | string | 存储分析结果的 JSON 文件的路径。 |

**示例**

```json
{
  "id": 1,
  "file_id": 1,
  "analysis_time": "2023-10-27T10:05:00Z",
  "result_file_path": "/data/analysis_results/1.json"
}
```

---

### `AnalysisResult`

包含一次完整数据分析的结果。这是 `POST /api/upload-and-analyze` 和 `GET /api/analysis/{analysis_id}/result` 等端点返回的主要数据结构。

| 字段 | 类型 | 描述 |
| :--- | :--- | :--- |
| `file_info` | object | 包含文件元信息，如名称、行数和列数。 |
| `time_info` | object | 时间序列信息，包括识别出的时间列和时间范围。 |
| `statistics` | object | 描述性统计结果。 |
| `missing_values` | object | 缺失值分析结果。 |
| `correlation_matrix` | object | 数值列之间的相关性矩阵。 |
| `stationarity_tests` | object | 时间序列的平稳性检验结果 (ADF Test)。 |
| `visualizations` | object | 包含多个图表的 JSON 定义。 |
| `from_history` | boolean | 指示结果是否来自缓存的历史记录。 |
| `file_id` | integer | 关联的 `FileRecord` 的 ID。 |
| `analysis_id` | integer | 关联的 `AnalysisRecord` 的 ID。 |

**示例**

```json
{
  "success": true,
  "data": {
    "file_info": {
      "name": "sample_data.csv",
      "rows": 1000,
      "columns": 5
    },
    "time_info": {
      "time_column": "Date",
      "time_range": {
        "start": "2023-01-01T00:00:00Z",
        "end": "2023-12-31T23:59:59Z"
      }
    },
    "statistics": { ... },
    "missing_values": { ... },
    "correlation_matrix": { ... },
    "stationarity_tests": { ... },
    "visualizations": {
      "time_series": { ... },
      "correlation_heatmap": { ... }
    }
  },
  "from_history": false,
  "file_id": 1,
  "analysis_id": 1
}
```

---

## 枚举类型

### `FileType`

文件的类型。

- `csv`
- `parquet`

### `AnalysisStatus`

分析任务的状态。

- `pending`: 等待处理
- `running`: 正在处理
- `completed`: 已完成
- `failed`: 已失败
