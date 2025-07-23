# 分析 API

本文档详细描述数据分析报告系统的数据分析相关API端点，包括统计分析、相关性分析、分布分析等功能。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (可选)
- **内容类型**: `application/json`

## 分析任务管理

### 创建分析任务

```http
POST /analysis/create
Content-Type: application/json
```

#### 请求体

```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_type": "basic_stats",
  "parameters": {
    "columns": ["quantity", "price", "total"],
    "confidence_level": 0.95,
    "include_outliers": true
  },
  "description": "Basic statistical analysis of sales data",
  "priority": "normal"
}
```

#### 请求参数说明

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file_id | string | 是 | 要分析的文件ID |
| analysis_type | string | 是 | 分析类型 |
| parameters | object | 否 | 分析参数 |
| description | string | 否 | 分析描述 |
| priority | string | 否 | 任务优先级 (low/normal/high) |

#### 支持的分析类型

| 分析类型 | 描述 | 适用数据类型 |
|----------|------|-------------|
| basic_stats | 基础统计分析 | 数值型 |
| correlation | 相关性分析 | 数值型 |
| distribution | 分布分析 | 数值型 |
| outlier_detection | 异常值检测 | 数值型 |
| time_series | 时间序列分析 | 时间序列 |
| categorical_analysis | 分类变量分析 | 分类型 |
| regression | 回归分析 | 数值型 |
| clustering | 聚类分析 | 数值型 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "analysis_type": "basic_stats",
    "status": "queued",
    "created_at": "2024-01-15T11:00:00Z",
    "estimated_completion": "2024-01-15T11:05:00Z",
    "priority": "normal"
  }
}
```

### 批量创建分析任务

```http
POST /analysis/batch
Content-Type: application/json
```

#### 请求体

```json
{
  "analyses": [
    {
      "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "analysis_type": "basic_stats",
      "parameters": {
        "columns": ["quantity", "price"]
      }
    },
    {
      "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "analysis_type": "correlation",
      "parameters": {
        "method": "pearson"
      }
    }
  ],
  "batch_description": "Comprehensive analysis of sales data"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "batch_id": "b47ac10b-58cc-4372-a567-0e02b2c3d483",
    "analyses": [
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d484",
        "analysis_type": "basic_stats",
        "status": "queued"
      },
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d485",
        "analysis_type": "correlation",
        "status": "queued"
      }
    ],
    "total_analyses": 2,
    "estimated_completion": "2024-01-15T11:10:00Z"
  }
}
```

## 分析状态查询

### 获取分析状态

```http
GET /analysis/{analysis_id}/status
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T11:00:00Z",
    "started_at": "2024-01-15T11:01:00Z",
    "completed_at": "2024-01-15T11:04:30Z",
    "processing_time": 210,
    "error_message": null
  }
}
```

#### 状态说明

| 状态 | 描述 |
|------|------|
| queued | 已排队等待处理 |
| running | 正在处理中 |
| completed | 处理完成 |
| failed | 处理失败 |
| cancelled | 已取消 |

### 获取批量分析状态

```http
GET /analysis/batch/{batch_id}/status
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "batch_id": "b47ac10b-58cc-4372-a567-0e02b2c3d483",
    "status": "completed",
    "total_analyses": 2,
    "completed_analyses": 2,
    "failed_analyses": 0,
    "progress": 100,
    "created_at": "2024-01-15T11:00:00Z",
    "completed_at": "2024-01-15T11:08:45Z",
    "analyses": [
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d484",
        "analysis_type": "basic_stats",
        "status": "completed",
        "progress": 100
      },
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d485",
        "analysis_type": "correlation",
        "status": "completed",
        "progress": 100
      }
    ]
  }
}
```

## 分析结果获取

### 获取分析结果

```http
GET /analysis/{analysis_id}/results
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| format | string | 否 | json | 结果格式 (json/csv/excel) |
| include_raw_data | boolean | 否 | false | 是否包含原始数据 |

