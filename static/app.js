// 客户端 JavaScript 逻辑
// 处理文件上传、服务器文件选择和分析结果展示

// 全局状态管理
let currentAnalysisData = null;
let isAnalyzing = false;

// DOM 元素引用
const elements = {
    uploadZone: null,
    fileInput: null,
    uploadBtn: null,
    serverFileList: null,
    statusSection: null,
    errorSection: null,
    resultsSection: null,
    progressFill: null,
    progressText: null,
    statusTitle: null,
    errorMessage: null,
    modal: null
};

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    setupEventListeners();
    loadServerFiles();
});

// 初始化DOM元素引用
function initializeElements() {
    elements.uploadZone = document.getElementById('upload-zone');
    elements.fileInput = document.getElementById('file-input');
    elements.uploadBtn = document.getElementById('upload-btn');
    elements.serverFileList = document.getElementById('server-file-list');
    elements.statusSection = document.getElementById('status-section');
    elements.errorSection = document.getElementById('error-section');
    elements.resultsSection = document.getElementById('results-section');
    elements.progressFill = document.getElementById('progress-fill');
    elements.progressText = document.getElementById('progress-text');
    elements.statusTitle = document.getElementById('status-title');
    elements.errorMessage = document.getElementById('error-message');
    elements.modal = document.getElementById('modal');
}

// 设置事件监听器
function setupEventListeners() {
    // 文件上传相关事件
    elements.uploadBtn?.addEventListener('click', () => elements.fileInput?.click());
    elements.fileInput?.addEventListener('change', handleFileSelect);
    
    // 拖拽上传事件
    elements.uploadZone?.addEventListener('dragover', handleDragOver);
    elements.uploadZone?.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone?.addEventListener('drop', handleFileDrop);
    // 优化点击事件：只有当点击的不是上传按钮时才触发文件选择，避免重复触发
    elements.uploadZone?.addEventListener('click', (event) => {
        // 检查点击目标是否为上传按钮或其子元素
        if (!event.target.closest('#upload-btn')) {
            elements.fileInput?.click();
        }
    });
    
    // 错误处理事件
    document.getElementById('retry-btn')?.addEventListener('click', retryLastOperation);
    document.getElementById('dismiss-error-btn')?.addEventListener('click', hideError);
    
    // 结果区域事件
    document.getElementById('new-analysis-btn')?.addEventListener('click', startNewAnalysis);
    document.getElementById('export-btn')?.addEventListener('click', exportResults);
    
    // 模态框事件
    document.getElementById('modal-close')?.addEventListener('click', hideModal);
    document.getElementById('modal-cancel')?.addEventListener('click', hideModal);
    
    // 点击模态框背景关闭
    elements.modal?.addEventListener('click', (e) => {
        if (e.target === elements.modal) {
            hideModal();
        }
    });
}

// ====== 文件上传功能 ======

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndUploadFile(file);
    }
}

// 处理拖拽悬停
function handleDragOver(event) {
    event.preventDefault();
    elements.uploadZone?.classList.add('drag-over');
}

// 处理拖拽离开
function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadZone?.classList.remove('drag-over');
}

// 处理文件拖拽
function handleFileDrop(event) {
    event.preventDefault();
    elements.uploadZone?.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        validateAndUploadFile(files[0]);
    }
}

