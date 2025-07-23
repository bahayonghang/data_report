# **Python 数据分析报告生成工具 \- 技术方案**

本文档旨在为开发一个**基于Web交互**的自动化数据分析报告工具提供全面的技术指导。该工具旨在简化时序数据的探索性分析流程，用户通过Web界面选择或上传文件，后端自动执行一系列分析，并最终在网页上展示一份交互式的报告。

## **1\. 功能清单 (Features)**

该工具将实现以下数据分析与交互功能：

#### **核心分析功能**

* **时序曲线图**: 绘制每个变量随时间变化的趋势图，直观展示数据波动。  
* **描述性统计**: 计算并展示每个变量的关键统计指标（均值、中位数、标准差、最大/最小值、四分位数等）。  
* **平稳性检验**: 对每个时间序列进行增广迪基-福勒检验 (ADF Test)，并提供p值以判断序列的平稳性。  
* **缺失值分析**: 统计并展示每个变量的缺失值数量与占比。  
* **数据分布分析**: 为每个变量绘制直方图 (Histogram)，以观察其数据分布形态。  
* **异常值检测**: 为每个变量绘制箱形图 (Box Plot)，以帮助识别潜在的异常值。  
* **相关性分析**: 计算所有数值型变量间的相关系数，并以热力图 (Heatmap) 的形式在报告起始部分进行全局展示。

#### **交互与输出功能**

* **Web界面文件交互**:  
  * **本地文件上传**: 允许用户通过浏览器上传本地电脑上的数据文件。  
  * **服务器文件选择**: 提供一个Web界面的文件浏览器，用于选择运行在服务器指定目录下的数据文件。  
* **动态Web报告**: 分析完成后，直接在当前网页上动态加载并展示所有分析结果与交互式图表，无需跳转或下载文件。  
* **后端服务模式**: 通过在终端启动Web服务来运行整个应用。

## **2\. 技术架构 (Architecture)**

工具的整体架构将采用经典的前后端分离模式。

graph TD  
    subgraph "用户端 (Web Browser)"  
        A\[用户访问Web页面\] \--\> B{前端界面\<br/\>(HTML, CSS, JavaScript)};  
        B \-- API请求 (上传/选择文件) \--\> C;  
        C \-- 返回JSON/HTML片段 \--\> B;  
        B \-- 动态渲染 \--\> D\[交互式Web报告\];  
    end

    subgraph "服务端 (Server)"  
        C\[Web框架: FastAPI\<br/\>(定义API接口)\];  
        C \-- 调度 \--\> E;  
        E\[核心引擎层\];  
        E \-- 分析结果 \--\> C;  
    end

    subgraph "核心引擎层"  
        subgraph E  
            F\[数据加载模块\<br/\>(polars)\];  
            G\[分析模块集\<br/\>(polars, numpy, statsmodels)\];  
            H\[可视化模块\<br/\>(plotly)\];  
        end  
    end  
      
    %% 流程连接  
    C \--\> F;  
    F \--\> G;  
    G \-- 数据 \--\> H;

## **3\. 技术选型 (Technology Stack)**

| 分类 | 技术库 | 角色与职责 |  
| Web框架 | FastAPI | 构建高性能的后端API接口，用于接收前端请求、处理数据和返回结果。 |  
| ASGI服务器 | uvicorn | 用于运行FastAPI应用的高性能Web服务器。 |  
| 数据处理 | polars | 高性能地读取CSV/Parquet文件，执行数据清洗、转换和核心计算。 |  
| 科学计算 | numpy | 作为statsmodels等库的依赖，提供基础数值数组结构。 |  
| 统计分析 | statsmodels | 提供严谨的统计检验功能，主要用于ADF平稳性检验。 |  
| 数据可视化 | plotly | 生成高质量的交互式HTML图表，其HTML片段可直接嵌入前端页面。 |  
| 报告模板 | jinja2 | (可选) 用于从后端渲染复杂的HTML页面结构。 |  
| 前端 | HTML/CSS/JS | 构建用户操作界面，通过Fetch API与后端通信，并使用JavaScript动态更新页面内容。需处理加载和错误状态，可考虑使用轻量级库（如Alpine.js）或模块化JS来提升开发效率和用户体验。 |

## **4\. 详细实现流程 (Implementation Flow)**

#### **步骤 1: 环境搭建与项目结构 (使用 uv)**