#### 基础统计分析结果示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "analysis_type": "basic_stats",
    "status": "completed",
    "results": {
      "summary": {
        "total_rows": 1500,
        "analyzed_columns": 3,
        "missing_values": 15,
        "processing_time": 2.5
      },
      "statistics": {
        "quantity": {
          "count": 1485,
          "mean": 15.67,
          "median": 12.0,
          "mode": 10.0,
          "std": 8.45,
          "variance": 71.4,
          "min": 1.0,
          "max": 100.0,
          "q1": 8.0,
          "q3": 20.0,
          "iqr": 12.0,
          "skewness": 1.23,
          "kurtosis": 2.45,
          "confidence_interval_95": [14.89, 16.45],
          "outliers": {
            "count": 23,
            "indices": [45, 123, 456, 789],
            "values": [85, 92, 88, 95]
          }
        },
        "price": {
          "count": 1490,
          "mean": 125.75,
          "median": 99.99,
          "mode": 49.99,
          "std": 75.23,
          "variance": 5659.55,
          "min": 9.99,
          "max": 999.99,
          "q1": 49.99,
          "q3": 199.99,
          "iqr": 150.0,
          "skewness": 2.1,
          "kurtosis": 6.8,
          "confidence_interval_95": [121.92, 129.58],
          "outliers": {
            "count": 12,
            "indices": [234, 567, 890],
            "values": [899.99, 999.99, 849.99]
          }
        },
        "total": {
          "count": 1485,
          "mean": 1970.25,
          "median": 1199.88,
          "mode": 499.90,
          "std": 1456.78,
          "variance": 2122207.84,
          "min": 9.99,
          "max": 99999.0,
          "q1": 599.95,
          "q3": 2999.80,
          "iqr": 2399.85,
          "skewness": 3.45,
          "kurtosis": 15.67,
          "confidence_interval_95": [1896.12, 2044.38],
          "outliers": {
            "count": 8,
            "indices": [123, 456],
            "values": [89999.0, 99999.0]
          }
        }
      }
    },
    "metadata": {
      "file_info": {
        "filename": "sales_data.csv",
        "rows": 1500,
        "columns": 8
      },
      "analysis_parameters": {
        "columns": ["quantity", "price", "total"],
        "confidence_level": 0.95,
        "include_outliers": true
      },
      "created_at": "2024-01-15T11:00:00Z",
      "completed_at": "2024-01-15T11:04:30Z"
    }
  }
}
```

### 相关性分析结果示例

```http
GET /analysis/{analysis_id}/results
```

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d485",
    "analysis_type": "correlation",
    "results": {
      "correlation_matrix": {
        "pearson": {
          "quantity": {
            "quantity": 1.0,
            "price": 0.15,
            "total": 0.89
          },
          "price": {
            "quantity": 0.15,
            "price": 1.0,
            "total": 0.76
          },
          "total": {
            "quantity": 0.89,
            "price": 0.76,
            "total": 1.0
          }
        },
        "spearman": {
          "quantity": {
            "quantity": 1.0,
            "price": 0.12,
            "total": 0.85
          },
          "price": {
            "quantity": 0.12,
            "price": 1.0,
            "total": 0.73
          },
          "total": {
            "quantity": 0.85,
            "price": 0.73,
            "total": 1.0
          }
        }
      },
      "significance_tests": {
        "quantity_price": {
          "correlation": 0.15,
          "p_value": 0.001,
          "significant": true,
          "confidence_interval": [0.10, 0.20]
        },
        "quantity_total": {
          "correlation": 0.89,
          "p_value": 0.0,
          "significant": true,
          "confidence_interval": [0.87, 0.91]
        },
        "price_total": {
          "correlation": 0.76,
          "p_value": 0.0,
          "significant": true,
          "confidence_interval": [0.73, 0.79]
        }
      },
      "strong_correlations": [
        {
          "variables": ["quantity", "total"],
          "correlation": 0.89,
          "strength": "strong",
          "direction": "positive"
        },
        {
          "variables": ["price", "total"],
          "correlation": 0.76,
          "strength": "strong",
          "direction": "positive"
        }
      ]
    }
  }
}
```

