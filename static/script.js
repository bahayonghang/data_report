// 数据报告应用的前端JavaScript代码

// 全局变量
let currentView = 'upload'; // 当前视图：upload, history, search
let historyData = []; // 历史记录数据
let currentPage = 1; // 当前页码
let hasMoreHistory = true; // 是否还有更多历史记录

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 绑定导航事件
    bindNavigationEvents();
    
    // 绑定历史记录事件
    bindHistoryEvents();
    
    // 绑定搜索事件
    bindSearchEvents();
    
    // 显示默认视图
    showView('upload');
}

/**
 * 绑定导航事件
 */
function bindNavigationEvents() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const view = this.getAttribute('data-view');
            showView(view);
        });
    });
}

/**
 * 显示指定视图
 * @param {string} view - 视图名称：upload, history, search
 */
function showView(view) {
    // 更新导航状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
    
    // 隐藏所有视图
    document.querySelectorAll('.view-container').forEach(container => {
        container.style.display = 'none';
    });
    
    // 显示目标视图
    const targetView = document.getElementById(`${view}-view`);
    if (targetView) {
        targetView.style.display = 'block';
    }
    
    currentView = view;
    
    // 根据视图执行特定操作
    switch(view) {
        case 'history':
            loadHistoryData();
            break;
        case 'search':
            focusSearchInput();
            break;
    }
}

/**
 * 绑定历史记录事件
 */
function bindHistoryEvents() {
    // 刷新按钮
    const refreshBtn = document.getElementById('refresh-history');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshHistoryData();
        });
    }
    
    // 筛选器
    const filterSelect = document.getElementById('history-filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            refreshHistoryData();
        });
    }
    
    // 加载更多按钮
    const loadMoreBtn = document.getElementById('load-more-history');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            loadMoreHistory();
        });
    }
}

/**
 * 绑定搜索事件
 */
function bindSearchEvents() {
    // 搜索表单
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch();
        });
    }
    
    // 搜索输入框回车事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch();
            }
        });
    }
}

/**
 * 加载历史记录数据
 */
async function loadHistoryData() {
    try {
        showHistoryLoading(true);
        
        const filter = document.getElementById('history-filter').value;
        const response = await fetch(`/api/files/history?page=1&limit=10&filter=${filter}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            historyData = data.data.files;
            currentPage = 1;
            hasMoreHistory = data.data.has_more;
            renderHistoryList();
        } else {
            showHistoryError('加载历史记录失败');
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
        showHistoryError('加载历史记录失败: ' + error.message);
    } finally {
        showHistoryLoading(false);
    }
}

/**
 * 刷新历史记录数据
 */
function refreshHistoryData() {
    historyData = [];
    currentPage = 1;
    hasMoreHistory = true;
    loadHistoryData();
}

/**
 * 加载更多历史记录
 */
async function loadMoreHistory() {
    if (!hasMoreHistory) return;
    
    try {
        const loadMoreBtn = document.getElementById('load-more-history');
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = '加载中...';
        
        const filter = document.getElementById('history-filter').value;
        const nextPage = currentPage + 1;
        const response = await fetch(`/api/files/history?page=${nextPage}&limit=10&filter=${filter}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            historyData = historyData.concat(data.data.files);
            currentPage = nextPage;
            hasMoreHistory = data.data.has_more;
            renderHistoryList();
        } else {
            throw new Error(data.error?.message || '加载失败');
        }
    } catch (error) {
        console.error('加载更多历史记录失败:', error);
        alert('加载更多历史记录失败: ' + error.message);
    } finally {
        const loadMoreBtn = document.getElementById('load-more-history');
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = '加载更多';
    }
}

/**
 * 渲染历史记录列表
 */