1. **安装 uv**: 如果您尚未安装uv，请先根据其官方文档进行安装 (通常使用 pip install uv 或 curl 命令)。  
2. **创建虚拟环境**: 使用 uv venv 命令在项目根目录下创建一个虚拟环境。  
3. **激活虚拟环境**: 根据您的操作系统激活环境 (例如，在Linux/macOS上使用 source .venv/bin/activate)。  
4. **安装依赖**: 使用 uv pip install fastapi uvicorn python-multipart polars numpy statsmodels plotly jinja2 安装所有依赖。uv 会高效地处理安装过程。  
5. **创建项目结构**: 按照下文“项目结构”一节的规划，创建所需的文件夹和空的.py文件。

#### **步骤 2: 后端API开发 (main.py)**

1. 创建一个FastAPI应用实例。  
2. 定义API接口 (Endpoints):  
   * GET /: 提供主页HTML。  
   * GET /api/list-files: (安全地)列出服务器上指定目录的文件，返回JSON。服务器上可供访问的文件目录不应在代码中硬编码，建议通过环境变量（如 DATA\_DIRECTORY）进行配置。应用在启动时读取此配置，所有文件相关的API都必须在此目录下操作。  
   * POST /api/analyze-server-file: 接收服务器上的文件路径作为请求，执行分析并返回结果。此端点应定义清晰的错误处理逻辑，使用标准的HTTP状态码（如 400 Bad Request 表示文件格式无效，500 Internal Server Error 表示分析过程出错）并返回具体的错误信息。需要处理的异常情况应包括：文件不存在、文件格式不支持、数据内容无法解析、分析超时等。  
   * POST /api/upload-and-analyze: 接收用户上传的文件，保存为临时文件，执行分析并返回结果。  
3. 在终端使用 uvicorn main:app \--reload 命令启动服务。

#### **步骤 3: 核心分析与可视化模块 (复用)**

1. data\_loader.py, analysis/\*.py, visualization/plots.py 中的核心逻辑保持不变，但需增加对时间列的特殊处理逻辑。  
2. 后端在执行分析时，首先需要识别作为时间索引的列。识别逻辑应为：检查第一列的列名是否为 DateTime 或 tagTime，或检查其数据类型是否为 datetime。  
3. 被识别为时间索引的列将**不进行**常规的统计分析（如均值、平稳性检验等）。分析模块仅需计算并返回该列的**时间范围**（即最早和最晚时间点）。  
4. 其他所有数值列将正常进入后续的统计分析和可视化流程。  
5. 这些分析函数将被后端的API接口函数调用，而不是被一个线性的主脚本调用。

#### **步骤 4: 前端界面开发 (templates/index.html & static/)**

1. 创建 index.html 作为主页面，包含文件上传表单和用于显示服务器文件的区域。  
2. 编写JavaScript (static/app.js):  
   * 页面加载时，调用 GET /api/list-files 获取服务器文件列表并渲染到页面上。  
   * 为“分析服务器文件”按钮添加事件监听，点击时将文件名发送到 POST /api/analyze-server-file。  
   * 为文件上传表单添加事件监听，提交时将文件数据发送到 POST /api/upload-and-analyze。  
   * 编写一个函数，用于处理从后端接收到的分析结果（JSON数据和图表HTML片段），并动态地将这些内容插入到页面的指定报告区域。

#### **步骤 5: 整合与数据流**

1. 用户在浏览器中操作。  
2. JavaScript发送API请求到FastAPI后端。  
3. FastAPI端点调用核心引擎中的分析和可视化函数。  
4. 核心引擎返回结构化的Python字典（包含统计数据和图表HTML片段）。  
5. FastAPI将该字典序列化为JSON并返回给前端。  
6. 前端JavaScript接收到JSON，解析后动态生成报告内容并呈现在用户面前。

## **5\. 项目结构 (Project Structure)**

data\_analysis\_report/  
│  
├── main.py                     \# 🚀 FastAPI应用主文件，包含API路由  
├── pyproject.toml              \# (推荐) 项目依赖与配置管理  
│  
├── src/  
│   └── reporter/  
│       ├── \_\_init\_\_.py  
│       │  
│       ├── analysis/           \# (不变) 分析功能集合  
│       │   └── ...  
│       │  
│       ├── visualization/      \# (不变) 可视化功能集合  
│       │   └── ...  
│       │  
│       ├── data\_loader.py      \# (不变) 数据加载模块  
│       └── security.py         \# (新增) 此模块应至少包含两个关键功能：1. 路径沙箱（Path Sandboxing），确保所有文件操作都限制在预设的安全根目录内。2. 路径遍历攻击防护（Path Traversal Prevention），严格校验和清理用户输入，拒绝任何包含 \`..\` 等字符的恶意路径请求。  
│  
├── static/                     \# 存放前端静态文件  
│   └── app.js                  \# 主要的JavaScript逻辑  
│   └── styles.css              \# CSS样式  
│  
└── templates/  
    └── index.html              \# 主页面HTML模板

