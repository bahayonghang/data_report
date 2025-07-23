# 报告生成 API

本文档详细描述数据分析报告系统的报告生成相关API端点，包括报告创建、模板管理、导出功能等。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (可选)
- **内容类型**: `application/json`

## 报告创建

### 创建报告

```http
POST /reports/create
Content-Type: application/json
```

#### 请求体

```json
{
  "title": "Sales Data Analysis Report",
  "description": "Comprehensive analysis of Q4 2023 sales data",
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_ids": [
    "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "a47ac10b-58cc-4372-a567-0e02b2c3d485"
  ],
  "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d490",
  "sections": [
    {
      "type": "executive_summary",
      "title": "Executive Summary",
      "include_charts": true
    },
    {
      "type": "data_overview",
      "title": "Data Overview",
      "parameters": {
        "include_data_quality": true,
        "show_sample_data": true
      }
    },
    {
      "type": "statistical_analysis",
      "title": "Statistical Analysis",
      "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482",
      "parameters": {
        "include_distributions": true,
        "show_outliers": true
      }
    },
    {
      "type": "correlation_analysis",
      "title": "Correlation Analysis",
      "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d485",
      "parameters": {
        "correlation_threshold": 0.5,
        "include_heatmap": true
      }
    },
    {
      "type": "conclusions",
      "title": "Conclusions and Recommendations",
      "content": "Based on the analysis, we recommend..."
    }
  ],
  "format_options": {
    "include_toc": true,
    "include_appendix": true,
    "chart_style": "professional",
    "color_scheme": "blue"
  },
  "metadata": {
    "author": "Data Analysis Team",
    "department": "Sales Analytics",
    "tags": ["sales", "Q4", "2023"]
  }
}
```

#### 请求参数说明

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| title | string | 是 | 报告标题 |
| description | string | 否 | 报告描述 |
| file_id | string | 是 | 数据文件ID |
| analysis_ids | array | 是 | 分析结果ID列表 |
| template_id | string | 否 | 报告模板ID |
| sections | array | 是 | 报告章节配置 |
| format_options | object | 否 | 格式选项 |
| metadata | object | 否 | 报告元数据 |

#### 支持的报告章节类型