function renderHistoryList() {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;
    
    // 首先清空加载状态和所有现有内容
    historyList.innerHTML = '';
    
    if (historyData.length === 0) {
        historyList.innerHTML = '<div class="empty-state">暂无历史记录</div>';
        return;
    }
    
    const html = historyData.map(item => {
        const uploadTime = new Date(item.created_at).toLocaleString('zh-CN');
        const fileSize = formatFileSize(item.file_size);
        
        return `
            <div class="history-item" data-id="${item.id}">
                <div class="history-info">
                    <div class="history-header">
                        <h4>${item.filename}</h4>
                        <span class="status-badge status-success">${item.file_type.toUpperCase()}</span>
                    </div>
                    <div class="history-meta">
                        <span>上传时间: ${uploadTime}</span>
                        <span>文件大小: ${fileSize}</span>
                        <span>数据行数: ${item.rows || 'N/A'}</span>
                        <span>列数: ${item.columns || 'N/A'}</span>
                    </div>
                </div>
                <div class="history-actions">
                    <button class="btn btn-primary btn-sm" onclick="viewHistoryResult(${item.id})">
                        查看结果
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteHistoryItem(${item.id})">
                        删除
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    historyList.innerHTML = html;
    
    // 更新加载更多按钮状态
    const loadMoreBtn = document.getElementById('load-more-history');
    if (loadMoreBtn) {
        loadMoreBtn.style.display = hasMoreHistory ? 'block' : 'none';
    }
}

/**
 * 显示历史记录加载状态
 * @param {boolean} loading - 是否显示加载状态
 */
function showHistoryLoading(loading) {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;
    
    if (loading) {
        historyList.innerHTML = '<div class="loading-state">正在加载历史记录...</div>';
    }
    // 当loading为false时，不需要在这里清除内容
    // 内容的渲染由renderHistoryList()函数负责
}

/**
 * 显示历史记录错误状态
 * @param {string} message - 错误消息
 */
function showHistoryError(message) {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;
    
    historyList.innerHTML = `<div class="error-state">${message}</div>`;
}

/**
 * 查看历史记录结果
 * @param {number} historyId - 历史记录ID
 */
async function viewHistoryResult(historyId) {
    try {
        const response = await fetch(`/api/history/${historyId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 显示分析结果（这里可以复用现有的结果显示逻辑）
        displayAnalysisResult(result);
        
        // 切换到上传视图显示结果
        showView('upload');
        
    } catch (error) {
        console.error('查看历史记录结果失败:', error);
        alert('查看历史记录结果失败: ' + error.message);
    }
}

/**
 * 删除历史记录项
 * @param {number} historyId - 历史记录ID
 */
async function deleteHistoryItem(historyId) {
    if (!confirm('确定要删除这条历史记录吗？此操作不可撤销。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/history/${historyId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 从本地数据中移除
            historyData = historyData.filter(item => item.id !== historyId);
            renderHistoryList();
            alert('历史记录删除成功');
        } else {
            throw new Error(result.error?.message || '删除失败');
        }
        
    } catch (error) {
        console.error('删除历史记录失败:', error);
        alert('删除历史记录失败: ' + error.message);
    }
}

/**
 * 聚焦搜索输入框
 */
function focusSearchInput() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.focus();
    }
}

/**
 * 执行搜索
 */
async function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('请输入搜索关键词');
        return;
    }
    
    try {
        showSearchLoading(true);
        
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            renderSearchResults(data.results);
        } else {
            showSearchError(data.error?.message || '搜索失败');
        }
        
    } catch (error) {
        console.error('搜索失败:', error);
        showSearchError('搜索失败: ' + error.message);
    } finally {
        showSearchLoading(false);
    }
}

/**
 * 渲染搜索结果
 * @param {Array} results - 搜索结果数组
 */
function renderSearchResults(results) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="empty-state">未找到相关文件</div>';
        return;
    }
    
    const html = results.map(item => {
        const uploadTime = new Date(item.created_at).toLocaleString('zh-CN');
        const fileSize = formatFileSize(item.file_size);
        
        return `
            <div class="search-result-item" data-id="${item.id}">
                <div class="result-header">
                    <h4>${item.filename}</h4>
                    <span class="relevance-score">相关度: ${(item.relevance * 100).toFixed(0)}%</span>
                </div>
                <div class="result-content">
                    <div class="result-snippet">${item.snippet}</div>
                    <div class="result-meta">
                        <span class="status-badge status-success">${item.file_type.toUpperCase()}</span>
                        <span>上传时间: ${uploadTime}</span>
                        <span>文件大小: ${fileSize}</span>
                        <span>数据行数: ${item.rows || 'N/A'}</span>
                        <span>列数: ${item.columns || 'N/A'}</span>
                    </div>
                </div>
                <div class="result-actions">
                    <button class="btn btn-primary btn-sm" onclick="viewHistoryResult(${item.id})">
                        查看结果
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    searchResults.innerHTML = html;
}

/**
 * 显示搜索加载状态
 * @param {boolean} loading - 是否显示加载状态
 */
function showSearchLoading(loading) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    if (loading) {
        searchResults.innerHTML = '<div class="loading-state">搜索中...</div>';
    }
}

/**
 * 显示搜索错误状态
 * @param {string} message - 错误消息
 */
function showSearchError(message) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    searchResults.innerHTML = `<div class="error-state">${message}</div>`;
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * 显示分析结果（复用现有逻辑）
 * @param {Object} result - 分析结果对象
 */
function displayAnalysisResult(result) {
    // 这里应该复用现有的分析结果显示逻辑
    // 由于原有代码可能在其他地方，这里提供一个基础实现
    console.log('显示分析结果:', result);
    
    // 可以在这里添加具体的结果显示逻辑
    // 例如更新图表、统计信息等
}