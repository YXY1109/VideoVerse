# VideoVerse 测试套件

完整的 pytest 单元测试和集成测试。

## 测试结构

```
tests/
├── __init__.py
├── conftest.py          # 共享 fixtures
├── test_config.py       # 配置管理测试
├── test_utils/          # 工具模块测试
│   ├── test_llm.py
│   ├── test_cache.py
│   ├── test_http.py
│   ├── test_decorators.py
│   ├── test_paths.py
│   └── test_common.py
├── test_tools/          # 工具模块测试
│   ├── test_prompts.py
│   └── test_spacy_utils.py
├── test_steps/          # 处理步骤测试
│   ├── test_step_01_download.py
│   ├── test_step_02_asr.py
│   └── ...
└── test_backends/       # 后端测试
    ├── test_asr_backends.py
    └── test_tts_backends.py
```

## 安装测试依赖

```bash
# 使用 uv
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定模块测试

```bash
# 配置模块
pytest tests/test_config.py

# Utils 模块
pytest tests/test_utils/

# 特定文件
pytest tests/test_utils/test_llm.py
```

### 运行带标记的测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"

# 跳过需要真实环境的测试
pytest -m "not integration"
```

### 运行异步测试

```bash
# pytest-asyncio 自动处理异步测试
pytest tests/test_utils/test_llm.py
```

### 并行运行测试

```bash
# 使用 pytest-xdist 并行运行
pytest -n auto
```

### 生成覆盖率报告

```bash
# 终端输出
pytest --cov=src --cov-report=term-missing

# HTML 报告
pytest --cov=src --cov-report=html

# 查看 HTML 报告
# Windows: start htmlcov/index.html
# Mac/Linux: open htmlcov/index.html
```

### 其他有用的选项

```bash
# 显示详细输出
pytest -v

# 显示失败的测试详情
pytest -vv

# 在第一个失败时停止
pytest -x

# 进入调试器
pytest --pdb

# 只运行上次失败的测试
pytest --lf

# 显示最慢的 10 个测试
pytest --durations=10
```

## Fixtures

### conftest.py 提供的共享 fixtures:

- `mock_settings`: 模拟配置对象
- `temp_env_vars`: 临时环境变量
- `temp_output_dir`: 临时输出目录
- `sample_video_path`: 示例视频路径
- `sample_audio_path`: 示例音频路径
- `sample_transcription_df`: 示例转录数据
- `sample_asr_result`: 示例 ASR 结果
- `mock_openai_client`: 模拟 OpenAI 客户端
- `mock_llm_response`: 模拟 LLM 响应
- `mock_cache_manager`: 模拟缓存管理器
- `mock_httpx_client`: 模拟 HTTP 客户端
- `async_runner`: 异步测试运行器

## 测试覆盖率目标

- **config 模块**: 100%
- **utils 模块**: 90%+
- **tools 模块**: 80%+
- **steps 模块**: 70%+
- **backends 模块**: 60%+ (接口层)

## 编写测试指南

### 单元测试示例

```python
import pytest

class TestMyFunction:
    """测试函数名称"""

    def test_basic_case(self):
        """测试基本场景"""
        from src.module import my_function
        result = my_function("input")
        assert result == "expected"

    @pytest.mark.parametrize("input,expected", [
        ("a", "A"),
        ("b", "B"),
    ])
    def test_parametrized(self, input, expected):
        """测试参数化"""
        from src.module import my_function
        assert my_function(input) == expected
```

### 异步测试示例

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    from src.module import async_function
    result = await async_function()
    assert result is not None
```

### 使用 Mock

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock():
    """测试使用 mock"""
    with patch('src.module.external_api', new=AsyncMock(return_value="mocked")):
        from src.module import my_function
        result = await my_function()
        assert result == "mocked"
```

### 使用 Fixtures

```python
@pytest.mark.asyncio
async def test_with_fixture(mock_settings):
    """测试使用 fixture"""
    assert mock_settings.openai_api_key == "test_api_key"
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 常见问题

### Q: 如何跳过需要真实 API Key 的测试?

A: 使用 `@pytest.mark.skip` 装饰器:

```python
@pytest.mark.skip(reason="需要真实的 API Key")
@pytest.mark.asyncio
async def test_real_api():
    pass
```

### Q: 如何测试需要长时间运行的函数?

A: 使用 `@pytest.mark.slow` 标记:

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_long_running():
    pass
```

然后运行时跳过: `pytest -m "not slow"`

### Q: 如何调试失败的测试?

A: 使用以下方法:

1. 显示详细输出: `pytest -vv`
2. 进入调试器: `pytest --pdb`
3. 只运行失败的测试: `pytest --lf`
4. 在第一个失败时停止: `pytest -x`
