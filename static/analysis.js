// 分析页面JavaScript逻辑
// 处理分析结果展示、用户交互和页面动画

// 全局变量
let analysisData = null;
let loadingInterval = null;
let progressValue = 0;

// DOM元素引用
const elements = {
    loadingOverlay: null,
    loadingTitle: null,
    loadingSubtitle: null,
    loadingProgressFill: null,
    loadingProgressText: null,
    analysisContainer: null,
    errorPage: null,
    errorMessage: null,
    analysisTimestamp: null,
    fileOverview: null,
    statsSummary: null,
    visualizations: null,
    detailedStats: null,
    backBtn: null,
    exportBtn: null,
    newAnalysisBtn: null,
    retryBtn: null,
    backToHomeBtn: null
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    setupEventListeners();
    startAnalysis();
});

// 初始化DOM元素引用
function initializeElements() {
    elements.loadingOverlay = document.getElementById('loading-overlay');
    elements.loadingTitle = document.getElementById('loading-title');
    elements.loadingSubtitle = document.getElementById('loading-subtitle');
    elements.loadingProgressFill = document.getElementById('loading-progress-fill');
    elements.loadingProgressText = document.getElementById('loading-progress-text');
    elements.analysisContainer = document.getElementById('analysis-container');
    elements.errorPage = document.getElementById('error-page');
    elements.errorMessage = document.getElementById('error-message');
    elements.analysisTimestamp = document.getElementById('analysis-timestamp');
    elements.fileOverview = document.getElementById('file-overview');
    elements.statsSummary = document.getElementById('stats-summary');
    elements.visualizations = document.getElementById('visualizations');
    elements.detailedStats = document.getElementById('detailed-stats');
    elements.backBtn = document.getElementById('back-btn');
    elements.exportBtn = document.getElementById('export-btn');
    elements.newAnalysisBtn = document.getElementById('new-analysis-btn');
    elements.retryBtn = document.getElementById('retry-btn');
    elements.backToHomeBtn = document.getElementById('back-to-home-btn');
}

// 设置事件监听器
function setupEventListeners() {
    // 返回首页按钮
    elements.backBtn?.addEventListener('click', () => {
        window.close();
        // 如果无法关闭窗口，则跳转到首页
        setTimeout(() => {
            window.location.href = '/';
        }, 100);
    });
    
    // 导出报告按钮
    elements.exportBtn?.addEventListener('click', exportResults);
    
    // 新分析按钮
    elements.newAnalysisBtn?.addEventListener('click', () => {
        window.open('/', '_blank');
    });
    
    // 重试按钮
    elements.retryBtn?.addEventListener('click', () => {
        hideError();
        startAnalysis();
    });
    
    // 返回首页按钮（错误页面）
    elements.backToHomeBtn?.addEventListener('click', () => {
        window.location.href = '/';
    });
    
    // 监听窗口关闭事件
    window.addEventListener('beforeunload', () => {
        // 清理sessionStorage中的分析数据
        sessionStorage.removeItem('analysisData');
        sessionStorage.removeItem('analysisError');
    });
}

// 开始分析流程
function startAnalysis() {
    showLoading();
    
    // 检查是否有分析数据
    const storedData = sessionStorage.getItem('analysisData');
    const storedError = sessionStorage.getItem('analysisError');
    
    if (storedError) {
        // 显示错误
        const errorData = JSON.parse(storedError);
        setTimeout(() => {
            showError(errorData.message || '分析过程中出现未知错误');
        }, 2000);
        return;
    }
    
    if (storedData) {
        // 有数据，模拟加载过程然后显示结果
        analysisData = JSON.parse(storedData);
        simulateLoadingProgress(() => {
            displayAnalysisResults(analysisData);
        });
    } else {
        // 没有数据，显示错误
        setTimeout(() => {
            showError('未找到分析数据，请重新上传文件进行分析');
        }, 2000);
    }
}

// 显示加载界面
function showLoading() {
    elements.loadingOverlay.style.display = 'flex';
    elements.analysisContainer.style.display = 'none';
    elements.errorPage.style.display = 'none';
    
    // 重置进度
    progressValue = 0;
    updateLoadingProgress(0);
}