### 分布分析结果示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d486",
    "analysis_type": "distribution",
    "results": {
      "normality_tests": {
        "quantity": {
          "shapiro_wilk": {
            "statistic": 0.892,
            "p_value": 0.001,
            "is_normal": false
          },
          "kolmogorov_smirnov": {
            "statistic": 0.156,
            "p_value": 0.002,
            "is_normal": false
          },
          "anderson_darling": {
            "statistic": 12.45,
            "critical_values": [0.576, 0.656, 0.787, 0.918, 1.092],
            "significance_levels": [15.0, 10.0, 5.0, 2.5, 1.0],
            "is_normal": false
          }
        }
      },
      "distribution_fitting": {
        "quantity": {
          "best_fit": "gamma",
          "distributions": {
            "normal": {
              "parameters": {"loc": 15.67, "scale": 8.45},
              "aic": 8945.23,
              "bic": 8956.78,
              "log_likelihood": -4470.61
            },
            "gamma": {
              "parameters": {"a": 3.45, "loc": 0, "scale": 4.54},
              "aic": 8723.45,
              "bic": 8740.12,
              "log_likelihood": -4358.72
            },
            "exponential": {
              "parameters": {"loc": 0, "scale": 15.67},
              "aic": 9234.56,
              "bic": 9245.23,
              "log_likelihood": -4615.28
            }
          }
        }
      },
      "histogram_data": {
        "quantity": {
          "bins": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
          "counts": [45, 123, 234, 345, 289, 178, 134, 89, 34, 12],
          "bin_edges": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100]
        }
      }
    }
  }
}
```

## 特定分析类型

### 异常值检测

```http
POST /analysis/outlier-detection
Content-Type: application/json
```

#### 请求体

```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parameters": {
    "columns": ["quantity", "price", "total"],
    "method": "isolation_forest",
    "contamination": 0.1,
    "threshold": 2.0
  }
}
```

#### 支持的异常值检测方法

| 方法 | 描述 | 参数 |
|------|------|------|
| iqr | 四分位距方法 | multiplier (默认1.5) |
| zscore | Z分数方法 | threshold (默认3.0) |
| isolation_forest | 孤立森林 | contamination (默认0.1) |
| local_outlier_factor | 局部异常因子 | n_neighbors (默认20) |
| one_class_svm | 单类SVM | nu (默认0.1) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d487",
    "results": {
      "outliers": {
        "quantity": {
          "method": "isolation_forest",
          "outlier_count": 23,
          "outlier_percentage": 1.53,
          "outlier_indices": [45, 123, 456, 789, 1001],
          "outlier_values": [85, 92, 88, 95, 98],
          "outlier_scores": [-0.15, -0.18, -0.16, -0.19, -0.21]
        },
        "price": {
          "method": "isolation_forest",
          "outlier_count": 12,
          "outlier_percentage": 0.80,
          "outlier_indices": [234, 567, 890],
          "outlier_values": [899.99, 999.99, 849.99],
          "outlier_scores": [-0.22, -0.25, -0.20]
        }
      },
      "summary": {
        "total_outliers": 35,
        "outlier_percentage": 2.33,
        "most_affected_column": "quantity",
        "detection_method": "isolation_forest"
      }
    }
  }
}
```

### 时间序列分析

```http
POST /analysis/time-series
Content-Type: application/json
```

#### 请求体

