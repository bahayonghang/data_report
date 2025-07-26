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

// ====== 工具函数 ======

/**
 * 格式化数据大小
 * @param {number} bytes - 字节数
 * @returns {string} - 格式化后的大小字符串
 */
function formatDataSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 重新生成图表（当图表数据被压缩时）
 * @param {string} containerId - 图表容器ID
 */
function regenerateChart(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div style="text-align: center; color: #6c757d; padding: 40px;">
            <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 15px;"></i>
            <h4 style="margin: 10px 0;">图表重新生成功能</h4>
            <p style="margin: 10px 0;">此功能需要重新请求服务器数据。</p>
            <p style="font-size: 0.9rem; color: #8d6e63;">请返回首页重新分析文件以获取完整的图表数据。</p>
            <div style="margin-top: 20px;">
                <button class="btn btn-secondary btn-sm" onclick="window.location.href='/'">
                    <i class="fas fa-home"></i> 返回首页
                </button>
            </div>
        </div>
    `;
}

/**
 * 显示数据压缩提示信息
 * @param {Object} compressionInfo - 压缩信息
 */
function displayCompressionNotice(compressionInfo) {
    // 在页面顶部插入压缩提示
    const noticeHtml = `
        <div class="compression-notice" style="
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            border: 1px solid #f1c40f;
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; align-items: center; gap: 15px;">
                <i class="fas fa-compress-alt" style="font-size: 1.5rem; color: #f39c12;"></i>
                <div style="flex: 1;">
                    <h4 style="margin: 0 0 8px 0; color: #d68910; font-size: 1.1rem;">
                        <i class="fas fa-info-circle"></i> 数据已压缩显示
                    </h4>
                    <p style="margin: 0; color: #8d6e63; line-height: 1.4;">
                        为了解决浏览器存储限制，部分可视化图表数据已被压缩。统计数据和分析结果完整保留。
                    </p>
                    ${compressionInfo && compressionInfo.timestamp ? `
                        <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #95a5a6;">
                            压缩时间: ${new Date(compressionInfo.timestamp).toLocaleString('zh-CN')}
                        </p>
                    ` : ''}
                </div>
                <button class="btn btn-outline-primary btn-sm" onclick="window.location.href='/'" style="
                    border-color: #f39c12;
                    color: #f39c12;
                    white-space: nowrap;
                ">
                    <i class="fas fa-redo"></i> 重新分析
                </button>
            </div>
        </div>
    `;
    
    // 将提示插入到分析容器的开头
    if (elements.analysisContainer) {
        elements.analysisContainer.insertAdjacentHTML('afterbegin', noticeHtml);
    }
}

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
    
    // 检查数据是否被压缩，如果是则显示提示
    if (data.compressed) {
        displayCompressionNotice(data.compression_info);
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
        <div class="stats-section-container">
            <div class="stats-section-header" onclick="toggleStatsSection('stats-summary')">
                <div class="stats-section-title">
                    <i class="fas fa-chart-pie"></i>
                    <span>统计摘要</span>
                    <span class="stats-count">(${columns.length}个变量)</span>
                </div>
                <div class="stats-section-toggle">
                    <i class="fas fa-chevron-down" id="toggle-stats-summary"></i>
                </div>
            </div>
            <div class="stats-section-description">显示各变量的基本统计信息和缺失值情况</div>
            <div class="stats-section-content collapsed" id="content-stats-summary">
                <div class="overview-grid stats-scrollable">
                    ${summaryCards}
                </div>
            </div>
        </div>
    `;
}