// 模拟加载进度
function simulateLoadingProgress(callback) {
    const steps = [
        { progress: 20, title: '正在解析数据', subtitle: '读取文件内容并验证数据格式...' },
        { progress: 40, title: '正在计算统计指标', subtitle: '计算基础统计信息和数据分布...' },
        { progress: 60, title: '正在生成图表', subtitle: '创建时间序列图和相关性分析...' },
        { progress: 80, title: '正在优化展示', subtitle: '优化图表显示和数据表格...' },
        { progress: 100, title: '分析完成', subtitle: '正在准备展示结果...' }
    ];
    
    let currentStep = 0;
    
    const progressInterval = setInterval(() => {
        if (currentStep < steps.length) {
            const step = steps[currentStep];
            updateLoadingProgress(step.progress, step.title, step.subtitle);
            currentStep++;
        } else {
            clearInterval(progressInterval);
            setTimeout(() => {
                hideLoading();
                callback();
            }, 500);
        }
    }, 800);
}

// 更新加载进度
function updateLoadingProgress(progress, title, subtitle) {
    if (elements.loadingProgressFill) {
        elements.loadingProgressFill.style.width = progress + '%';
    }
    if (elements.loadingProgressText) {
        elements.loadingProgressText.textContent = progress + '%';
    }
    if (title && elements.loadingTitle) {
        elements.loadingTitle.textContent = title;
    }
    if (subtitle && elements.loadingSubtitle) {
        elements.loadingSubtitle.textContent = subtitle;
    }
}

// 隐藏加载界面
function hideLoading() {
    elements.loadingOverlay.classList.add('fade-out');
    setTimeout(() => {
        elements.loadingOverlay.style.display = 'none';
        elements.analysisContainer.style.display = 'block';
    }, 500);
}

// 显示错误页面
function showError(message) {
    hideLoading();
    elements.errorMessage.textContent = message;
    elements.errorPage.style.display = 'flex';
}

// 隐藏错误页面
function hideError() {
    elements.errorPage.style.display = 'none';
}

// 显示分析结果
function displayAnalysisResults(data) {
    analysisData = data;
    const resultData = data.data;
    
    // 设置时间戳
    if (elements.analysisTimestamp) {
        elements.analysisTimestamp.textContent = new Date().toLocaleString('zh-CN');
    }
    
    // 显示各个部分
    displayFileOverview(resultData.file_info, resultData.time_info);
    displayStatsSummary(resultData.statistics, resultData.missing_values);
    displayVisualizations(resultData.visualizations);
    displayDetailedStats(resultData.statistics, resultData.stationarity_tests);
    
    // 显示容器
    elements.analysisContainer.style.display = 'block';
}