```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parameters": {
    "date_column": "date",
    "value_columns": ["total"],
    "frequency": "D",
    "seasonal_periods": 7,
    "forecast_periods": 30
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d488",
    "results": {
      "trend_analysis": {
        "trend_direction": "increasing",
        "trend_strength": 0.75,
        "trend_slope": 12.5,
        "trend_r_squared": 0.68
      },
      "seasonality": {
        "has_seasonality": true,
        "seasonal_strength": 0.45,
        "seasonal_period": 7,
        "seasonal_components": {
          "Monday": -15.2,
          "Tuesday": -8.7,
          "Wednesday": 5.3,
          "Thursday": 12.8,
          "Friday": 18.9,
          "Saturday": 22.1,
          "Sunday": -35.2
        }
      },
      "stationarity": {
        "adf_test": {
          "statistic": -3.45,
          "p_value": 0.01,
          "critical_values": {
            "1%": -3.43,
            "5%": -2.86,
            "10%": -2.57
          },
          "is_stationary": true
        }
      },
      "forecast": {
        "method": "arima",
        "model_params": {"p": 1, "d": 1, "q": 1},
        "predictions": [
          {
            "date": "2024-02-01",
            "predicted_value": 2150.5,
            "confidence_interval_lower": 1980.2,
            "confidence_interval_upper": 2320.8
          },
          {
            "date": "2024-02-02",
            "predicted_value": 2165.3,
            "confidence_interval_lower": 1975.1,
            "confidence_interval_upper": 2355.5
          }
        ],
        "model_metrics": {
          "aic": 1234.56,
          "bic": 1245.78,
          "mse": 15678.9,
          "mae": 98.7
        }
      }
    }
  }
}
```

### 聚类分析

```http
POST /analysis/clustering
Content-Type: application/json
```

#### 请求体

```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parameters": {
    "columns": ["quantity", "price", "total"],
    "algorithm": "kmeans",
    "n_clusters": 3,
    "normalize": true,
    "random_state": 42
  }
}
```

#### 支持的聚类算法