// 显示可视化图表 - 支持可折叠分组
function displayVisualizations(visualizations) {
    if (!elements.visualizations || !visualizations) return;
    
    // 按图表类型分组
    const chartGroups = {
        time_series: {
            title: '时间序列图表',
            icon: 'fas fa-chart-line',
            description: '展示数据随时间变化的趋势',
            charts: []
        },
        correlation: {
            title: '相关性分析',
            icon: 'fas fa-th',
            description: '显示变量之间的相关性强度',
            charts: []
        },
        distribution: {
            title: '数据分布图表',
            icon: 'fas fa-chart-bar',
            description: '显示数据的分布形态和频次',
            charts: []
        },
        box_plots: {
            title: '箱形图分析',
            icon: 'fas fa-square',
            description: '显示数据的分布和异常值',
            charts: []
        }
    };
    
    // 时序图表
    if (visualizations.time_series && Array.isArray(visualizations.time_series)) {
        visualizations.time_series.forEach((chart, index) => {
            if (!chart.error) {
                chartGroups.time_series.charts.push({
                    id: `time-series-chart-${index}`,
                    title: chart.title || `时间序列趋势图 ${index + 1}`,
                    data: chart
                });
            }
        });
    }
    
    // 相关性热力图
    if (visualizations.correlation_heatmap && !visualizations.correlation_heatmap.error) {
        chartGroups.correlation.charts.push({
            id: 'correlation-heatmap',
            title: '变量相关性热力图',
            data: visualizations.correlation_heatmap
        });
    }
    
    // 分布直方图
    if (visualizations.distributions && Array.isArray(visualizations.distributions)) {
        visualizations.distributions.forEach((chart, index) => {
            if (!chart.error) {
                chartGroups.distribution.charts.push({
                    id: `distribution-chart-${index}`,
                    title: chart.title || `数据分布直方图 ${index + 1}`,
                    data: chart
                });
            }
        });
    }
    
    // 箱形图
    if (visualizations.box_plots && Array.isArray(visualizations.box_plots)) {
        visualizations.box_plots.forEach((chart, index) => {
            if (!chart.error) {
                chartGroups.box_plots.charts.push({
                    id: `box-plot-${index}`,
                    title: chart.title || `箱形图 ${index + 1}`,
                    data: chart
                });
            }
        });
    }
    
    // 检查是否有图表数据
    const hasCharts = Object.values(chartGroups).some(group => group.charts.length > 0);
    if (!hasCharts) {
        elements.visualizations.innerHTML = `
            <h3><i class="fas fa-chart-line"></i> 数据可视化</h3>
            <div class="viz-item">
                <p style="text-align: center; color: #6c757d; padding: 40px;">暂无可用的图表数据</p>
            </div>
        `;
        return;
    }
    
    // 生成可折叠的图表分组
    const groupsHtml = Object.entries(chartGroups)
        .filter(([key, group]) => group.charts.length > 0)
        .map(([key, group]) => {
            const chartsHtml = group.charts.map(chart => `
                <div class="viz-item">
                    <div class="viz-header">
                        <h4><i class="fas fa-chart-bar"></i> ${chart.title}</h4>
                        <div class="viz-actions">
                            <button class="btn btn-secondary btn-sm" onclick="downloadChart('${chart.id}')">
                                <i class="fas fa-download"></i> 下载
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="fullscreenChart('${chart.id}')">
                                <i class="fas fa-expand"></i> 全屏
                            </button>
                        </div>
                    </div>
                    <div class="chart-container" id="${chart.id}">
                        <div class="chart-loading">
                            <i class="fas fa-spinner fa-spin"></i> 正在渲染图表...
                        </div>
                    </div>
                </div>
            `).join('');
            
            return `
                <div class="chart-group">
                    <div class="chart-group-header" onclick="toggleChartGroup('${key}')">
                        <div class="chart-group-title">
                            <i class="${group.icon}"></i>
                            <span>${group.title}</span>
                            <span class="chart-count">(${group.charts.length}个图表)</span>
                        </div>
                        <div class="chart-group-toggle">
                            <i class="fas fa-chevron-down" id="toggle-${key}"></i>
                        </div>
                    </div>
                    <div class="chart-group-description">${group.description}</div>
                    <div class="chart-group-content collapsed" id="content-${key}">
                        <div class="viz-grid">
                            ${chartsHtml}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    
    elements.visualizations.innerHTML = `
        <h3><i class="fas fa-chart-line"></i> 数据可视化</h3>
        <div class="chart-groups-container">
            ${groupsHtml}
        </div>
    `;
    
    // 渲染所有图表（即使在折叠状态下也预先渲染）
    setTimeout(() => {
        Object.values(chartGroups).forEach(group => {
            group.charts.forEach(chart => {
                renderPlotlyChart(chart.id, chart.data);
            });
        });
    }, 100);
}

// 渲染Plotly图表
function renderPlotlyChart(containerId, chartData) {
    const container = document.getElementById(containerId);
    if (!container || !chartData) return;
    
    // 检查数据是否被压缩（图表数据被移除）
    if (chartData.compressed || (chartData.image === null && chartData.original_size)) {
        container.innerHTML = `
            <div style="text-align: center; color: #f39c12; padding: 40px; background: #fef9e7; border-radius: 8px; border: 1px solid #f1c40f;">
                <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 15px;"></i>
                <h4 style="margin: 10px 0; color: #d68910;">图表数据已压缩</h4>
                <p style="margin: 10px 0; color: #8d6e63;">为了节省存储空间，此图表的可视化数据已被移除。</p>
                <p style="font-size: 0.9rem; color: #8d6e63;">原始图表大小: ${formatDataSize(chartData.original_size || 0)}</p>
                <div style="margin-top: 20px;">
                    <button class="btn btn-primary btn-sm" onclick="regenerateChart('${containerId}')">
                        <i class="fas fa-refresh"></i> 重新生成图表
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
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
                height: 400,  // 调整为适配4列布局的尺寸
                width: 600,   // 调整为适配4列布局的尺寸
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
        <div class="stats-section-container">
            <div class="stats-section-header" onclick="toggleStatsSection('detailed-stats')">
                <div class="stats-section-title">
                    <i class="fas fa-table"></i>
                    <span>详细统计分析</span>
                    <span class="stats-count">(${columns.length}个变量)</span>
                </div>
                <div class="stats-section-toggle">
                    <i class="fas fa-chevron-down" id="toggle-detailed-stats"></i>
                </div>
            </div>
            <div class="stats-section-description">包含描述性统计、高级统计分析和平稳性检验结果</div>
            <div class="stats-section-content collapsed" id="content-detailed-stats">
                <div class="stats-scrollable">
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
                </div>
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

// 切换图表分组的折叠/展开状态
function toggleChartGroup(groupKey) {
    const content = document.getElementById(`content-${groupKey}`);
    const toggle = document.getElementById(`toggle-${groupKey}`);
    
    if (!content || !toggle) return;
    
    const isCollapsed = content.classList.contains('collapsed');
    
    if (isCollapsed) {
        // 展开
        content.classList.remove('collapsed');
        toggle.classList.remove('fa-chevron-down');
        toggle.classList.add('fa-chevron-up');
        
        // 添加展开动画
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // 动画完成后移除maxHeight限制
        setTimeout(() => {
            content.style.maxHeight = 'none';
        }, 300);
    } else {
        // 折叠
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // 强制重绘
        content.offsetHeight;
        
        content.style.maxHeight = '0';
        toggle.classList.remove('fa-chevron-up');
        toggle.classList.add('fa-chevron-down');
        
        // 动画完成后添加collapsed类
        setTimeout(() => {
            content.classList.add('collapsed');
        }, 300);
    }
}

// 切换统计部分的折叠/展开状态
function toggleStatsSection(sectionKey) {
    const content = document.getElementById(`content-${sectionKey}`);
    const toggle = document.getElementById(`toggle-${sectionKey}`);
    
    if (!content || !toggle) return;
    
    const isCollapsed = content.classList.contains('collapsed');
    
    if (isCollapsed) {
        // 展开
        content.classList.remove('collapsed');
        toggle.classList.remove('fa-chevron-down');
        toggle.classList.add('fa-chevron-up');
        
        // 添加展开动画
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // 动画完成后移除maxHeight限制
        setTimeout(() => {
            content.style.maxHeight = 'none';
        }, 300);
    } else {
        // 折叠
        content.style.maxHeight = content.scrollHeight + 'px';
        
        // 强制重绘
        content.offsetHeight;
        
        content.style.maxHeight = '0';
        toggle.classList.remove('fa-chevron-up');
        toggle.classList.add('fa-chevron-down');
        
        // 动画完成后添加collapsed类
        setTimeout(() => {
            content.classList.add('collapsed');
        }, 300);
    }
}