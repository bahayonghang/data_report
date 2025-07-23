// 文档增强功能

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initCodeCopyButtons();
    initAPIExamples();
    initPerformanceMetrics();
    initTableEnhancements();
    initSearchEnhancements();
});

// 代码复制功能
function initCodeCopyButtons() {
    // 为所有代码块添加复制按钮，但排除Mermaid图表
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(function(codeBlock) {
        const pre = codeBlock.parentElement;
        if (pre.querySelector('.copy-button')) return; // 避免重复添加
        
        // 排除Mermaid代码块
        if (codeBlock.classList.contains('language-mermaid') || 
            pre.classList.contains('mermaid') ||
            codeBlock.textContent.trim().startsWith('graph') ||
            codeBlock.textContent.trim().startsWith('flowchart') ||
            codeBlock.textContent.trim().startsWith('sequenceDiagram')) {
            return;
        }
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '📋 复制';
        copyButton.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            background: #007bff;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        `;
        
        copyButton.addEventListener('click', function() {
            navigator.clipboard.writeText(codeBlock.textContent).then(function() {
                copyButton.innerHTML = '✅ 已复制';
                setTimeout(function() {
                    copyButton.innerHTML = '📋 复制';
                }, 2000);
            }).catch(function() {
                copyButton.innerHTML = '❌ 失败';
                setTimeout(function() {
                    copyButton.innerHTML = '📋 复制';
                }, 2000);
            });
        });
        
        copyButton.addEventListener('mouseenter', function() {
            copyButton.style.opacity = '1';
        });
        
        copyButton.addEventListener('mouseleave', function() {
            copyButton.style.opacity = '0.7';
        });
        
        pre.style.position = 'relative';
        pre.appendChild(copyButton);
    });
}

// API示例切换功能
function initAPIExamples() {
    // 查找所有API示例容器
    const apiExamples = document.querySelectorAll('.api-examples');
    
    apiExamples.forEach(function(container) {
        const tabs = container.querySelectorAll('.example-tab');
        const contents = container.querySelectorAll('.example-content');
        
        tabs.forEach(function(tab, index) {
            tab.addEventListener('click', function() {
                // 移除所有活动状态
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // 激活当前选项卡
                tab.classList.add('active');
                if (contents[index]) {
                    contents[index].classList.add('active');
                }
            });
        });
    });
}

// 性能指标动画
function initPerformanceMetrics() {
    const metrics = document.querySelectorAll('.performance-metric');
    
    // 创建Intersection Observer来检测元素是否进入视口
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                animateMetric(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    metrics.forEach(function(metric) {
        observer.observe(metric);
    });
}

function animateMetric(element) {
    const text = element.textContent;
    const match = text.match(/(\d+(?:\.\d+)?)/); // 匹配数字
    
    if (match) {
        const finalValue = parseFloat(match[1]);
        const unit = text.replace(match[0], '').trim();
        let currentValue = 0;
        const increment = finalValue / 50; // 50步动画
        
        const timer = setInterval(function() {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            
            element.textContent = currentValue.toFixed(1) + ' ' + unit;
        }, 20);
    }
}

// 表格增强功能
function initTableEnhancements() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(function(table) {
        // 添加响应式包装器
        if (!table.parentElement.classList.contains('table-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-wrapper';
            wrapper.style.cssText = 'overflow-x: auto; margin: 1rem 0;';
            
            table.parentElement.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
        
        // 添加排序功能（如果表格有数据）
        const headers = table.querySelectorAll('th');
        if (headers.length > 0) {
            headers.forEach(function(header, index) {
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
            });
        }
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isNumeric = rows.every(row => {
        const cell = row.cells[columnIndex];
        return cell && !isNaN(parseFloat(cell.textContent.trim()));
    });
    
    rows.sort(function(a, b) {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (isNumeric) {
            return parseFloat(aText) - parseFloat(bText);
        } else {
            return aText.localeCompare(bText);
        }
    });
    
    // 重新排列行
    rows.forEach(function(row) {
        tbody.appendChild(row);
    });
}

// 搜索增强功能
function initSearchEnhancements() {
    // 添加搜索快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl+K 或 Cmd+K 打开搜索
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.md-search__input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // ESC 关闭搜索
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('.md-search__input');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.blur();
            }
        }
    });
}

// 添加页面加载进度条
function showLoadingProgress() {
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: linear-gradient(90deg, #007bff, #28a745);
        z-index: 9999;
        transition: width 0.3s ease;
    `;
    
    document.body.appendChild(progressBar);
    
    let progress = 0;
    const timer = setInterval(function() {
        progress += Math.random() * 15;
        if (progress >= 90) {
            progress = 90;
            clearInterval(timer);
        }
        progressBar.style.width = progress + '%';
    }, 100);
    
    window.addEventListener('load', function() {
        clearInterval(timer);
        progressBar.style.width = '100%';
        setTimeout(function() {
            progressBar.remove();
        }, 500);
    });
}

// 添加返回顶部按钮
function addBackToTopButton() {
    const button = document.createElement('button');
    button.innerHTML = '↑';
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #007bff;
        color: white;
        border: none;
        font-size: 20px;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.3s, transform 0.3s;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    
    button.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    document.body.appendChild(button);
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            button.style.opacity = '1';
            button.style.transform = 'scale(1)';
        } else {
            button.style.opacity = '0';
            button.style.transform = 'scale(0.8)';
        }
    });
}

// 初始化页面增强功能
showLoadingProgress();
addBackToTopButton();

// 添加打印样式优化
function optimizePrintStyles() {
    const printStyles = document.createElement('style');
    printStyles.textContent = `
        @media print {
            .md-header, .md-tabs, .md-footer, .copy-button {
                display: none !important;
            }
            
            .md-content {
                margin: 0 !important;
                max-width: none !important;
            }
            
            pre {
                white-space: pre-wrap !important;
                word-break: break-word !important;
            }
            
            .md-typeset h1, .md-typeset h2 {
                page-break-after: avoid;
            }
            
            .md-typeset table {
                page-break-inside: avoid;
            }
        }
    `;
    document.head.appendChild(printStyles);
}

optimizePrintStyles();

// 控制台欢迎信息
console.log(`
%c数据分析报告系统文档
%c版本: 0.1.0
%c访问 https://github.com/your-username/data_report 了解更多
`,
'color: #007bff; font-size: 16px; font-weight: bold;',
'color: #28a745; font-size: 12px;',
'color: #6c757d; font-size: 12px;'
);