| 章节类型 | 描述 | 必需参数 |
|----------|------|----------|
| executive_summary | 执行摘要 | - |
| data_overview | 数据概览 | - |
| statistical_analysis | 统计分析 | analysis_id |
| correlation_analysis | 相关性分析 | analysis_id |
| distribution_analysis | 分布分析 | analysis_id |
| outlier_analysis | 异常值分析 | analysis_id |
| time_series_analysis | 时间序列分析 | analysis_id |
| clustering_analysis | 聚类分析 | analysis_id |
| custom_analysis | 自定义分析 | analysis_id |
| conclusions | 结论和建议 | content |
| appendix | 附录 | - |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
    "title": "Sales Data Analysis Report",
    "status": "generating",
    "created_at": "2024-01-15T14:00:00Z",
    "estimated_completion": "2024-01-15T14:05:00Z",
    "progress": 0,
    "sections_count": 5,
    "file_info": {
      "filename": "sales_data.csv",
      "size": 2048576
    }
  }
}
```

### 从模板创建报告

```http
POST /reports/create-from-template
Content-Type: application/json
```

#### 请求体

```json
{
  "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d490",
  "title": "Monthly Sales Report - January 2024",
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "analysis_ids": [
    "a47ac10b-58cc-4372-a567-0e02b2c3d482",
    "a47ac10b-58cc-4372-a567-0e02b2c3d485"
  ],
  "parameter_overrides": {
    "correlation_analysis": {
      "correlation_threshold": 0.3
    },
    "format_options": {
      "color_scheme": "green"
    }
  },
  "metadata": {
    "author": "John Doe",
    "period": "2024-01"
  }
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d492",
    "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d490",
    "title": "Monthly Sales Report - January 2024",
    "status": "generating",
    "created_at": "2024-01-15T14:10:00Z",
    "estimated_completion": "2024-01-15T14:13:00Z"
  }
}
```

## 报告状态和管理

### 获取报告状态

```http
GET /reports/{report_id}/status
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T14:00:00Z",
    "started_at": "2024-01-15T14:00:30Z",
    "completed_at": "2024-01-15T14:04:15Z",
    "generation_time": 225,
    "current_section": null,
    "sections_completed": 5,
    "total_sections": 5,
    "error_message": null,
    "file_size": 1024768,
    "page_count": 12
  }
}
```

#### 状态说明

| 状态 | 描述 |
|------|------|
| queued | 已排队等待生成 |
| generating | 正在生成中 |
| completed | 生成完成 |
| failed | 生成失败 |
| cancelled | 已取消 |

### 获取报告详情

```http
GET /reports/{report_id}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
    "title": "Sales Data Analysis Report",
    "description": "Comprehensive analysis of Q4 2023 sales data",
    "status": "completed",
    "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "analysis_ids": [
      "a47ac10b-58cc-4372-a567-0e02b2c3d482",
      "a47ac10b-58cc-4372-a567-0e02b2c3d485"
    ],
    "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d490",
    "sections": [
      {
        "type": "executive_summary",
        "title": "Executive Summary",
        "status": "completed",
        "page_start": 1,
        "page_end": 2
      },
      {
        "type": "data_overview",
        "title": "Data Overview",
        "status": "completed",
        "page_start": 3,
        "page_end": 4
      },
      {
        "type": "statistical_analysis",
        "title": "Statistical Analysis",
        "status": "completed",
        "page_start": 5,
        "page_end": 8
      },
      {
        "type": "correlation_analysis",
        "title": "Correlation Analysis",
        "status": "completed",
        "page_start": 9,
        "page_end": 10
      },
      {
        "type": "conclusions",
        "title": "Conclusions and Recommendations",
        "status": "completed",
        "page_start": 11,
        "page_end": 12
      }
    ],
    "format_options": {
      "include_toc": true,
      "include_appendix": true,
      "chart_style": "professional",
      "color_scheme": "blue"
    },
    "metadata": {
      "author": "Data Analysis Team",
      "department": "Sales Analytics",
      "tags": ["sales", "Q4", "2023"],
      "version": "1.0",
      "language": "en"
    },
    "statistics": {
      "page_count": 12,
      "word_count": 3456,
      "chart_count": 8,
      "table_count": 5,
      "file_size": 1024768
    },
    "created_at": "2024-01-15T14:00:00Z",
    "completed_at": "2024-01-15T14:04:15Z",
    "generation_time": 225
  }
}
```

### 获取报告列表

```http
GET /reports
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| status | string | 否 | - | 按状态过滤 |
| file_id | string | 否 | - | 按文件ID过滤 |
| template_id | string | 否 | - | 按模板ID过滤 |
| author | string | 否 | - | 按作者过滤 |
| date_from | string | 否 | - | 开始日期 |
| date_to | string | 否 | - | 结束日期 |
| tags | string | 否 | - | 按标签过滤 (逗号分隔) |
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 20 | 每页数量 |
| sort_by | string | 否 | created_at | 排序字段 |
| sort_order | string | 否 | desc | 排序顺序 (asc/desc) |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
        "title": "Sales Data Analysis Report",
        "status": "completed",
        "created_at": "2024-01-15T14:00:00Z",
        "completed_at": "2024-01-15T14:04:15Z",
        "author": "Data Analysis Team",
        "page_count": 12,
        "file_size": 1024768,
        "tags": ["sales", "Q4", "2023"]
      },
      {
        "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d492",
        "title": "Monthly Sales Report - January 2024",
        "status": "generating",
        "created_at": "2024-01-15T14:10:00Z",
        "progress": 60,
        "author": "John Doe",
        "tags": ["sales", "monthly"]
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_items": 45,
      "items_per_page": 20
    },
    "filters": {
      "status": null,
      "file_id": null,
      "template_id": null,
      "author": null,
      "date_from": null,
      "date_to": null,
      "tags": null
    }
  }
}
```

## 报告导出

### 下载报告

```http
GET /reports/{report_id}/download
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| format | string | 否 | pdf | 导出格式 (pdf/docx/html/json) |
| sections | string | 否 | all | 包含的章节 (all/specific) |
| include_raw_data | boolean | 否 | false | 是否包含原始数据 |
| watermark | boolean | 否 | false | 是否添加水印 |