// 显示文件概览
function displayFileOverview(fileInfo, timeInfo) {
    if (!elements.fileOverview) return;
    
    const timeRange = timeInfo.time_range;
    const hasTimeData = timeInfo.time_column && timeRange;
    
    elements.fileOverview.innerHTML = `
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
    if (!elements.statsSummary) return;
    
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
    
    elements.statsSummary.innerHTML = `
        <h3><i class="fas fa-chart-pie"></i> 统计摘要</h3>
        <div class="overview-grid">
            ${summaryCards}
        </div>
    `;
}

// 显示可视化图表
function displayVisualizations(visualizations) {
    if (!elements.visualizations || !visualizations) return;
    
    const vizItems = [];
    
    // 时序图表 - 现在是数组，每个变量一个图表
    if (visualizations.time_series && Array.isArray(visualizations.time_series)) {
        visualizations.time_series.forEach((chart, index) => {
            if (!chart.error) {
                vizItems.push({
                    id: `time-series-chart-${index}`,
                    title: chart.title || `时间序列趋势图 ${index + 1}`,
                    data: chart,
                    description: '展示数据随时间变化的趋势'
                });
            }
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
        elements.visualizations.innerHTML = `
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
    
    elements.visualizations.innerHTML = `
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
    if (!elements.detailedStats || !statistics) return;
    
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
    
    elements.detailedStats.innerHTML = `
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
                            <th>第一四分位数</th>
                            <th>第三四分位数</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${descriptiveRows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 高级统计 -->
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
                            <th>P值</th>
                            <th>平稳性</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${advancedRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// 导出PDF报告
function exportResults() {
    if (!analysisData) return;
    
    // 显示导出提示
    const exportBtn = elements.exportBtn;
    const originalText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在生成PDF...';
    exportBtn.disabled = true;
    
    // 准备打印样式
    preparePrintStyles();
    
    // 等待图表完全渲染后再打印
    setTimeout(() => {
        // 设置文档标题
        const originalTitle = document.title;
        document.title = `数据分析报告_${new Date().toISOString().split('T')[0]}`;
        
        // 触发浏览器打印对话框
        window.print();
        
        // 恢复原始状态
        setTimeout(() => {
            document.title = originalTitle;
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
            removePrintStyles();
        }, 1000);
    }, 500);
}

// 准备打印样式
function preparePrintStyles() {
    // 创建打印专用样式
    const printStyles = document.createElement('style');
    printStyles.id = 'print-styles';
    printStyles.textContent = `
        @media print {
            /* 隐藏不需要打印的元素 */
            .analysis-header,
            .header-actions,
            .viz-actions,
            .error-page,
            #loading-overlay {
                display: none !important;
            }
            
            /* 页面设置 */
            body {
                background: white !important;
                color: black !important;
                font-size: 12pt;
                line-height: 1.4;
            }
            
            .analysis-page {
                background: white !important;
            }
            
            .analysis-content {
                padding: 0 !important;
            }
            
            .content-section {
                background: white !important;
                box-shadow: none !important;
                border: 1px solid #ddd !important;
                margin-bottom: 20pt !important;
                page-break-inside: avoid;
                padding: 15pt !important;
            }
            
            .content-section h3 {
                color: #333 !important;
                border-bottom: 2px solid #333;
                padding-bottom: 5pt;
                margin-bottom: 15pt !important;
            }
            
            /* 表格样式 */
            .stats-table {
                border-collapse: collapse;
                width: 100%;
                font-size: 10pt;
            }
            
            .stats-table th,
            .stats-table td {
                border: 1px solid #333 !important;
                padding: 5pt !important;
                text-align: left;
            }
            
            .stats-table th {
                background: #f0f0f0 !important;
                font-weight: bold;
            }
            
            /* 概览卡片 */
            .overview-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150pt, 1fr));
                gap: 10pt;
            }
            
            .overview-card {
                border: 1px solid #ddd !important;
                padding: 10pt !important;
                background: white !important;
                text-align: center;
            }
            
            /* 图表容器 */
            .viz-item {
                page-break-inside: avoid;
                margin-bottom: 20pt;
                border: 1px solid #ddd;
                padding: 10pt;
            }
            
            .viz-header h4 {
                color: #333 !important;
                margin-bottom: 10pt;
            }
            
            .chart-container {
                max-height: 400pt;
                overflow: hidden;
            }
            
            /* 页面标题 */
            .analysis-page::before {
                content: "数据分析报告";
                display: block;
                font-size: 18pt;
                font-weight: bold;
                text-align: center;
                margin-bottom: 20pt;
                padding-bottom: 10pt;
                border-bottom: 3px solid #333;
            }
            
            /* 页脚信息 */
            .analysis-page::after {
                content: "生成时间: " attr(data-timestamp);
                display: block;
                font-size: 10pt;
                text-align: center;
                margin-top: 20pt;
                padding-top: 10pt;
                border-top: 1px solid #ddd;
            }
        }
    `;
    
    document.head.appendChild(printStyles);
    
    // 设置时间戳
    document.querySelector('.analysis-page').setAttribute('data-timestamp', new Date().toLocaleString('zh-CN'));
}

// 移除打印样式
function removePrintStyles() {
    const printStyles = document.getElementById('print-styles');
    if (printStyles) {
        printStyles.remove();
    }
}

// 下载图表
function downloadChart(chartId) {
    const element = document.getElementById(chartId);
    if (element && element._fullLayout) {
        Plotly.downloadImage(element, {
            format: 'png',
            width: 1000,
            height: 600,
            filename: `chart_${chartId}`
        });
    }
}

// 全屏显示图表
function fullscreenChart(chartId) {
    const element = document.getElementById(chartId);
    if (element) {
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }
    }
}