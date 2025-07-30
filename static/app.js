// 客户端 JavaScript 逻辑
// 处理文件上传、服务器文件选择和分析结果展示

// 全局状态管理
let currentAnalysisData = null;
let isAnalyzing = false;
let currentView = 'upload'; // 'upload', 'history', 'search'
let fileHistory = [];
let searchResults = [];

// DOM 元素引用
const elements = {
    uploadZone: null,
    fileInput: null,
    uploadBtn: null,
    // 服务器文件列表已删除
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
    // 初始加载首页数据
    loadHomepageData();
});

// 初始化DOM元素引用
function initializeElements() {
    elements.uploadZone = document.getElementById('upload-zone');
    elements.fileInput = document.getElementById('file-input');
    elements.uploadBtn = document.getElementById('upload-btn');
    // 服务器文件列表元素已删除
    
    // 导航相关元素通过class选择器获取，不需要单独的ID引用
    
    // 视图容器
    elements.uploadView = document.getElementById('upload-view');
    elements.historyView = document.getElementById('history-view');
    elements.searchView = document.getElementById('search-view');
    
    // 历史记录相关
    elements.historyList = document.getElementById('history-list');
    elements.historyFilter = document.getElementById('history-filter');
    elements.loadMoreBtn = document.getElementById('load-more-btn');
    
    // 搜索相关
    elements.searchInput = document.getElementById('search-input');
    elements.searchBtn = document.getElementById('search-btn');
    elements.searchResults = document.getElementById('search-results');
    
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
    
    // 导航切换事件 - 使用正确的选择器
    document.querySelectorAll('.nav-item').forEach(navItem => {
        navItem.addEventListener('click', () => {
            const view = navItem.getAttribute('data-view');
            switchView(view);
        });
    });
    
    // 历史记录相关事件
    elements.historyFilter?.addEventListener('change', () => loadFileHistory(true));
    elements.loadMoreBtn?.addEventListener('click', loadMoreHistory);
    
    // 搜索相关事件
    elements.searchBtn?.addEventListener('click', performSearch);
    elements.searchInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
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

// 服务器文件列表功能已删除

// 服务器文件分析功能已删除

// 上传并分析文件
async function uploadAndAnalyze(file) {
    if (isAnalyzing) return;
    
    // 创建AbortController用于超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
        controller.abort();
    }, 120000); // 2分钟超时
    
    try {
        showProgress('正在上传和分析文件...', '正在上传文件: ' + file.name);
        isAnalyzing = true;
        
        // 模拟上传进度
        updateProgress(10, '正在上传文件...');
        
        const formData = new FormData();
        formData.append('file', file);
        
        // 添加超时和错误处理的fetch请求
        const response = await fetch('/api/upload-and-analyze', {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            // 添加请求头以便后端识别
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        updateProgress(60, '正在处理数据...');
        
        // 检查HTTP状态码
        if (!response.ok) {
            let errorMessage = `HTTP错误: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail?.message || errorData.message || errorMessage;
            } catch (parseError) {
                // 如果无法解析错误响应，使用默认错误信息
                console.warn('无法解析错误响应:', parseError);
            }
            throw new Error(errorMessage);
        }
        
        updateProgress(80, '正在生成分析结果...');
        
        const data = await response.json();
        
        if (data.success) {
            updateProgress(100, '分析完成!');
            setTimeout(() => {
                // 分析成功，安全存储数据到sessionStorage并打开新页面
                if (safeStoreAnalysisData(data)) {
                    // 打开新的分析结果页面
                    const analysisWindow = window.open('/analysis', '_blank');
                    
                    // 如果无法打开新窗口，则在当前页面跳转
                    if (!analysisWindow) {
                        window.location.href = '/analysis';
                    }
                } else {
                    // 存储失败，显示错误信息
                    showError('数据存储失败', '分析结果数据过大，无法在浏览器中存储。请尝试分析较小的数据文件。');
                }
                
                hideProgress();
            }, 500);
        } else {
            throw new Error(data.error?.message || data.message || '分析失败');
        }
    } catch (error) {
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        console.error('Error uploading and analyzing file:', error);
        hideProgress();
        
        // 根据错误类型提供更详细的错误信息
        let errorTitle = '文件上传分析失败';
        let errorMessage = error.message;
        
        if (error.name === 'AbortError') {
            errorTitle = '请求超时';
            errorMessage = '文件分析时间过长，请尝试上传较小的文件或稍后重试。';
        } else if (error.message.includes('Failed to fetch')) {
            errorTitle = '网络连接错误';
            errorMessage = '无法连接到服务器，请检查网络连接后重试。';
        } else if (error.message.includes('HTTP错误')) {
            errorTitle = '服务器错误';
        }
        
        showError(errorTitle, errorMessage);
    } finally {
        isAnalyzing = false;
        // 重置文件输入
        if (elements.fileInput) {
            elements.fileInput.value = '';
        }
    }
}

// ====== UI 更新函数 ======

// 服务器文件显示功能已删除

// 服务器文件错误显示功能已删除

// 服务器文件选择功能已删除

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

/**
 * 安全存储分析数据到sessionStorage
 * @param {Object} data - 要存储的分析数据
 * @returns {boolean} - 存储是否成功
 */
function safeStoreAnalysisData(data) {
    try {
        const dataString = JSON.stringify(data);
        const dataSizeKB = new Blob([dataString]).size / 1024;
        
        // 检查数据大小（sessionStorage通常限制为5-10MB）
        const maxSizeKB = 4 * 1024; // 4MB安全限制
        
        if (dataSizeKB > maxSizeKB) {
            console.warn(`数据过大 (${dataSizeKB.toFixed(2)}KB > ${maxSizeKB}KB)，尝试压缩数据`);
            
            // 尝试压缩数据：移除可视化图表的base64数据，只保留元数据
            const compressedData = compressAnalysisData(data);
            const compressedString = JSON.stringify(compressedData);
            const compressedSizeKB = new Blob([compressedString]).size / 1024;
            
            if (compressedSizeKB > maxSizeKB) {
                console.error(`压缩后数据仍然过大 (${compressedSizeKB.toFixed(2)}KB > ${maxSizeKB}KB)`);
                return false;
            }
            
            sessionStorage.setItem('analysisData', compressedString);
            console.info(`数据已压缩存储 (${compressedSizeKB.toFixed(2)}KB)`);
        } else {
            sessionStorage.setItem('analysisData', dataString);
            console.info(`数据已存储 (${dataSizeKB.toFixed(2)}KB)`);
        }
        
        return true;
    } catch (error) {
        console.error('存储分析数据失败:', error);
        
        // 如果是配额超限错误，尝试清理旧数据后重试
        if (error.name === 'QuotaExceededError') {
            try {
                // 清理可能的旧数据
                sessionStorage.removeItem('analysisData');
                sessionStorage.removeItem('analysisError');
                
                // 重试存储压缩数据
                const compressedData = compressAnalysisData(data);
                sessionStorage.setItem('analysisData', JSON.stringify(compressedData));
                console.info('清理旧数据后重新存储成功');
                return true;
            } catch (retryError) {
                console.error('重试存储失败:', retryError);
                return false;
            }
        }
        
        return false;
    }
}

/**
 * 压缩分析数据，移除大型可视化数据
 * @param {Object} data - 原始分析数据
 * @returns {Object} - 压缩后的数据
 */
function compressAnalysisData(data) {
    const compressed = JSON.parse(JSON.stringify(data)); // 深拷贝
    
    // 如果有可视化数据，移除base64图片数据，只保留元数据
    if (compressed.data && compressed.data.visualizations) {
        const viz = compressed.data.visualizations;
        
        // 处理各种图表类型
        ['time_series', 'correlation_heatmap', 'distribution_plots', 'box_plots'].forEach(chartType => {
            if (viz[chartType] && viz[chartType].image) {
                // 保留图表元数据，移除base64数据
                viz[chartType] = {
                    ...viz[chartType],
                    image: null, // 移除图片数据
                    compressed: true, // 标记为已压缩
                    original_size: viz[chartType].image ? viz[chartType].image.length : 0
                };
            }
        });
    }
    
    // 标记数据已被压缩
    compressed.compressed = true;
    compressed.compression_info = {
        timestamp: new Date().toISOString(),
        removed_visualizations: true
    };
    
    return compressed;
}

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
    // 服务器文件加载已删除
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

// ====== 核心功能函数 ======

// 视图切换函数
function switchView(view) {
    currentView = view;
    
    // 更新导航状态 - 移除所有active类
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 为当前视图的导航按钮添加active类
    const activeNavItem = document.querySelector(`[data-view="${view}"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }
    
    // 隐藏所有视图
    elements.uploadView?.style.setProperty('display', 'none');
    elements.historyView?.style.setProperty('display', 'none');
    elements.searchView?.style.setProperty('display', 'none');
    
    // 显示对应视图
    switch(view) {
        case 'upload':
            elements.uploadView?.style.setProperty('display', 'block');
            // 加载首页数据
            loadHomepageData();
            break;
        case 'history':
            elements.historyView?.style.setProperty('display', 'block');
            // 加载历史记录数据
            loadFileHistory();
            break;
        case 'search':
            elements.searchView?.style.setProperty('display', 'block');
            break;
    }
}

// 历史记录管理
let historyOffset = 0;
const historyLimit = 20;

// 加载文件历史记录
async function loadFileHistory(reset = false) {
    if (reset) {
        historyOffset = 0;
        if (elements.historyList) {
            elements.historyList.innerHTML = '';
        }
    }
    
    try {
        // 显示加载状态
        showHistoryLoading();
        
        const response = await fetch(`/api/files/history?offset=${historyOffset}&limit=${historyLimit}`);
        const data = await response.json();
        
        if (data.success && data.data && data.data.files && Array.isArray(data.data.files)) {
            renderHistoryList(data.data.files, reset);
            historyOffset += data.data.files.length;
            
            // 更新加载更多按钮状态
            if (elements.loadMoreBtn) {
                elements.loadMoreBtn.style.display = data.data.has_more ? 'block' : 'none';
            }
        } else {
            // 如果没有 files 数组或数据格式不正确，显示空状态
            if (reset && elements.historyList) {
                elements.historyList.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-history"></i>
                        <p>暂无历史记录</p>
                        <p class="history-tip">上传并分析文件后，记录将显示在这里</p>
                    </div>
                `;
            }
            if (elements.loadMoreBtn) {
                elements.loadMoreBtn.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error loading file history:', error);
        showHistoryError(error.message);
    }
    // 注意：这里不再需要在finally块中隐藏加载状态，因为renderHistoryList或showHistoryError会处理这个
}

// 显示历史记录加载状态
function showHistoryLoading() {
    if (elements.historyList) {
        elements.historyList.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>正在加载历史记录...</p>
            </div>
        `;
    }
}

// 显示历史记录错误
function showHistoryError(message) {
    if (elements.historyList) {
        elements.historyList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>加载失败: ${message}</p>
                <button class="btn btn-primary" onclick="loadFileHistory(true)">
                    <i class="fas fa-redo"></i> 重试
                </button>
            </div>
        `;
    }
}

// 渲染历史记录列表
function renderHistoryList(files, reset = false) {
    if (!elements.historyList) return;
    
    // 如果是重置操作或者第一次加载，清空所有内容（包括加载状态）
    if (reset || historyOffset === 0) {
        elements.historyList.innerHTML = '';
    }
    
    if (files.length === 0 && (reset || historyOffset === 0)) {
        elements.historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <p>暂无历史记录</p>
                <p class="history-tip">上传并分析文件后，记录将显示在这里</p>
            </div>
        `;
        return;
    }
    
    const historyItems = files.map(file => {
        const date = formatDate(file.created_at);
        const fileSize = formatFileSize(file.file_size);
        
        return `
            <div class="history-item" data-id="${file.id}">
                <div class="history-header">
                    <h4>${file.filename}</h4>
                    <span class="history-date">${date}</span>
                </div>
                <div class="history-content">
                    <div class="history-meta">
                        <span><i class="fas fa-database"></i> ${fileSize}</span>
                        <span><i class="fas fa-table"></i> ${file.rows?.toLocaleString()} 行</span>
                        <span><i class="fas fa-columns"></i> ${file.columns?.toLocaleString()} 列</span>
                    </div>
                    <div class="history-summary">
                        <p>${file.summary || '数据分析完成'}</p>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-primary btn-sm" onclick="viewHistoryResult('${file.id}')">
                        <i class="fas fa-eye"></i> 查看结果
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteHistoryItem('${file.id}')">
                        <i class="fas fa-trash"></i> 删除
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    // 如果是第一次加载或重置，直接设置innerHTML；否则追加内容
    if (reset || historyOffset === files.length) {
        elements.historyList.innerHTML = historyItems;
    } else {
        elements.historyList.insertAdjacentHTML('beforeend', historyItems);
    }
}

// 加载更多历史记录
async function loadMoreHistory() {
    await loadFileHistory(false);
}

// 查看历史记录结果
async function viewHistoryResult(historyId) {
    try {
        const response = await fetch(`/api/history/${historyId}`);
        const data = await response.json();
        
        if (data.success) {
            // 安全存储历史数据到sessionStorage并打开分析页面
            if (safeStoreAnalysisData(data)) {
                const analysisWindow = window.open('/analysis', '_blank');
                if (!analysisWindow) {
                    window.location.href = '/analysis';
                }
            } else {
                showError('数据存储失败', '历史记录数据过大，无法在浏览器中存储。');
            }
        } else {
            throw new Error(data.error?.message || '获取历史记录失败');
        }
    } catch (error) {
        console.error('Error viewing history result:', error);
        showError('查看失败', error.message);
    }
}

// 查看分析结果
async function viewAnalysisResult(analysisId) {
    try {
        const response = await fetch(`/api/analysis/${analysisId}`);
        const data = await response.json();
        
        if (data.success) {
            // 安全存储分析数据到sessionStorage并打开分析页面
            if (safeStoreAnalysisData(data)) {
                const analysisWindow = window.open('/analysis', '_blank');
                if (!analysisWindow) {
                    window.location.href = '/analysis';
                }
            } else {
                showError('数据存储失败', '分析结果数据过大，无法在浏览器中存储。');
            }
        } else {
            throw new Error(data.message || '获取分析结果失败');
        }
    } catch (error) {
        console.error('Error viewing analysis result:', error);
        showMessage('查看分析结果失败: ' + error.message, 'error');
    }
}

// 服务器文件分析功能已删除

// 删除历史记录项
async function deleteHistoryItem(historyId) {
    showModal(
        '确认删除',
        '确定要删除这条分析记录吗？此操作不可撤销。',
        async () => {
            try {
                const response = await fetch(`/api/history/${historyId}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (data.success) {
                    // 从DOM中移除该项
                    const historyItem = document.querySelector(`[data-id="${historyId}"]`);
                    if (historyItem) {
                        historyItem.remove();
                    }
                    
                    // 如果列表为空，重新加载
                    if (elements.historyList.children.length === 0) {
                        loadFileHistory(true);
                    }
                } else {
                    throw new Error(data.error?.message || '删除失败');
                }
            } catch (error) {
                console.error('Error deleting history item:', error);
                showError('删除失败', error.message);
            }
        }
    );
}

// 搜索功能
async function performSearch() {
    const query = elements.searchInput?.value?.trim();
    if (!query) {
        showError('搜索错误', '请输入搜索关键词');
        return;
    }
    
    try {
        elements.searchBtn.disabled = true;
        elements.searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 搜索中...';
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displaySearchResults(data.results);
        } else {
            throw new Error(data.error?.message || '搜索失败');
        }
    } catch (error) {
        console.error('Error performing search:', error);
        showError('搜索失败', error.message);
    } finally {
        elements.searchBtn.disabled = false;
        elements.searchBtn.innerHTML = '<i class="fas fa-search"></i> 搜索';
    }
}

// 显示搜索结果
function displaySearchResults(results) {
    if (!elements.searchResults) return;
    
    if (results.length === 0) {
        elements.searchResults.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>未找到相关结果</p>
                <p class="search-tip">尝试使用不同的关键词或检查拼写</p>
            </div>
        `;
        return;
    }
    
    const resultItems = results.map(result => {
        const date = formatDate(result.created_at);
        const relevance = Math.round(result.relevance * 100);
        
        return `
            <div class="search-result-item" data-id="${result.id}">
                <div class="result-header">
                    <h4>${result.filename}</h4>
                    <span class="relevance-score">${relevance}% 匹配</span>
                </div>
                <div class="result-content">
                    <p class="result-snippet">${result.snippet}</p>
                    <div class="result-meta">
                        <span><i class="fas fa-clock"></i> ${date}</span>
                        <span><i class="fas fa-database"></i> ${formatFileSize(result.file_size)}</span>
                        <span><i class="fas fa-table"></i> ${result.rows?.toLocaleString()} 行</span>
                    </div>
                </div>
                <div class="result-actions">
                    <button class="btn btn-primary btn-sm" onclick="viewSearchResult('${result.id}')">
                        <i class="fas fa-eye"></i> 查看详情
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="analyzeSearchResult('${result.filename}')">
                        <i class="fas fa-play"></i> 重新分析
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    elements.searchResults.innerHTML = resultItems;
}

// 查看搜索结果
async function viewSearchResult(resultId) {
    // 与查看历史记录结果相同的逻辑
    await viewHistoryResult(resultId);
}

// 搜索结果文件分析功能已删除

// 服务器文件加载功能已删除

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
                height: 400,  // 调整为适配2列布局的尺寸
                width: 600,   // 调整为适配2列布局的尺寸
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
        width: 800,   // 调整为适配2列布局的尺寸
        height: 500,  // 调整为适配2列布局的尺寸
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

// ====== 首页数据加载功能 ======

// 加载首页数据
function loadHomepageData() {
    loadRecentAnalyses();
    loadSystemStats();
}

// 加载最近分析记录
async function loadRecentAnalyses() {
    const recentList = document.getElementById('recent-analyses-list');
    if (!recentList) return;
    
    try {
        const response = await fetch('/api/files/history?limit=3');
        const data = await response.json();
        
        if (data.success && data.data && data.data.files && data.data.files.length > 0) {
            const recentItems = data.data.files.map(file => {
                const date = formatDate(file.created_at);
                const fileSize = formatFileSize(file.file_size);
                
                return `
                    <div class="recent-item" onclick="viewHistoryResult('${file.id}')">
                        <div class="recent-header">
                            <div class="recent-title">${file.filename}</div>
                            <div class="recent-time">${date}</div>
                        </div>
                        <div class="recent-meta">
                            <span><i class="fas fa-database"></i> ${fileSize}</span>
                            <span><i class="fas fa-table"></i> ${file.rows || 0} 行</span>
                            <span><i class="fas fa-columns"></i> ${file.columns || 0} 列</span>
                        </div>
                    </div>
                `;
            }).join('');
            
            recentList.innerHTML = recentItems;
        } else {
            recentList.innerHTML = `
                <div class="empty-state" style="padding: 20px;">
                    <i class="fas fa-history"></i>
                    <p>暂无分析记录</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading recent analyses:', error);
        recentList.innerHTML = `
            <div class="error-state" style="padding: 20px;">
                <i class="fas fa-exclamation-triangle"></i>
                <p>加载失败</p>
            </div>
        `;
    }
}

// 加载系统统计信息
async function loadSystemStats() {
    try {
        // 模拟系统统计数据 - 在实际项目中应该从API获取
        const response = await fetch('/api/files/history?limit=1000'); // 获取更多数据进行统计
        const data = await response.json();
        
        if (data.success && data.data) {
            const files = data.data.files || [];
            
            // 统计已分析文件数量
            const totalFiles = files.length;
            document.getElementById('total-files').textContent = totalFiles;
            
            // 分析次数（假设每个文件分析一次）
            document.getElementById('total-analyses').textContent = totalFiles;
            
            // 计算总数据量
            const totalSize = files.reduce((sum, file) => sum + (file.file_size || 0), 0);
            document.getElementById('data-processed').textContent = formatFileSize(totalSize);
            
            // 平均处理时间（模拟数据）
            document.getElementById('avg-processing-time').textContent = '2.3s';
        } else {
            // 设置默认值
            document.getElementById('total-files').textContent = '0';
            document.getElementById('total-analyses').textContent = '0';
            document.getElementById('data-processed').textContent = '0 B';
            document.getElementById('avg-processing-time').textContent = '-';
        }
    } catch (error) {
        console.error('Error loading system stats:', error);
        // 设置错误状态的默认值
        document.getElementById('total-files').textContent = '-';
        document.getElementById('total-analyses').textContent = '-';
        document.getElementById('data-processed').textContent = '-';
        document.getElementById('avg-processing-time').textContent = '-';
    }
}