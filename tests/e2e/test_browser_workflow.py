"""
浏览器端端到端测试
测试完整的用户交互流程
"""

import pytest
import tempfile
import json
import csv
import io
from pathlib import Path
from datetime import datetime, timedelta
from playwright.sync_api import Page, expect, BrowserContext


class TestBrowserWorkflow:
    """浏览器端用户工作流测试"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """设置测试环境"""
        self.page = page
        self.page.set_default_timeout(10000)

    def test_homepage_loads(self):
        """测试主页加载"""
        self.page.goto("http://localhost:8000")
        
        # 验证页面标题
        expect(self.page).to_have_title("数据报告分析工具")
        
        # 验证关键元素存在
        expect(self.page.locator("h1")).to_contain_text("数据报告分析工具")
        expect(self.page.locator("#file-selector")).to_be_visible()
        expect(self.page.locator("#upload-section")).to_be_visible()
        expect(self.page.locator("#results-container")).to_be_hidden()

    def test_file_upload_workflow(self):
        """测试文件上传工作流"""
        self.page.goto("http://localhost:8000")
        
        # 创建测试数据
        test_data = [
            ["DateTime", "value1", "value2"],
            ["2024-01-01 10:00:00", "1.5", "2.5"],
            ["2024-01-01 11:00:00", "2.0", "3.0"],
            ["2024-01-01 12:00:00", "1.8", "2.8"],
        ]
        
        csv_content = "\n".join([",".join(row) for row in test_data])
        
        # 上传文件
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "test_data.csv",
            "mimeType": "text/csv",
            "buffer": csv_content.encode()
        })
        
        # 等待分析完成
        expect(self.page.locator("#loading")).to_be_hidden(timeout=30000)
        
        # 验证结果显示
        expect(self.page.locator("#results-container")).to_be_visible()
        expect(self.page.locator("#file-summary")).to_contain_text("test_data.csv")
        expect(self.page.locator("#stats-table")).to_be_visible()

    def test_server_file_analysis(self):
        """测试服务器文件分析"""
        self.page.goto("http://localhost:8000")
        
        # 等待文件列表加载
        expect(self.page.locator("#file-list")).to_be_visible()
        
        # 如果有文件，测试分析功能
        file_items = self.page.locator(".file-item")
        if file_items.count() > 0:
            first_file = file_items.first
            file_name = first_file.locator(".file-name").text_content()
            
            # 点击分析按钮
            first_file.locator(".analyze-btn").click()
            
            # 等待分析完成
            expect(self.page.locator("#loading")).to_be_hidden(timeout=30000)
            
            # 验证结果显示
            expect(self.page.locator("#results-container")).to_be_visible()
            expect(self.page.locator("#file-summary")).to_contain_text(file_name)

    def test_chart_interactions(self):
        """测试图表交互功能"""
        self.page.goto("http://localhost:8000")
        
        # 上传测试数据
        test_data = [
            ["DateTime", "temperature", "humidity"],
            ["2024-01-01 10:00:00", "20.5", "65.2"],
            ["2024-01-01 11:00:00", "21.0", "66.0"],
            ["2024-01-01 12:00:00", "22.5", "64.8"],
        ]
        
        csv_content = "\n".join([",".join(row) for row in test_data])
        
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "temp_data.csv",
            "mimeType": "text/csv",
            "buffer": csv_content.encode()
        })
        
        # 等待分析完成
        expect(self.page.locator("#loading")).to_be_hidden(timeout=30000)
        
        # 验证图表存在
        expect(self.page.locator(".plotly-graph-div")).to_have_count(4, timeout=5000)
        
        # 测试图表交互
        charts = self.page.locator(".plotly-graph-div")
        for chart in charts.all():
            chart.hover()
            chart.click()

    def test_error_handling_display(self):
        """测试错误处理和显示"""
        self.page.goto("http://localhost:8000")
        
        # 测试无效文件上传
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "invalid.txt",
            "mimeType": "text/plain",
            "buffer": b"This is not a valid CSV file"
        })
        
        # 验证错误消息显示
        expect(self.page.locator(".error-message")).to_be_visible(timeout=5000)
        expect(self.page.locator(".error-message")).to_contain_text("不支持")

    def test_responsive_design(self):
        """测试响应式设计"""
        # 测试桌面视图
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        self.page.goto("http://localhost:8000")
        
        # 验证布局
        sidebar = self.page.locator("#sidebar")
        expect(sidebar).to_be_visible()
        
        # 测试移动视图
        self.page.set_viewport_size({"width": 375, "height": 667})
        self.page.goto("http://localhost:8000")
        
        # 验证移动布局
        menu_button = self.page.locator(".mobile-menu-toggle")
        if menu_button.is_visible():
            menu_button.click()
            expect(self.page.locator("#sidebar")).to_be_visible()

    def test_data_refresh(self):
        """测试数据刷新功能"""
        self.page.goto("http://localhost:8000")
        
        # 初始加载文件列表
        expect(self.page.locator("#file-list")).to_be_visible()
        
        # 点击刷新按钮
        refresh_button = self.page.locator("#refresh-files")
        if refresh_button.is_visible():
            refresh_button.click()
            
            # 等待刷新完成
            expect(self.page.locator("#loading")).to_be_hidden()
            expect(self.page.locator("#file-list")).to_be_visible()

    def test_large_dataset_handling(self):
        """测试大数据集处理"""
        self.page.goto("http://localhost:8000")
        
        # 创建较大的测试数据集
        dates = [datetime.now() - timedelta(hours=i) for i in range(1000)]
        
        csv_content = "DateTime,value1,value2,value3\n"
        for i, date in enumerate(dates):
            csv_content += f"{date.isoformat()},{i},{i*2},{i*0.5}\n"
        
        # 上传大文件
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "large_data.csv",
            "mimeType": "text/csv",
            "buffer": csv_content.encode()
        })
        
        # 等待分析完成，应该有进度指示器
        expect(self.page.locator("#loading")).to_be_hidden(timeout=60000)
        
        # 验证结果显示
        expect(self.page.locator("#results-container")).to_be_visible()
        expect(self.page.locator("#file-summary")).to_contain_text("large_data.csv")

    def test_keyboard_navigation(self):
        """测试键盘导航"""
        self.page.goto("http://localhost:8000")
        
        # 测试Tab键导航
        self.page.keyboard.press("Tab")
        active_element = self.page.evaluate("document.activeElement.tagName")
        assert active_element in ["INPUT", "BUTTON"]

    def test_accessibility(self):
        """测试可访问性"""
        self.page.goto("http://localhost:8000")
        
        # 检查ARIA标签
        file_input = self.page.locator("input[type='file']")
        expect(file_input).to_have_attribute("aria-label", "选择文件")
        
        # 检查按钮文本
        analyze_buttons = self.page.locator("button:has-text('分析')")
        expect(analyze_buttons.first).to_be_visible()

    def test_multiple_file_analysis(self):
        """测试多文件分析"""
        self.page.goto("http://localhost:8000")
        
        # 创建多个测试文件
        file1_data = [
            ["DateTime", "temp"],
            ["2024-01-01 10:00:00", "20.5"],
            ["2024-01-01 11:00:00", "21.0"],
        ]
        
        file2_data = [
            ["DateTime", "humidity"],
            ["2024-01-01 10:00:00", "65.2"],
            ["2024-01-01 11:00:00", "66.0"],
        ]
        
        # 上传第一个文件
        csv_content1 = "\n".join([",".join(row) for row in file1_data])
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "temp.csv",
            "mimeType": "text/csv",
            "buffer": csv_content1.encode()
        })
        
        expect(self.page.locator("#results-container")).to_be_visible()
        
        # 上传第二个文件
        csv_content2 = "\n".join([",".join(row) for row in file2_data])
        file_input.set_input_files({
            "name": "humidity.csv",
            "mimeType": "text/csv",
            "buffer": csv_content2.encode()
        })
        
        expect(self.page.locator("#results-container")).to_be_visible()
        expect(self.page.locator("#file-summary")).to_contain_text("humidity.csv")


class TestPerformance:
    """性能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page

    def test_page_load_performance(self):
        """测试页面加载性能"""
        navigation_start = self.page.evaluate("performance.timing.navigationStart")
        
        self.page.goto("http://localhost:8000")
        
        load_end = self.page.evaluate("performance.timing.loadEventEnd")
        load_time = load_end - navigation_start
        
        # 页面加载时间应小于3秒
        assert load_time < 3000, f"页面加载时间过长: {load_time}ms"

    def test_chart_render_performance(self):
        """测试图表渲染性能"""
        self.page.goto("http://localhost:8000")
        
        # 上传测试数据
        test_data = [
            ["DateTime", "value1", "value2", "value3"],
            ["2024-01-01 10:00:00", "1.5", "2.5", "3.5"],
            ["2024-01-01 11:00:00", "2.0", "3.0", "4.0"],
            ["2024-01-01 12:00:00", "1.8", "2.8", "3.8"],
        ]
        
        csv_content = "\n".join([",".join(row) for row in test_data])
        
        file_input = self.page.locator("input[type='file']")
        file_input.set_input_files({
            "name": "perf_test.csv",
            "mimeType": "text/csv",
            "buffer": csv_content.encode()
        })
        
        # 测量图表渲染时间
        start_time = self.page.evaluate("performance.now()")
        
        # 等待图表渲染完成
        expect(self.page.locator(".plotly-graph-div")).to_have_count(4, timeout=10000)
        
        end_time = self.page.evaluate("performance.now()")
        render_time = end_time - start_time
        
        # 图表渲染时间应小于2秒
        assert render_time < 2000, f"图表渲染时间过长: {render_time}ms"