#### 支持的导出格式

| 格式 | 描述 | 文件扩展名 | 内容类型 |
|------|------|------------|----------|
| pdf | PDF文档 | .pdf | application/pdf |
| docx | Word文档 | .docx | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| html | HTML网页 | .html | text/html |
| json | JSON数据 | .json | application/json |
| pptx | PowerPoint演示文稿 | .pptx | application/vnd.openxmlformats-officedocument.presentationml.presentation |

#### 响应

成功时返回文件流，包含以下响应头：

```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="Sales_Data_Analysis_Report.pdf"
Content-Length: 1024768
```

### 获取报告预览

```http
GET /reports/{report_id}/preview
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | integer | 否 | 1 | 预览页码 |
| format | string | 否 | html | 预览格式 (html/image) |
| width | integer | 否 | 800 | 预览宽度 (仅图片格式) |
| height | integer | 否 | 600 | 预览高度 (仅图片格式) |

#### HTML预览响应示例

```json
{
  "success": true,
  "data": {
    "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
    "page": 1,
    "total_pages": 12,
    "format": "html",
    "content": "<div class='report-page'>...</div>",
    "css": ".report-page { font-family: Arial, sans-serif; }",
    "preview_url": "http://localhost:8000/api/v1/reports/r47ac10b-58cc-4372-a567-0e02b2c3d491/preview?page=1"
  }
}
```

### 批量导出报告

```http
POST /reports/batch-export
Content-Type: application/json
```

#### 请求体

```json
{
  "report_ids": [
    "r47ac10b-58cc-4372-a567-0e02b2c3d491",
    "r47ac10b-58cc-4372-a567-0e02b2c3d492"
  ],
  "format": "pdf",
  "archive_format": "zip",
  "include_metadata": true,
  "filename_pattern": "{title}_{date}"
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "export_id": "e47ac10b-58cc-4372-a567-0e02b2c3d493",
    "status": "processing",
    "total_reports": 2,
    "processed_reports": 0,
    "estimated_completion": "2024-01-15T14:20:00Z",
    "download_url": null
  }
}
```

### 获取批量导出状态

```http
GET /reports/batch-export/{export_id}/status
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "export_id": "e47ac10b-58cc-4372-a567-0e02b2c3d493",
    "status": "completed",
    "total_reports": 2,
    "processed_reports": 2,
    "failed_reports": 0,
    "created_at": "2024-01-15T14:15:00Z",
    "completed_at": "2024-01-15T14:18:30Z",
    "processing_time": 210,
    "archive_size": 2048576,
    "download_url": "http://localhost:8000/api/v1/reports/batch-export/e47ac10b-58cc-4372-a567-0e02b2c3d493/download",
    "expires_at": "2024-01-16T14:18:30Z"
  }
}
```

## 报告模板管理

### 创建报告模板

```http
POST /reports/templates
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "Standard Sales Analysis Template",
  "description": "Standard template for sales data analysis reports",
  "category": "sales",
  "sections": [
    {
      "type": "executive_summary",
      "title": "Executive Summary",
      "required": true,
      "parameters": {
        "include_charts": true,
        "max_length": 500
      }
    },
    {
      "type": "data_overview",
      "title": "Data Overview",
      "required": true,
      "parameters": {
        "include_data_quality": true,
        "show_sample_data": true,
        "sample_size": 10
      }
    },
    {
      "type": "statistical_analysis",
      "title": "Statistical Analysis",
      "required": true,
      "parameters": {
        "include_distributions": true,
        "show_outliers": true,
        "confidence_level": 0.95
      }
    },
    {
      "type": "correlation_analysis",
      "title": "Correlation Analysis",
      "required": false,
      "parameters": {
        "correlation_threshold": 0.5,
        "include_heatmap": true,
        "method": "pearson"
      }
    },
    {
      "type": "conclusions",
      "title": "Conclusions and Recommendations",
      "required": true,
      "parameters": {
        "include_recommendations": true,
        "max_length": 1000
      }
    }
  ],
  "default_format_options": {
    "include_toc": true,
    "include_appendix": false,
    "chart_style": "professional",
    "color_scheme": "blue",
    "font_family": "Arial",
    "font_size": 12
  },
  "metadata": {
    "author": "Data Analysis Team",
    "version": "1.0",
    "tags": ["sales", "standard", "analysis"]
  },
  "is_public": true
}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d494",
    "name": "Standard Sales Analysis Template",
    "description": "Standard template for sales data analysis reports",
    "category": "sales",
    "version": "1.0",
    "is_public": true,
    "sections_count": 5,
    "created_at": "2024-01-15T15:00:00Z",
    "created_by": "Data Analysis Team"
  }
}
```

### 获取模板列表

```http
GET /reports/templates
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| category | string | 否 | - | 按分类过滤 |
| is_public | boolean | 否 | - | 是否公开模板 |
| tags | string | 否 | - | 按标签过滤 (逗号分隔) |
| search | string | 否 | - | 搜索关键词 |
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 20 | 每页数量 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d494",
        "name": "Standard Sales Analysis Template",
        "description": "Standard template for sales data analysis reports",
        "category": "sales",
        "version": "1.0",
        "is_public": true,
        "sections_count": 5,
        "usage_count": 156,
        "rating": 4.8,
        "created_at": "2024-01-15T15:00:00Z",
        "created_by": "Data Analysis Team",
        "tags": ["sales", "standard", "analysis"]
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 2,
      "total_items": 25,
      "items_per_page": 20
    },
    "categories": ["sales", "finance", "marketing", "operations", "custom"]
  }
}
```

### 获取模板详情

```http
GET /reports/templates/{template_id}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d494",
    "name": "Standard Sales Analysis Template",
    "description": "Standard template for sales data analysis reports",
    "category": "sales",
    "version": "1.0",
    "is_public": true,
    "sections": [
      {
        "type": "executive_summary",
        "title": "Executive Summary",
        "required": true,
        "order": 1,
        "parameters": {
          "include_charts": true,
          "max_length": 500
        }
      }
    ],
    "default_format_options": {
      "include_toc": true,
      "include_appendix": false,
      "chart_style": "professional",
      "color_scheme": "blue",
      "font_family": "Arial",
      "font_size": 12
    },
    "metadata": {
      "author": "Data Analysis Team",
      "version": "1.0",
      "tags": ["sales", "standard", "analysis"]
    },
    "statistics": {
      "usage_count": 156,
      "rating": 4.8,
      "reviews_count": 23,
      "last_used": "2024-01-15T13:45:00Z"
    },
    "created_at": "2024-01-15T15:00:00Z",
    "updated_at": "2024-01-15T15:00:00Z",
    "created_by": "Data Analysis Team"
  }
}
```

### 更新模板

```http
PUT /reports/templates/{template_id}
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "Enhanced Sales Analysis Template",
  "description": "Enhanced template with additional analysis sections",
  "sections": [
    {
      "type": "executive_summary",
      "title": "Executive Summary",
      "required": true,
      "parameters": {
        "include_charts": true,
        "max_length": 600
      }
    }
  ],
  "version": "1.1"
}
```

### 删除模板

```http
DELETE /reports/templates/{template_id}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "template_id": "t47ac10b-58cc-4372-a567-0e02b2c3d494",
    "message": "Template deleted successfully",
    "deleted_at": "2024-01-15T16:00:00Z"
  }
}
```

## 报告分享和协作

### 创建分享链接

```http
POST /reports/{report_id}/share
Content-Type: application/json
```

#### 请求体

```json
{
  "access_level": "view",
  "expires_at": "2024-02-15T00:00:00Z",
  "password_protected": true,
  "password": "secure123",
  "allow_download": true,
  "allowed_formats": ["pdf", "html"],
  "watermark": true,
  "recipients": [
    {
      "email": "john.doe@company.com",
      "access_level": "view"
    },
    {
      "email": "jane.smith@company.com",
      "access_level": "comment"
    }
  ]
}
```

#### 访问级别说明

| 访问级别 | 描述 | 权限 |
|----------|------|------|
| view | 仅查看 | 查看报告内容 |
| comment | 评论 | 查看 + 添加评论 |
| edit | 编辑 | 查看 + 评论 + 编辑报告 |
| admin | 管理员 | 所有权限 + 管理分享设置 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "share_id": "s47ac10b-58cc-4372-a567-0e02b2c3d495",
    "share_url": "http://localhost:8000/shared/reports/s47ac10b-58cc-4372-a567-0e02b2c3d495",
    "access_level": "view",
    "expires_at": "2024-02-15T00:00:00Z",
    "password_protected": true,
    "allow_download": true,
    "watermark": true,
    "created_at": "2024-01-15T16:30:00Z",
    "recipients_notified": 2
  }
}
```

