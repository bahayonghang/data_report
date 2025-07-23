"""
基础统计分析模块单元测试
"""

import pytest
import polars as pl
import numpy as np
from src.reporter.analysis.basic_stats import (
    calculate_descriptive_stats,
    analyze_missing_values,
    detect_outliers,
    calculate_correlation_matrix,
    get_data_summary
)


class TestCalculateDescriptiveStats:
    """描述性统计测试"""
    
    def test_normal_data(self):
        """测试正常数据"""
        df = pl.DataFrame({
            'values': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        stats = calculate_descriptive_stats(df, ['values'])
        
        assert 'values' in stats
        assert stats['values']['count'] == 10
        assert abs(stats['values']['mean'] - 5.5) < 0.01
        assert abs(stats['values']['median'] - 5.5) < 0.01
        assert abs(stats['values']['std'] - 3.03) < 0.1
        assert stats['values']['min'] == 1
        assert stats['values']['max'] == 10
    
    def test_with_nulls(self):
        """测试包含空值的数据"""
        df = pl.DataFrame({
            'values': [1, None, 3, None, 5]
        })
        
        stats = calculate_descriptive_stats(df, ['values'])
        
        assert stats['values']['count'] == 3
        assert abs(stats['values']['mean'] - 3.0) < 0.01
    
    def test_single_value(self):
        """测试单个值"""
        df = pl.DataFrame({
            'values': [42]
        })
        
        stats = calculate_descriptive_stats(df, ['values'])
        
        assert stats['values']['count'] == 1
        assert stats['values']['mean'] == 42
        assert stats['values']['std'] == 0
    
    def test_empty_column(self):
        """测试空列"""
        df = pl.DataFrame({
            'values': [None, None, None]
        })
        
        stats = calculate_descriptive_stats(df, ['values'])
        
        assert 'values' not in stats


class TestAnalyzeMissingValues:
    """缺失值分析测试"""
    
    def test_no_missing_values(self):
        """测试无缺失值"""
        df = pl.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4.0, 5.0, 6.0]
        })
        
        missing = analyze_missing_values(df)
        
        for col in ['col1', 'col2']:
            assert missing[col]['null_count'] == 0
            assert missing[col]['null_percentage'] == 0
    
    def test_with_missing_values(self):
        """测试有缺失值"""
        df = pl.DataFrame({
            'col1': [1, None, 3, None],
            'col2': [None, 2.0, None, 4.0]
        })
        
        missing = analyze_missing_values(df)
        
        assert missing['col1']['null_count'] == 2
        assert missing['col1']['null_percentage'] == 50
        assert missing['col2']['null_count'] == 2
        assert missing['col2']['null_percentage'] == 50
    
    def test_empty_dataframe(self):
        """测试空数据框"""
        df = pl.DataFrame()
        
        missing = analyze_missing_values(df)
        
        assert missing == {}


class TestDetectOutliers:
    """异常值检测测试"""
    
    def test_iqr_method(self):
        """测试IQR方法"""
        df = pl.DataFrame({
            'values': [1, 2, 3, 4, 5, 100]  # 100是异常值
        })
        
        outliers = detect_outliers(df, ['values'], method='iqr')
        
        assert outliers['values']['outlier_count'] == 1
        assert 100 in outliers['values']['outlier_values']
    
    def test_zscore_method(self):
        """测试Z-score方法"""
        df = pl.DataFrame({
            'values': [1, 2, 3, 4, 5, 100]  # 100是异常值
        })
        
        outliers = detect_outliers(df, ['values'], method='zscore')
        
        assert outliers['values']['outlier_count'] == 1
        assert 100 in outliers['values']['outlier_values']
    
    def test_no_outliers(self):
        """测试无异常值"""
        df = pl.DataFrame({
            'values': [1, 2, 3, 4, 5]
        })
        
        outliers = detect_outliers(df, ['values'])
        
        assert outliers['values']['outlier_count'] == 0
        assert len(outliers['values']['outlier_values']) == 0
    
    def test_with_nulls(self):
        """测试包含空值"""
        df = pl.DataFrame({
            'values': [1, 2, None, 4, 5, 100]
        })
        
        outliers = detect_outliers(df, ['values'])
        
        assert outliers['values']['outlier_count'] == 1
        assert 100 in outliers['values']['outlier_values']


