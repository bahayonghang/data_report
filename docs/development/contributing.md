# 贡献指南

感谢您对数据分析报告系统的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试、问题报告和功能建议。

## 贡献方式

### 🐛 报告问题

如果您发现了bug或有功能建议，请：

1. 检查 [Issues](https://github.com/your-username/data_report/issues) 确保问题未被报告
2. 使用适当的问题模板创建新issue
3. 提供详细的描述和复现步骤
4. 包含相关的环境信息

### 💡 功能建议

我们欢迎新功能的建议：

1. 在Issues中创建功能请求
2. 详细描述功能的用途和价值
3. 提供可能的实现方案
4. 讨论功能的设计和影响

### 📝 改进文档

文档改进包括：

- 修复错别字和语法错误
- 添加缺失的文档
- 改进现有文档的清晰度
- 添加使用示例
- 翻译文档

### 🔧 代码贡献

代码贡献是最直接的贡献方式：

- 修复bug
- 实现新功能
- 性能优化
- 代码重构
- 添加测试

## 开发流程

### 1. 准备工作

#### Fork 项目

1. 访问 [项目主页](https://github.com/your-username/data_report)
2. 点击右上角的 "Fork" 按钮
3. 克隆您的fork到本地：

```bash
git clone https://github.com/YOUR_USERNAME/data_report.git
cd data_report
```

#### 设置上游仓库

```bash
git remote add upstream https://github.com/your-username/data_report.git
git remote -v
```

#### 设置开发环境

请参考 [开发环境设置](setup.md) 文档。

### 2. 创建分支

为每个功能或修复创建单独的分支：

```bash
# 同步最新代码
git checkout main
git pull upstream main

# 创建新分支
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/issue-number-description
```

#### 分支命名规范

- `feature/功能名称` - 新功能
- `fix/问题描述` - bug修复
- `docs/文档主题` - 文档更新
- `refactor/重构内容` - 代码重构
- `test/测试内容` - 测试相关
- `chore/维护内容` - 维护任务

### 3. 开发代码

#### 编码规范

我们遵循以下编码规范：

- **PEP 8**: Python代码风格指南
- **类型注解**: 使用类型提示提高代码可读性
- **文档字符串**: 为所有公共函数和类添加docstring
- **测试**: 为新功能编写测试

#### 代码质量检查

在提交前运行质量检查：

```bash
# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy src/

# 运行测试
uv run pytest

# 测试覆盖率
uv run pytest --cov=src --cov-report=term-missing
```

#### 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: bug修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `perf`: 性能优化
- `ci`: CI配置文件和脚本的变动

**示例**:

```bash
# 新功能
git commit -m "feat(analysis): add correlation analysis support"

# bug修复
git commit -m "fix(upload): handle large file upload timeout"

# 文档更新
git commit -m "docs(api): update endpoint documentation"

# 重大变更
git commit -m "feat!: change API response format

BREAKING CHANGE: API responses now use 'data' field instead of 'result'"
```

### 4. 测试

#### 编写测试

为新功能编写相应的测试：

```python
# tests/test_analysis.py
import pytest
from src.core.analysis import DataAnalyzer

class TestDataAnalyzer:
    """数据分析器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.analyzer = DataAnalyzer()
    
    def test_basic_statistics(self, sample_dataframe):
        """测试基本统计功能"""
        result = self.analyzer.calculate_basic_stats(sample_dataframe)
        
        assert "mean" in result
        assert "std" in result
        assert result["count"] == len(sample_dataframe)
    
    def test_empty_dataframe(self):
        """测试空数据框处理"""
        import pandas as pd
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="数据框不能为空"):
            self.analyzer.calculate_basic_stats(empty_df)
    
    @pytest.mark.parametrize("file_type", ["csv", "parquet"])
    def test_file_loading(self, file_type, tmp_path):
        """测试文件加载功能"""
        # 创建测试文件
        test_file = tmp_path / f"test.{file_type}"
        # ... 创建测试数据
        
        result = self.analyzer.load_file(str(test_file))
        assert not result.empty
```

#### 测试类型

1. **单元测试**: 测试单个函数或方法
2. **集成测试**: 测试组件间的交互
3. **端到端测试**: 测试完整的用户流程
4. **性能测试**: 测试性能和资源使用

#### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_analysis.py

# 运行特定测试
uv run pytest tests/test_analysis.py::TestDataAnalyzer::test_basic_statistics

# 并行运行测试
uv run pytest -n auto

# 生成HTML覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 5. 提交Pull Request

#### 准备PR

1. 确保所有测试通过
2. 更新相关文档
3. 添加变更日志条目（如果需要）
4. 推送分支到您的fork

```bash
git push origin feature/your-feature-name
```

#### 创建PR

1. 访问GitHub上的项目页面
2. 点击 "Compare & pull request"
3. 填写PR模板
4. 等待代码审查

#### PR模板

```markdown
## 变更描述

简要描述此PR的变更内容。

## 变更类型

- [ ] Bug修复
- [ ] 新功能
- [ ] 重大变更
- [ ] 文档更新
- [ ] 性能优化
- [ ] 代码重构

## 测试

- [ ] 添加了新的测试
- [ ] 所有测试通过
- [ ] 手动测试通过

## 检查清单

- [ ] 代码遵循项目规范
- [ ] 自我审查了代码
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 变更不会破坏现有功能

## 相关Issue

关闭 #issue_number

## 截图（如果适用）

添加截图来说明变更。

## 额外说明

添加任何其他相关信息。
```

## 代码审查

### 审查标准

代码审查将关注以下方面：

1. **功能正确性**: 代码是否实现了预期功能
2. **代码质量**: 代码是否清晰、可维护
3. **性能**: 是否有性能问题
4. **安全性**: 是否存在安全漏洞
5. **测试覆盖**: 是否有足够的测试
6. **文档**: 是否有适当的文档

### 审查流程

1. **自动检查**: CI/CD流水线自动运行测试和检查
2. **人工审查**: 维护者和贡献者进行代码审查
3. **讨论**: 在PR中讨论问题和改进建议
4. **修改**: 根据反馈修改代码
5. **合并**: 审查通过后合并到主分支

### 响应审查意见

- 及时回应审查意见
- 解释设计决策
- 根据建议修改代码
- 感谢审查者的时间和建议

## 发布流程

### 版本号规范

我们使用 [语义化版本](https://semver.org/) (SemVer)：

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的API变更
- `MINOR`: 向后兼容的功能新增
- `PATCH`: 向后兼容的问题修正

### 发布步骤

1. **准备发布**:
   ```bash
   # 更新版本号
   # 更新 CHANGELOG.md
   # 确保所有测试通过
   ```

2. **创建发布标签**:
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

3. **自动发布**: GitHub Actions自动构建和发布

## 社区准则

### 行为准则

我们致力于为每个人提供友好、安全和欢迎的环境。请遵循以下准则：

- **尊重**: 尊重不同的观点和经验
- **包容**: 欢迎所有背景的贡献者
- **建设性**: 提供建设性的反馈
- **专业**: 保持专业和礼貌的交流
- **学习**: 保持开放的学习态度

### 沟通渠道

- **GitHub Issues**: 问题报告和功能讨论
- **GitHub Discussions**: 一般讨论和问答
- **Pull Requests**: 代码审查和技术讨论
- **Email**: 私人或敏感问题

## 认可贡献者

我们重视每一个贡献，无论大小。贡献者将被添加到：

- `CONTRIBUTORS.md` 文件
- 项目README的贡献者部分
- 发布说明中的感谢部分

### 贡献类型

我们认可以下类型的贡献：

- 💻 代码
- 📖 文档
- 🐛 问题报告
- 💡 想法和建议
- 🤔 答疑解惑
- 📢 推广宣传
- 🎨 设计
- 🌍 翻译

## 开发资源

### 有用的链接

- [项目主页](https://github.com/your-username/data_report)
- [问题跟踪](https://github.com/your-username/data_report/issues)
- [项目看板](https://github.com/your-username/data_report/projects)
- [Wiki](https://github.com/your-username/data_report/wiki)
- [发布页面](https://github.com/your-username/data_report/releases)

### 学习资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Polars文档](https://pola-rs.github.io/polars/)
- [Plotly文档](https://plotly.com/python/)
- [Pytest文档](https://docs.pytest.org/)
- [Python类型提示](https://docs.python.org/3/library/typing.html)

### 开发工具

- [VS Code扩展推荐](.vscode/extensions.json)
- [Pre-commit配置](.pre-commit-config.yaml)
- [GitHub Actions工作流](.github/workflows/)

## 常见问题

### Q: 我是新手，可以贡献吗？

A: 当然可以！我们欢迎所有级别的贡献者。可以从以下开始：
- 修复文档中的错别字
- 添加测试用例
- 报告问题
- 回答其他人的问题

### Q: 如何选择要解决的问题？

A: 建议从以下标签的问题开始：
- `good first issue`: 适合新手的问题
- `help wanted`: 需要帮助的问题
- `documentation`: 文档相关问题
- `bug`: 简单的bug修复

### Q: 我的PR被拒绝了怎么办？

A: 不要气馁！这很正常。请：
- 仔细阅读反馈意见
- 询问不明白的地方
- 根据建议修改代码
- 重新提交

### Q: 如何保持fork同步？

A: 定期同步上游仓库：

```bash
git checkout main
git pull upstream main
git push origin main
```

### Q: 可以同时处理多个问题吗？

A: 建议一次专注于一个问题，特别是对于新贡献者。这样可以：
- 更好地专注于质量
- 更快地获得反馈
- 避免合并冲突

## 感谢

感谢您考虑为数据分析报告系统做出贡献！您的参与使这个项目变得更好。

如果您有任何问题或需要帮助，请随时通过GitHub Issues或其他沟通渠道联系我们。

---

**记住**: 每个专家都曾经是初学者。我们都在学习，一起成长！🚀