| 算法 | 描述 | 主要参数 |
|------|------|----------|
| kmeans | K均值聚类 | n_clusters, random_state |
| dbscan | 基于密度的聚类 | eps, min_samples |
| hierarchical | 层次聚类 | n_clusters, linkage |
| gaussian_mixture | 高斯混合模型 | n_components, covariance_type |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d489",
    "results": {
      "cluster_assignments": [0, 1, 0, 2, 1, 0, 2, 1],
      "cluster_centers": {
        "cluster_0": {
          "quantity": 8.5,
          "price": 75.2,
          "total": 638.7
        },
        "cluster_1": {
          "quantity": 25.3,
          "price": 150.8,
          "total": 3816.2
        },
        "cluster_2": {
          "quantity": 45.7,
          "price": 89.9,
          "total": 4108.4
        }
      },
      "cluster_statistics": {
        "cluster_0": {
          "size": 567,
          "percentage": 37.8,
          "intra_cluster_distance": 234.5
        },
        "cluster_1": {
          "size": 489,
          "percentage": 32.6,
          "intra_cluster_distance": 345.7
        },
        "cluster_2": {
          "size": 444,
          "percentage": 29.6,
          "intra_cluster_distance": 298.3
        }
      },
      "model_metrics": {
        "silhouette_score": 0.68,
        "calinski_harabasz_score": 1234.56,
        "davies_bouldin_score": 0.89,
        "inertia": 15678.9
      }
    }
  }
}
```

## 分析历史和管理

### 获取分析历史

```http
GET /analysis/history
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| file_id | string | 否 | - | 按文件ID过滤 |
| analysis_type | string | 否 | - | 按分析类型过滤 |
| status | string | 否 | - | 按状态过滤 |
| date_from | string | 否 | - | 开始日期 |
| date_to | string | 否 | - | 结束日期 |
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 20 | 每页数量 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analyses": [
      {
        "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
        "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "analysis_type": "basic_stats",
        "status": "completed",
        "created_at": "2024-01-15T11:00:00Z",
        "completed_at": "2024-01-15T11:04:30Z",
        "processing_time": 270,
        "description": "Basic statistical analysis of sales data"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 45,
      "items_per_page": 20
    }
  }
}
```

### 取消分析任务

```http
DELETE /analysis/{analysis_id}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T11:02:00Z",
    "message": "Analysis task cancelled successfully"
  }
}
```

### 重新运行分析

```http
POST /analysis/{analysis_id}/rerun
Content-Type: application/json
```

#### 请求体

```json
{
  "parameters": {
    "columns": ["quantity", "price", "total", "region"],
    "confidence_level": 0.99
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "new_analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d490",
    "original_analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "status": "queued",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

## 分析模板

### 创建分析模板

```http
POST /analysis/templates
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "Sales Data Analysis Template",
  "description": "Standard analysis template for sales data",
  "analyses": [
    {
      "analysis_type": "basic_stats",
      "parameters": {
        "columns": ["quantity", "price", "total"],
        "confidence_level": 0.95
      }
    },
    {
      "analysis_type": "correlation",
      "parameters": {
        "method": "pearson"
      }
    },
    {
      "analysis_type": "outlier_detection",
      "parameters": {
        "method": "isolation_forest",
        "contamination": 0.1
      }
    }
  ],
  "tags": ["sales", "standard", "comprehensive"]
}
```

### 使用分析模板

```http
POST /analysis/templates/{template_id}/apply
Content-Type: application/json
```

#### 请求体

```json
{
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parameter_overrides": {
    "basic_stats": {
      "confidence_level": 0.99
    }
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ANALYSIS_FAILED",
    "message": "Analysis failed due to insufficient data",
    "details": {
      "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
      "error_type": "data_error",
      "column": "quantity",
      "reason": "All values are null"
    },
    "timestamp": "2024-01-15T11:03:00Z"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| ANALYSIS_NOT_FOUND | 404 | 分析任务不存在 |
| INVALID_ANALYSIS_TYPE | 400 | 不支持的分析类型 |
| INSUFFICIENT_DATA | 400 | 数据不足以进行分析 |
| ANALYSIS_FAILED | 500 | 分析执行失败 |
| QUEUE_FULL | 503 | 分析队列已满 |
| TIMEOUT | 408 | 分析超时 |
| INVALID_PARAMETERS | 400 | 分析参数无效 |

## SDK 示例

### Python SDK

```python
from data_report_client import DataReportClient

client = DataReportClient(base_url="http://localhost:8000/api/v1")

# 创建基础统计分析
analysis = client.analysis.create(
    file_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    analysis_type="basic_stats",
    parameters={
        "columns": ["quantity", "price", "total"],
        "confidence_level": 0.95
    }
)

# 等待分析完成
result = client.analysis.wait_for_completion(analysis.data.analysis_id)

# 获取结果
if result.data.status == "completed":
    results = client.analysis.get_results(analysis.data.analysis_id)
    print(f"Mean quantity: {results.data.results.statistics.quantity.mean}")
else:
    print(f"Analysis failed: {result.data.error_message}")
```

### JavaScript SDK

```javascript
import { DataReportClient } from '@data-report/client';

const client = new DataReportClient({
  baseURL: 'http://localhost:8000/api/v1'
});

// 创建批量分析
const batchAnalysis = await client.analysis.createBatch({
  analyses: [
    {
      file_id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
      analysis_type: 'basic_stats',
      parameters: { columns: ['quantity', 'price'] }
    },
    {
      file_id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
      analysis_type: 'correlation'
    }
  ]
});

// 监控批量分析状态
const status = await client.analysis.getBatchStatus(batchAnalysis.data.batch_id);
console.log(`Batch progress: ${status.data.progress}%`);

// 获取所有结果
if (status.data.status === 'completed') {
  for (const analysis of status.data.analyses) {
    const results = await client.analysis.getResults(analysis.analysis_id);
    console.log(`${analysis.analysis_type} completed:`, results.data.results);
  }
}
```

通过这些API端点，您可以完整地管理数据分析报告系统中的各种分析任务，从基础统计到高级机器学习分析。