### 获取分享信息

```http
GET /reports/{report_id}/shares
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "shares": [
      {
        "share_id": "s47ac10b-58cc-4372-a567-0e02b2c3d495",
        "share_url": "http://localhost:8000/shared/reports/s47ac10b-58cc-4372-a567-0e02b2c3d495",
        "access_level": "view",
        "expires_at": "2024-02-15T00:00:00Z",
        "password_protected": true,
        "view_count": 15,
        "last_accessed": "2024-01-15T18:45:00Z",
        "created_at": "2024-01-15T16:30:00Z",
        "status": "active"
      }
    ],
    "total_shares": 1,
    "total_views": 15
  }
}
```

### 撤销分享

```http
DELETE /reports/{report_id}/shares/{share_id}
```

#### 响应示例

```json
{
  "success": true,
  "data": {
    "share_id": "s47ac10b-58cc-4372-a567-0e02b2c3d495",
    "message": "Share link revoked successfully",
    "revoked_at": "2024-01-15T17:00:00Z"
  }
}
```

## 报告评论和反馈

### 添加评论

```http
POST /reports/{report_id}/comments
Content-Type: application/json
```

#### 请求体

```json
{
  "content": "The correlation analysis section provides excellent insights.",
  "section_type": "correlation_analysis",
  "page_number": 9,
  "position": {
    "x": 150,
    "y": 300
  },
  "comment_type": "feedback",
  "priority": "normal"
}
```