class TestCalculateCorrelationMatrix:
    """相关系数矩阵测试"""
    
    def test_perfect_correlation(self):
        """测试完全相关"""
        df = pl.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [2, 4, 6, 8, 10]  # col1的2倍
        })
        
        corr = calculate_correlation_matrix(df, ['col1', 'col2'])
        
        assert abs(corr['matrix']['col1']['col2'] - 1.0) < 0.01
        assert abs(corr['matrix']['col2']['col1'] - 1.0) < 0.01
    
    def test_no_correlation(self):
        """测试无相关"""
        df = pl.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [5, 4, 3, 2, 1]  # 完全负相关
        })
        
        corr = calculate_correlation_matrix(df, ['col1', 'col2'])
        
        assert abs(corr['matrix']['col1']['col2'] + 1.0) < 0.01
    
    def test_single_column(self):
        """测试单列"""
        df = pl.DataFrame({
            'col1': [1, 2, 3, 4, 5]
        })
        
        corr = calculate_correlation_matrix(df, ['col1'])
        
        assert corr['shape'] == (0, 0)
    
    def test_empty_columns(self):
        """测试空列列表"""
        df = pl.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })
        
        corr = calculate_correlation_matrix(df, [])
        
        assert corr['shape'] == (0, 0)


class TestGetDataSummary:
    """数据摘要测试"""
    
    def test_numeric_data(self):
        """测试数值数据"""
        df = pl.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [1.1, 2.2, 3.3, 4.4, 5.5],
            'col3': ['a', 'b', 'c', 'd', 'e']  # 分类变量
        })
        
        summary = get_data_summary(df)
        
        assert summary['total_rows'] == 5
        assert summary['total_columns'] == 3
        assert summary['numeric_columns'] == 2
        assert summary['categorical_columns'] == 1
        assert 'descriptive_stats' in summary
        assert 'correlation_matrix' in summary
    
    def test_no_numeric_columns(self):
        """测试无数值列"""
        df = pl.DataFrame({
            'col1': ['a', 'b', 'c'],
            'col2': ['x', 'y', 'z']
        })
        
        summary = get_data_summary(df)
        
        assert summary['total_rows'] == 3
        assert summary['total_columns'] == 2
        assert summary['numeric_columns'] == 0
        assert summary['categorical_columns'] == 2
        assert 'descriptive_stats' not in summary
        assert 'correlation_matrix' not in summary


@pytest.fixture
def sample_dataframe():
    """创建测试数据框"""
    return pl.DataFrame({
        'temperature': [20.5, 21.0, 22.5, None, 20.0, 19.5, 100.0],  # 100是异常值
        'humidity': [65, 68, 70, 72, None, 75, 80],
        'pressure': [1013, 1015, 1012, 1014, 1013, None, 1011]
    })


class TestIntegration:
    """集成测试"""
    
    def test_full_analysis_pipeline(self, sample_dataframe):
        """测试完整分析流程"""
        numeric_columns = ['temperature', 'humidity', 'pressure']
        
        # 描述性统计
        desc_stats = calculate_descriptive_stats(sample_dataframe, numeric_columns)
        assert len(desc_stats) == 3
        
        # 缺失值分析
        missing = analyze_missing_values(sample_dataframe)
        assert missing['temperature']['null_count'] == 1
        assert missing['humidity']['null_count'] == 1
        
        # 异常值检测
        outliers = detect_outliers(sample_dataframe, numeric_columns)
        assert outliers['temperature']['outlier_count'] > 0
        
        # 相关系数矩阵
        corr_matrix = calculate_correlation_matrix(sample_dataframe, numeric_columns)
        assert corr_matrix['shape'] == (3, 3)
        
        # 数据摘要
        summary = get_data_summary(sample_dataframe)
        assert summary['total_rows'] == 7
        assert summary['total_columns'] == 3