// 验证并上传文件
function validateAndUploadFile(file) {
    // 验证文件类型
    const allowedTypes = ['.csv', '.parquet'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showError('不支持的文件类型', `请上传 CSV 或 Parquet 格式的文件。当前文件: ${file.name}`);
        return;
    }
    
    // 验证文件大小 (1GB)
    const maxSize = 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('文件过大', `文件大小不能超过 1GB。当前文件大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
        return;
    }
    
    // 开始上传和分析
    uploadAndAnalyze(file);
}

// ====== API 调用函数 ======

// 获取服务器文件列表
async function listServerFiles() {
    try {
        const response = await fetch('/api/list-files');
        const data = await response.json();
        
        if (data.success) {
            displayServerFiles(data.files);
        } else {
            throw new Error(data.error?.message || '获取文件列表失败');
        }
    } catch (error) {
        console.error('Error loading server files:', error);
        displayServerFilesError(error.message);
    }
}

// 分析服务器文件
async function analyzeServerFile(filename) {
    if (isAnalyzing) return;
    
    try {
        showProgress('正在分析服务器文件...', '正在加载文件: ' + filename);
        isAnalyzing = true;
        
        // 模拟进度更新
        updateProgress(20, '正在读取文件...');
        
        const formData = new FormData();
        formData.append('filename', filename);
        
        const response = await fetch('/api/analyze-server-file', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(80, '正在生成分析结果...');
        
        const data = await response.json();
        
        if (data.success) {
            updateProgress(100, '分析完成!');
            setTimeout(() => {
                // 分析成功，将数据存储到sessionStorage并打开新页面
                sessionStorage.setItem('analysisData', JSON.stringify(data));
                
                // 打开新的分析结果页面
                const analysisWindow = window.open('/analysis', '_blank');
                
                // 如果无法打开新窗口，则在当前页面跳转
                if (!analysisWindow) {
                    window.location.href = '/analysis';
                }
                
                hideProgress();
            }, 500);
        } else {
            throw new Error(data.error?.message || '分析失败');
        }
    } catch (error) {
        console.error('Error analyzing server file:', error);
        hideProgress();
        showError('服务器文件分析失败', error.message);
    } finally {
        isAnalyzing = false;
    }
}

// 上传并分析文件
async function uploadAndAnalyze(file) {
    if (isAnalyzing) return;
    
    try {
        showProgress('正在上传和分析文件...', '正在上传文件: ' + file.name);
        isAnalyzing = true;
        
        // 模拟上传进度
        updateProgress(30, '正在上传文件...');
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload-and-analyze', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(80, '正在生成分析结果...');
        
        const data = await response.json();
        
        if (data.success) {
            updateProgress(100, '分析完成!');
            setTimeout(() => {
                // 分析成功，将数据存储到sessionStorage并打开新页面
                sessionStorage.setItem('analysisData', JSON.stringify(data));
                
                // 打开新的分析结果页面
                const analysisWindow = window.open('/analysis', '_blank');
                
                // 如果无法打开新窗口，则在当前页面跳转
                if (!analysisWindow) {
                    window.location.href = '/analysis';
                }
                
                hideProgress();
            }, 500);
        } else {
            throw new Error(data.error?.message || '分析失败');
        }
    } catch (error) {
        console.error('Error uploading and analyzing file:', error);
        hideProgress();
        showError('文件上传分析失败', error.message);
    } finally {
        isAnalyzing = false;
        // 重置文件输入
        if (elements.fileInput) {
            elements.fileInput.value = '';
        }
    }
}

// ====== UI 更新函数 ======

// 显示服务器文件列表
function displayServerFiles(files) {
    if (!elements.serverFileList) return;
    
    if (files.length === 0) {
        elements.serverFileList.innerHTML = `
            <div class="loading-files">
                <i class="fas fa-folder-open"></i>
                <p>暂无可用的数据文件</p>
            </div>
        `;
        return;
    }
    
    const fileItems = files.map(file => {
        const fileSize = formatFileSize(file.size);
        const modifiedDate = formatDate(file.modified);
        const fileIcon = getFileIcon(file.name);
        
        return `
            <div class="file-item" onclick="selectServerFile('${file.name}')">
                <div class="file-info">
                    <i class="file-icon ${fileIcon}"></i>
                    <div class="file-details">
                        <h4>${file.name}</h4>
                        <div class="file-meta">${fileSize} • 修改于 ${modifiedDate}</div>
                    </div>
                </div>
                <button class="btn btn-primary btn-sm">
                    <i class="fas fa-play"></i> 分析
                </button>
            </div>
        `;
    }).join('');
    
    elements.serverFileList.innerHTML = fileItems;
}

// 显示服务器文件错误
function displayServerFilesError(errorMessage) {
    if (!elements.serverFileList) return;
    
    elements.serverFileList.innerHTML = `
        <div class="loading-files">
            <i class="fas fa-exclamation-triangle" style="color: #e53e3e;"></i>
            <p>加载文件列表失败</p>
            <p style="font-size: 0.9rem; color: #6c757d; margin-top: 10px;">${errorMessage}</p>
            <button class="btn btn-secondary btn-sm" onclick="loadServerFiles()" style="margin-top: 15px;">
                <i class="fas fa-redo"></i> 重试
            </button>
        </div>
    `;
}

// 选择服务器文件
function selectServerFile(filename) {
    analyzeServerFile(filename);
}

// 显示进度
function showProgress(title, text) {
    hideError();
    hideResults();
    
    if (elements.statusTitle) elements.statusTitle.textContent = title;
    if (elements.progressText) elements.progressText.textContent = text;
    if (elements.progressFill) elements.progressFill.style.width = '0%';
    
    elements.statusSection?.style.setProperty('display', 'block');
    elements.statusSection?.classList.add('fade-in-up');
}

// 更新进度
function updateProgress(percentage, text) {
    if (elements.progressFill) {
        elements.progressFill.style.width = percentage + '%';
    }
    if (elements.progressText && text) {
        elements.progressText.textContent = text;
    }
}

// 隐藏进度
function hideProgress() {
    elements.statusSection?.style.setProperty('display', 'none');
}

// 显示错误
function showError(title, message) {
    hideProgress();
    hideResults();
    
    if (elements.errorMessage) {
        elements.errorMessage.innerHTML = `<strong>${title}</strong><br>${message}`;
    }
    
    elements.errorSection?.style.setProperty('display', 'block');
    elements.errorSection?.classList.add('fade-in-up');
}

// 隐藏错误
function hideError() {
    elements.errorSection?.style.setProperty('display', 'none');
}

// 隐藏结果
function hideResults() {
    elements.resultsSection?.style.setProperty('display', 'none');
}

// 显示分析结果
function displayAnalysisResults(data) {
    hideProgress();
    hideError();
    
    const resultData = data.data;
    
    // 显示文件概览
    displayFileOverview(resultData.file_info, resultData.time_info);
    
    // 显示统计摘要
    displayStatsSummary(resultData.statistics, resultData.missing_values);
    
    // 显示可视化图表
    displayVisualizations(resultData.visualizations);
    
    // 显示详细统计
    displayDetailedStats(resultData.statistics, resultData.stationarity_tests);
    
    elements.resultsSection?.style.setProperty('display', 'block');
    elements.resultsSection?.classList.add('fade-in-up');
    
    // 滚动到结果区域
    elements.resultsSection?.scrollIntoView({ behavior: 'smooth' });
}

// 显示文件概览
function displayFileOverview(fileInfo, timeInfo) {
    const overviewElement = document.getElementById('file-overview');
    if (!overviewElement) return;
    
    const timeRange = timeInfo.time_range;
    const hasTimeData = timeInfo.time_column && timeRange;
    
    overviewElement.innerHTML = `
        <h3><i class="fas fa-info-circle"></i> 文件概览</h3>
        <div class="overview-grid">
            <div class="overview-card">
                <div class="number">${fileInfo.name}</div>
                <div class="label">文件名称</div>
            </div>
            <div class="overview-card">
                <div class="number">${fileInfo.rows.toLocaleString()}</div>
                <div class="label">数据行数</div>
            </div>
            <div class="overview-card">
                <div class="number">${fileInfo.columns}</div>
                <div class="label">数据列数</div>
            </div>
            ${hasTimeData ? `
                <div class="overview-card">
                    <div class="number">${timeInfo.time_column}</div>
                    <div class="label">时间列</div>
                </div>
                <div class="overview-card">
                    <div class="number">${timeRange.duration_days || 0}</div>
                    <div class="label">时间跨度(天)</div>
                </div>
            ` : ''}
        </div>
    `;
}

// 显示统计摘要
function displayStatsSummary(statistics, missingValues) {
    const summaryElement = document.getElementById('stats-summary');
    if (!summaryElement) return;
    
    const columns = Object.keys(statistics);
    if (columns.length === 0) return;
    
    let summaryCards = '';
    
    columns.forEach(column => {
        const stats = statistics[column];
        const missing = missingValues[column];
        
        summaryCards += `
            <div class="overview-card">
                <h4>${column}</h4>
                <div class="file-meta">
                    均值: ${stats.mean.toFixed(2)} | 
                    标准差: ${stats.std.toFixed(2)}<br>
                    缺失值: ${missing.null_count} (${missing.null_percentage}%)
                </div>
            </div>
        `;
    });
    
    summaryElement.innerHTML = `
        <h3><i class="fas fa-chart-pie"></i> 统计摘要</h3>
        <div class="overview-grid">
            ${summaryCards}
        </div>
    `;
}

// ====== 工具函数 ======

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 获取文件图标
function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    switch (extension) {
        case 'csv':
            return 'fas fa-file-csv';
        case 'parquet':
            return 'fas fa-file-code';
        default:
            return 'fas fa-file';
    }
}

// 重试上次操作
function retryLastOperation() {
    hideError();
    loadServerFiles();
}

// 开始新分析
function startNewAnalysis() {
    hideResults();
    hideError();
    currentAnalysisData = null;
    // 重置文件输入
    if (elements.fileInput) {
        elements.fileInput.value = '';
    }
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 导出结果
function exportResults() {
    if (!currentAnalysisData) return;
    
    // 创建导出数据
    const exportData = {
        timestamp: new Date().toISOString(),
        file_info: currentAnalysisData.data.file_info,
        statistics: currentAnalysisData.data.statistics,
        // 不包含可视化数据以减小文件大小
    };
    
    // 下载JSON文件
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 显示模态框
function showModal(title, content, confirmCallback) {
    if (!elements.modal) return;
    
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = content;
    
    elements.modal.style.display = 'flex';
    
    // 设置确认回调
    const confirmBtn = document.getElementById('modal-confirm');
    confirmBtn.onclick = () => {
        if (confirmCallback) confirmCallback();
        hideModal();
    };
}

// 隐藏模态框
function hideModal() {
    if (elements.modal) {
        elements.modal.style.display = 'none';
    }
}

// 加载服务器文件
function loadServerFiles() {
    listServerFiles();
}

// ====== 任务7.3: 动态结果渲染 ======

// 显示可视化图表
function displayVisualizations(visualizations) {
    const vizElement = document.getElementById('visualizations');
    if (!vizElement || !visualizations) return;
    
    const vizItems = [];
    
    // 时序图表
    if (visualizations.time_series && !visualizations.time_series.error) {
        vizItems.push({
            id: 'time-series-chart',
            title: '时间序列趋势图',
            data: visualizations.time_series,
            description: '展示数据随时间变化的趋势'
        });
    }
    
    // 相关性热力图
    if (visualizations.correlation_heatmap && !visualizations.correlation_heatmap.error) {
        vizItems.push({
            id: 'correlation-heatmap',
            title: '变量相关性热力图',
            data: visualizations.correlation_heatmap,
            description: '显示变量之间的相关性强度'
        });
    }
    
    // 分布直方图
    if (visualizations.distributions && Array.isArray(visualizations.distributions)) {
        visualizations.distributions.forEach((chart, index) => {
            if (!chart.error) {
                vizItems.push({
                    id: `distribution-chart-${index}`,
                    title: `数据分布直方图 ${index + 1}`,
                    data: chart,
                    description: '显示数据的分布形态和频次'
                });
            }
        });
    }
    
    // 箱形图
    if (visualizations.box_plots && Array.isArray(visualizations.box_plots)) {
        visualizations.box_plots.forEach((chart, index) => {
            if (!chart.error) {
                vizItems.push({
                    id: `box-plot-${index}`,
                    title: `箱形图 ${index + 1}`,
                    data: chart,
                    description: '显示数据的分布和异常值'
                });
            }
        });
    }
    
    if (vizItems.length === 0) {
        vizElement.innerHTML = `
            <h3><i class="fas fa-chart-line"></i> 数据可视化</h3>
            <div class="viz-item">
                <p style="text-align: center; color: #6c757d; padding: 40px;">暂无可用的图表数据</p>
            </div>
        `;
        return;
    }
    
    // 生成可视化网格
    const vizGrid = vizItems.map(item => `
        <div class="viz-item">
            <div class="viz-header">
                <h4><i class="fas fa-chart-bar"></i> ${item.title}</h4>
                <div class="viz-actions">
                    <button class="btn btn-secondary btn-sm" onclick="downloadChart('${item.id}')">
                        <i class="fas fa-download"></i> 下载
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="fullscreenChart('${item.id}')">
                        <i class="fas fa-expand"></i> 全屏
                    </button>
                </div>
            </div>
            <p class="viz-description">${item.description}</p>
            <div class="chart-container" id="${item.id}">
                <div class="chart-loading">
                    <i class="fas fa-spinner fa-spin"></i> 正在渲染图表...
                </div>
            </div>
        </div>
    `).join('');
    
    vizElement.innerHTML = `
        <h3><i class="fas fa-chart-line"></i> 数据可视化</h3>
        <div class="viz-grid">
            ${vizGrid}
        </div>
    `;
    
    // 渲染Plotly图表
    setTimeout(() => {
        vizItems.forEach(item => {
            renderPlotlyChart(item.id, item.data);
        });
    }, 100);
}

// 渲染Plotly图表
function renderPlotlyChart(containerId, chartData) {
    const container = document.getElementById(containerId);
    if (!container || !chartData) return;
    
    try {
        // 配置图表选项
        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            displaylogo: false,
            toImageButtonOptions: {
                format: 'png',
                filename: `chart_${containerId}`,
                height: 600,
                width: 1000,
                scale: 2
            }
        };
        
        // 创建图表
        Plotly.newPlot(containerId, chartData.data || [], chartData.layout || {}, config)
            .then(() => {
                // 图表渲染完成后的处理
                container.querySelector('.chart-loading')?.remove();
                
                // 添加图表交互事件
                container.on('plotly_hover', function(data) {
                    // 可以添加自定义悬停处理
                });
                
                container.on('plotly_click', function(data) {
                    // 可以添加自定义点击处理
                });
            })
            .catch(error => {
                console.error('Error rendering chart:', error);
                container.innerHTML = `
                    <div style="text-align: center; color: #e53e3e; padding: 40px;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>图表渲染失败</p>
                        <p style="font-size: 0.9rem; margin-top: 10px;">${error.message}</p>
                    </div>
                `;
            });
    } catch (error) {
        console.error('Error creating chart:', error);
        container.innerHTML = `
            <div style="text-align: center; color: #e53e3e; padding: 40px;">
                <i class="fas fa-exclamation-triangle"></i>
                <p>图表创建失败</p>
            </div>
        `;
    }
}

// 显示详细统计表格
function displayDetailedStats(statistics, stationarityTests) {
    const statsElement = document.getElementById('detailed-stats');
    if (!statsElement || !statistics) return;
    
    const columns = Object.keys(statistics);
    if (columns.length === 0) return;
    
    // 创建描述性统计表格
    const descriptiveRows = columns.map(column => {
        const stats = statistics[column];
        return `
            <tr>
                <td><strong>${column}</strong></td>
                <td>${stats.count}</td>
                <td>${stats.mean.toFixed(4)}</td>
                <td>${stats.median.toFixed(4)}</td>
                <td>${stats.std.toFixed(4)}</td>
                <td>${stats.min.toFixed(4)}</td>
                <td>${stats.max.toFixed(4)}</td>
                <td>${stats.q1.toFixed(4)}</td>
                <td>${stats.q3.toFixed(4)}</td>
            </tr>
        `;
    }).join('');
    
    // 创建高级统计表格
    const advancedRows = columns.map(column => {
        const stats = statistics[column];
        const stationarity = stationarityTests && stationarityTests[column] ? stationarityTests[column] : null;
        
        return `
            <tr>
                <td><strong>${column}</strong></td>
                <td>${stats.skewness.toFixed(4)}</td>
                <td>${stats.kurtosis.toFixed(4)}</td>
                <td>${stationarity ? stationarity.adf_statistic.toFixed(4) : 'N/A'}</td>
                <td>${stationarity ? stationarity.p_value.toFixed(4) : 'N/A'}</td>
                <td>
                    ${stationarity ? 
                        `<span class="status-badge ${stationarity.is_stationary ? 'status-success' : 'status-warning'}">
                            ${stationarity.is_stationary ? '平稳' : '非平稳'}
                        </span>` : 'N/A'
                    }
                </td>
            </tr>
        `;
    }).join('');
    
    statsElement.innerHTML = `
        <h3><i class="fas fa-table"></i> 详细统计分析</h3>
        
        <!-- 描述性统计 -->
        <div class="stats-section">
            <h4>描述性统计</h4>
            <div class="table-container">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>变量</th>
                            <th>计数</th>
                            <th>均值</th>
                            <th>中位数</th>
                            <th>标准差</th>
                            <th>最小值</th>
                            <th>最大值</th>
                            <th>Q1</th>
                            <th>Q3</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${descriptiveRows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 高级统计 -->
        ${stationarityTests ? `
            <div class="stats-section">
                <h4>高级统计分析</h4>
                <div class="table-container">
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>变量</th>
                                <th>偏度</th>
                                <th>峰度</th>
                                <th>ADF统计量</th>
                                <th>p值</th>
                                <th>平稳性</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${advancedRows}
                        </tbody>
                    </table>
                </div>
            </div>
        ` : ''}
        
        <!-- 数据导出 -->
        <div class="stats-actions">
            <button class="btn btn-secondary" onclick="exportStatsTable()">
                <i class="fas fa-file-excel"></i> 导出统计表格
            </button>
            <button class="btn btn-secondary" onclick="copyStatsToClipboard()">
                <i class="fas fa-copy"></i> 复制到剪贴板
            </button>
        </div>
    `;
}

// ====== 图表交互功能 ======

// 下载图表
function downloadChart(chartId) {
    const element = document.getElementById(chartId);
    if (!element) return;
    
    // 使用Plotly的下载功能
    Plotly.downloadImage(chartId, {
        format: 'png',
        width: 1200,
        height: 800,
        filename: `chart_${chartId}_${new Date().toISOString().split('T')[0]}`
    }).catch(error => {
        console.error('Download failed:', error);
        showError('下载失败', '无法下载图表，请重试。');
    });
}

// 全屏显示图表
function fullscreenChart(chartId) {
    const element = document.getElementById(chartId);
    if (!element) return;
    
    const chartData = element._fullData || [];
    const chartLayout = element._fullLayout || {};
    
    // 创建全屏模态框内容
    const modalContent = `
        <div id="fullscreen-chart" style="width: 100%; height: 70vh;"></div>
    `;
    
    showModal('图表详情', modalContent, null);
    
    // 隐藏确认按钮，只显示关闭
    document.getElementById('modal-confirm').style.display = 'none';
    
    // 在模态框中渲染图表
    setTimeout(() => {
        const fullscreenLayout = {
            ...chartLayout,
            width: undefined,
            height: undefined,
            autosize: true
        };
        
        Plotly.newPlot('fullscreen-chart', chartData, fullscreenLayout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        });
    }, 100);
}

// ====== 数据导出功能 ======

// 导出统计表格
function exportStatsTable() {
    if (!currentAnalysisData) return;
    
    const statistics = currentAnalysisData.data.statistics;
    const missingValues = currentAnalysisData.data.missing_values;
    const stationarityTests = currentAnalysisData.data.stationarity_tests;
    
    // 创建CSV数据
    const csvData = [];
    
    // 表头
    csvData.push([
        '变量名', '计数', '均值', '中位数', '标准差', '最小值', '最大值', 'Q1', 'Q3',
        '偏度', '峰度', '缺失值数量', '缺失值百分比', 'ADF统计量', 'p值', '是否平稳'
    ]);
    
    // 数据行
    Object.keys(statistics).forEach(column => {
        const stats = statistics[column];
        const missing = missingValues[column];
        const stationarity = stationarityTests && stationarityTests[column];
        
        csvData.push([
            column,
            stats.count,
            stats.mean.toFixed(4),
            stats.median.toFixed(4),
            stats.std.toFixed(4),
            stats.min.toFixed(4),
            stats.max.toFixed(4),
            stats.q1.toFixed(4),
            stats.q3.toFixed(4),
            stats.skewness.toFixed(4),
            stats.kurtosis.toFixed(4),
            missing.null_count,
            missing.null_percentage,
            stationarity ? stationarity.adf_statistic.toFixed(4) : '',
            stationarity ? stationarity.p_value.toFixed(4) : '',
            stationarity ? (stationarity.is_stationary ? '平稳' : '非平稳') : ''
        ]);
    });
    
    // 转换为CSV字符串
    const csvString = csvData.map(row => 
        row.map(cell => `"${cell}"`).join(',')
    ).join('\n');
    
    // 下载CSV文件
    const blob = new Blob(['\ufeff' + csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `statistics_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 复制统计数据到剪贴板
function copyStatsToClipboard() {
    if (!currentAnalysisData) return;
    
    const statistics = currentAnalysisData.data.statistics;
    
    // 创建简化的文本格式
    let textData = '统计分析结果\n';
    textData += '==================\n\n';
    
    Object.keys(statistics).forEach(column => {
        const stats = statistics[column];
        textData += `${column}:\n`;
        textData += `  均值: ${stats.mean.toFixed(4)}\n`;
        textData += `  中位数: ${stats.median.toFixed(4)}\n`;
        textData += `  标准差: ${stats.std.toFixed(4)}\n`;
        textData += `  范围: ${stats.min.toFixed(4)} - ${stats.max.toFixed(4)}\n\n`;
    });
    
    // 复制到剪贴板
    navigator.clipboard.writeText(textData).then(() => {
        // 显示成功提示
        showModal('复制成功', '统计数据已复制到剪贴板', null);
        document.getElementById('modal-confirm').style.display = 'none';
    }).catch(error => {
        console.error('Copy failed:', error);
        showError('复制失败', '无法复制到剪贴板，请手动选择复制。');
    });
}