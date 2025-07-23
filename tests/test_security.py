"""
安全模块单元测试
"""

import os
import tempfile
from pathlib import Path

from src.reporter.security import (
    validate_path,
    sanitize_filename,
    is_allowed_file_type,
    check_file_size,
    validate_file_operation,
)


class TestValidatePath:
    """路径验证测试"""

    def test_valid_path(self):
        """测试有效路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.csv"
            test_file.write_text("test")

            assert validate_path("test.csv", tmpdir) is True

    def test_path_traversal_attack(self):
        """测试路径遍历攻击"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert validate_path("../../../etc/passwd", tmpdir) is False

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert validate_path("nonexistent.csv", tmpdir) is False


class TestSanitizeFilename:
    """文件名清理测试"""

    def test_safe_filename(self):
        """测试安全文件名"""
        assert sanitize_filename("data.csv") == "data.csv"

    def test_dangerous_characters(self):
        """测试危险字符清理"""
        assert sanitize_filename("file<>.csv") == "file.csv"
        assert sanitize_filename("test.csv") == "test.csv"

    def test_empty_filename(self):
        """测试空文件名"""
        assert sanitize_filename("") == "uploaded_file"


class TestIsAllowedFileType:
    """文件类型检查测试"""

    def test_allowed_extensions(self):
        """测试允许的扩展名"""
        assert is_allowed_file_type("data.csv") is True
        assert is_allowed_file_type("data.CSV") is True
        assert is_allowed_file_type("data.parquet") is True

    def test_disallowed_extensions(self):
        """测试不允许的扩展名"""
        assert is_allowed_file_type("data.txt") is False
        assert is_allowed_file_type("data.json") is False


class TestCheckFileSize:
    """文件大小检查测试"""

    def test_small_file(self):
        """测试小文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp:
            tmp.write("small file")
            tmp.flush()

            assert check_file_size(tmp.name) is True

        os.unlink(tmp.name)

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        assert check_file_size("/nonexistent/file.csv") is False


class TestValidateFileOperation:
    """文件操作综合验证测试"""

    def test_valid_operation(self):
        """测试有效文件操作"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.csv"
            test_file.write_text("test data")

            is_valid, error_msg = validate_file_operation("test.csv", tmpdir)
            assert is_valid is True
            assert error_msg == ""