#### 评论类型说明

| 评论类型 | 描述 |
|----------|------|
| feedback | 反馈意见 |
| question | 问题询问 |
| suggestion | 改进建议 |
| error | 错误报告 |
| approval | 审批意见 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "comment_id": "c47ac10b-58cc-4372-a567-0e02b2c3d496",
    "content": "The correlation analysis section provides excellent insights.",
    "section_type": "correlation_analysis",
    "page_number": 9,
    "comment_type": "feedback",
    "priority": "normal",
    "author": "John Doe",
    "created_at": "2024-01-15T17:30:00Z",
    "status": "open"
  }
}
```

### 获取评论列表

```http
GET /reports/{report_id}/comments
```

#### 查询参数

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| section_type | string | 否 | - | 按章节类型过滤 |
| comment_type | string | 否 | - | 按评论类型过滤 |
| status | string | 否 | - | 按状态过滤 (open/resolved/closed) |
| author | string | 否 | - | 按作者过滤 |
| page | integer | 否 | 1 | 页码 |
| limit | integer | 否 | 20 | 每页数量 |

#### 响应示例

```json
{
  "success": true,
  "data": {
    "comments": [
      {
        "comment_id": "c47ac10b-58cc-4372-a567-0e02b2c3d496",
        "content": "The correlation analysis section provides excellent insights.",
        "section_type": "correlation_analysis",
        "page_number": 9,
        "comment_type": "feedback",
        "priority": "normal",
        "author": "John Doe",
        "created_at": "2024-01-15T17:30:00Z",
        "updated_at": "2024-01-15T17:30:00Z",
        "status": "open",
        "replies_count": 2
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 1,
      "total_items": 5,
      "items_per_page": 20
    },
    "summary": {
      "total_comments": 5,
      "open_comments": 3,
      "resolved_comments": 2,
      "by_type": {
        "feedback": 2,
        "question": 2,
        "suggestion": 1
      }
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
    "code": "REPORT_GENERATION_FAILED",
    "message": "Report generation failed due to missing analysis results",
    "details": {
      "report_id": "r47ac10b-58cc-4372-a567-0e02b2c3d491",
      "missing_analysis_ids": [
        "a47ac10b-58cc-4372-a567-0e02b2c3d485"
      ],
      "failed_sections": ["correlation_analysis"]
    },
    "timestamp": "2024-01-15T14:03:00Z"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|----------|------------|------|
| REPORT_NOT_FOUND | 404 | 报告不存在 |
| TEMPLATE_NOT_FOUND | 404 | 模板不存在 |
| INVALID_SECTION_TYPE | 400 | 无效的章节类型 |
| MISSING_ANALYSIS_RESULTS | 400 | 缺少分析结果 |
| REPORT_GENERATION_FAILED | 500 | 报告生成失败 |
| EXPORT_FAILED | 500 | 导出失败 |
| INVALID_FORMAT | 400 | 不支持的格式 |
| TEMPLATE_IN_USE | 409 | 模板正在使用中 |
| SHARE_EXPIRED | 410 | 分享链接已过期 |
| ACCESS_DENIED | 403 | 访问被拒绝 |

## SDK 示例

### Python SDK

```python
from data_report_client import DataReportClient

client = DataReportClient(base_url="http://localhost:8000/api/v1")

# 创建报告
report = client.reports.create(
    title="Sales Analysis Report",
    file_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    analysis_ids=[
        "a47ac10b-58cc-4372-a567-0e02b2c3d482",
        "a47ac10b-58cc-4372-a567-0e02b2c3d485"
    ],
    sections=[
        {
            "type": "executive_summary",
            "title": "Executive Summary"
        },
        {
            "type": "statistical_analysis",
            "title": "Statistical Analysis",
            "analysis_id": "a47ac10b-58cc-4372-a567-0e02b2c3d482"
        }
    ]
)

# 等待报告生成完成
result = client.reports.wait_for_completion(report.data.report_id)

# 下载报告
if result.data.status == "completed":
    pdf_content = client.reports.download(
        report.data.report_id,
        format="pdf"
    )
    
    with open("report.pdf", "wb") as f:
        f.write(pdf_content)
    
    print("Report downloaded successfully")
else:
    print(f"Report generation failed: {result.data.error_message}")
```

### JavaScript SDK

```javascript
import { DataReportClient } from '@data-report/client';

const client = new DataReportClient({
  baseURL: 'http://localhost:8000/api/v1'
});

// 从模板创建报告
const report = await client.reports.createFromTemplate({
  template_id: 't47ac10b-58cc-4372-a567-0e02b2c3d490',
  title: 'Monthly Sales Report - January 2024',
  file_id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
  analysis_ids: [
    'a47ac10b-58cc-4372-a567-0e02b2c3d482',
    'a47ac10b-58cc-4372-a567-0e02b2c3d485'
  ]
});

// 监控报告生成进度
const checkProgress = async () => {
  const status = await client.reports.getStatus(report.data.report_id);
  console.log(`Progress: ${status.data.progress}%`);
  
  if (status.data.status === 'completed') {
    // 创建分享链接
    const share = await client.reports.createShare(report.data.report_id, {
      access_level: 'view',
      expires_at: '2024-02-15T00:00:00Z',
      allow_download: true
    });
    
    console.log(`Report available at: ${share.data.share_url}`);
  } else if (status.data.status === 'generating') {
    setTimeout(checkProgress, 5000); // 5秒后再次检查
  }
};

checkProgress();
```

通过这些API端点，您可以完整地管理数据分析报告系统中的报告生成、模板管理、导出分享等功能，为用户提供专业的报告服务。