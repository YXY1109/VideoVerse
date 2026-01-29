# 流水线重构和测试实施计划

> **给 Claude 的提示：** 必需的子技能：使用 superpowers:executing-plans 来逐步实施这个计划。

**目标：** 使用基于插件的架构将 13 步视频处理流水线从 `temp/` 重构到 `core/`，实施全面的 pytest 测试套件，并优化最佳实践。

**架构：**
1. **插件系统**：为每个处理步骤创建 `PipelineStep` 基类
2. **上下文管理**：使用 `PipelineContext` 在步骤之间传递数据
3. **注册表模式**：使用 `StepRegistry` 进行步骤注册和依赖解析
4. **引擎**：使用 `PipelineEngine` 编排执行，自动处理依赖关系

**技术栈：**
- Python 3.10-3.12 配合 uv 包管理器
- pytest + pytest-asyncio + pytest-cov 用于测试
- pydantic-settings 用于配置管理
- 已有：WhisperX、Spacy、Demucs、OpenAI API

---

## 第一阶段：基础设施搭建

### 任务 1.1：创建 pytest 配置

**文件：**
- 创建：`pytest.ini`
- 创建：`tests/__init__.py`

**步骤 1：编写 pytest.ini 配置**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=core
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --asyncio-mode=auto

markers =
    unit: 单元测试
    integration: 集成测试
    slow: 需要模型或网络的慢速测试
    gpu: 需要 GPU 的测试
    llm: 需要 LLM API 的测试
    requires_download: 需要文件下载的测试

asyncio_mode = auto
```

**步骤 2：创建 tests/__init__.py**

```python
"""VideoVerse 核心模块测试套件。"""
```

**步骤 3：运行 pytest 验证配置**

```bash
cd /d/PycharmProjects/VideoVerse
pytest --version
```

预期结果：pytest 显示版本和已加载的配置

**步骤 4：提交**

```bash
git add pytest.ini tests/__init__.py
git commit -m "test: 添加 pytest 配置和测试目录结构"
```

---

### 任务 1.2：扩展模型路径配置

**文件：**
- 修改：`core/config.py`

**步骤 1：编写新配置选项的失败测试**

创建：`tests/unit/test_config.py`

```python
import os
import pytest
from pathlib import Path
from core.config import Settings, get_settings

def test_model_cache_dir_from_env(monkeypatch):
    """测试 MODEL_CACHE_DIR 可以从环境变量设置"""
    monkeypatch.setenv("MODEL_CACHE_DIR", "/custom/models")
    settings = Settings()
    assert settings.model_cache_dir == "/custom/models"

def test_default_output_dir():
    """测试默认输出目录"""
    settings = Settings()
    assert settings.output_dir == "output"

def test_output_dir_from_env(monkeypatch):
    """测试 OUTPUT_DIR 可以被覆盖"""
    monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
    settings = Settings()
    assert settings.output_dir == "/custom/output"

def test_disable_auto_download(monkeypatch):
    """测试 DISABLE_AUTO_DOWNLOAD 设置"""
    monkeypatch.setenv("DISABLE_AUTO_DOWNLOAD", "true")
    settings = Settings()
    assert settings.disable_auto_download is True
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_config.py -v
```

预期结果：FAIL - model_cache_dir 和其他属性尚不存在

**步骤 3：实现配置扩展**

修改：`core/config.py`

添加到 Settings 类：

```python
from typing import List

class Settings(BaseSettings):
    # ... 现有字段 ...

    # 路径配置
    output_dir: str = Field(default="output", alias="OUTPUT_DIR")
    model_cache_dir: str = Field(default="models", alias="MODEL_CACHE_DIR")
    temp_dir: str = Field(default="temp", alias="TEMP_DIR")

    # 下载行为
    disable_auto_download: bool = Field(default=False, alias="DISABLE_AUTO_DOWNLOAD")
    hf_endpoint: str = Field(default="https://hf-mirror.com", alias="HF_ENDPOINT")

    # 视频配置
    youtube_resolution: str = Field(default="1080", alias="YOUTUBE_RESOLUTION")
    allowed_video_formats: List[str] = Field(
        default=["mp4", "mkv", "webm", "avi"],
        alias="ALLOWED_VIDEO_FORMATS"
    )

    # 字幕配置
    burn_subtitles: bool = Field(default=True, alias="BURN_SUBTITLES")
    subtitle_max_length: int = Field(default=75, alias="SUBTITLE_MAX_LENGTH")

    # TTS 速度配置
    speed_factor_min: float = Field(default=0.8, alias="SPEED_FACTOR_MIN")
    speed_factor_accept: float = Field(default=1.0, alias="SPEED_FACTOR_ACCEPT")
    speed_factor_max: float = Field(default=1.2, alias="SPEED_FACTOR_MAX")

    # 模型路径
    whisper_model_dir: str = Field(default="", alias="WHISPER_MODEL_DIR")
    whisper_zh_model: str = Field(default="", alias="WHISPER_ZH_MODEL")
    wav2vec2_model: str = Field(default="", alias="WAV2VEC2_MODEL")
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_config.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/config.py tests/unit/test_config.py
git commit -m "feat(config): 添加模型路径和流水线配置"
```

---

### 任务 1.3：创建 PathManager

**文件：**
- 创建：`core/paths.py`
- 测试：`tests/unit/test_paths.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_paths.py`

```python
import pytest
from pathlib import Path
from core.paths import PathManager, paths

def test_path_manager_output_dir():
    """测试输出目录属性"""
    manager = PathManager()
    output_dir = manager.output_dir
    assert isinstance(output_dir, Path)
    assert str(output_dir).endswith("output")

def test_path_manager_models_dir():
    """测试模型目录使用配置"""
    manager = PathManager()
    models_dir = manager.models_dir
    assert isinstance(models_dir, Path)

def test_ensure_directories(tmp_path):
    """测试目录创建"""
    manager = PathManager(base_dir=tmp_path)
    manager.ensure_directories()
    assert (tmp_path / "output").exists()
    assert (tmp_path / "output" / "audio").exists()
    assert (tmp_path / "output" / "log").exists()

def test_global_paths_instance():
    """测试全局 paths 实例可用"""
    from core.paths import paths
    assert paths is not None
    assert hasattr(paths, 'output_dir')
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_paths.py -v
```

预期结果：FAIL - core/paths.py 不存在

**步骤 3：实现 PathManager**

创建：`core/paths.py`

```python
"""VideoVerse 流水线的路径管理。"""
from pathlib import Path
from typing import Optional
from core.config import get_settings

settings = get_settings()


class PathManager:
    """管理流水线的所有文件路径。"""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = base_dir or Path.cwd()
        self._output_dir = None

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def output_dir(self) -> Path:
        if self._output_dir is None:
            custom_path = settings.output_dir
            self._output_dir = Path(custom_path) if custom_path else self._base_dir / "output"
        return self._output_dir

    @property
    def models_dir(self) -> Path:
        return Path(settings.model_cache_dir)

    @property
    def temp_dir(self) -> Path:
        return Path(settings.temp_dir)

    @property
    def audio_dir(self) -> Path:
        return self.output_dir / "audio"

    @property
    def log_dir(self) -> Path:
        return self.output_dir / "log"

    @property
    def audio_refers_dir(self) -> Path:
        return self.audio_dir / "refers"

    @property
    def audio_segs_dir(self) -> Path:
        return self.audio_dir / "segs"

    @property
    def audio_tmp_dir(self) -> Path:
        return self.audio_dir / "tmp"

    # 输出文件
    @property
    def cleaned_chunks(self) -> Path:
        return self.log_dir / "cleaned_chunks.xlsx"

    @property
    def split_by_nlp(self) -> Path:
        return self.log_dir / "split_by_nlp.txt"

    @property
    def split_by_meaning(self) -> Path:
        return self.log_dir / "split_by_meaning.txt"

    @property
    def terminology(self) -> Path:
        return self.log_dir / "terminology.json"

    @property
    def translation_results(self) -> Path:
        return self.log_dir / "translation_results.xlsx"

    @property
    def raw_audio_file(self) -> Path:
        return self.audio_dir / "raw.mp3"

    @property
    def vocal_audio_file(self) -> Path:
        return self.audio_dir / "vocal.mp3"

    @property
    def output_video_with_sub(self) -> Path:
        return self.output_dir / "output_with_subtitles.mp4"

    @property
    def output_video_dubbed(self) -> Path:
        return self.output_dir / "output_dubbed.mp4"

    def ensure_directories(self) -> None:
        """创建所有必要的目录。"""
        dirs = [
            self.output_dir,
            self.audio_dir,
            self.log_dir,
            self.audio_refers_dir,
            self.audio_segs_dir,
            self.audio_tmp_dir,
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# 全局实例
paths = PathManager()
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_paths.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/paths.py tests/unit/test_paths.py
git commit -m "feat(paths): 添加 PathManager 用于集中路径管理"
```

---

### 任务 1.4：创建 conftest.py 共享 fixtures

**文件：**
- 创建：`tests/conftest.py`

**步骤 1：创建包含基本 fixtures 的 conftest.py**

```python
"""VideoVerse 测试的共享 pytest fixtures。"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from core.config import Settings
from core.pipeline.context import PipelineContext
from core.paths import PathManager


@pytest.fixture(scope="session")
def project_root() -> Path:
    """项目根目录。"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """测试数据目录。"""
    test_dir = project_root / "tests" / "fixtures"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def test_settings() -> Settings:
    """测试环境配置。"""
    return Settings(
        openai_api_key="test_key",
        openai_api_base="http://mock.openai.com/v1",
        openai_model="gpt-4o",
        model_cache_dir="tests/fixtures/models",
        output_dir="tests/fixtures/output",
        whisper_runtime="local",
        tts_method="edge",
        disable_auto_download=True,
    )


@pytest.fixture
def pipeline_context(test_settings: Settings) -> PipelineContext:
    """流水线执行上下文。"""
    # 在这里导入以避免循环依赖
    from core.pipeline.context import PipelineContext
    return PipelineContext(
        video_source="tests/fixtures/video/demo.mp4",
        source_language="zh",
        target_language="en",
        config=test_settings,
        storage={},
    )


@pytest.fixture
def mock_llm_client():
    """模拟 LLM 客户端。"""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="模拟响应"))]
        )
    )
    return mock
```

**步骤 2：运行 pytest 验证 fixtures 加载**

```bash
pytest --collect-only
```

预期结果：Fixtures 被收集，没有错误

**步骤 3：提交**

```bash
git add tests/conftest.py
git commit -m "test: 在 conftest.py 中添加共享 fixtures"
```

---

## 第二阶段：流水线引擎框架

### 任务 2.1：创建 PipelineContext

**文件：**
- 创建：`core/pipeline/__init__.py`
- 创建：`core/pipeline/context.py`
- 测试：`tests/unit/test_pipeline/test_context.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_pipeline/test_context.py`

```python
import pytest
from core.pipeline.context import PipelineContext
from core.config import Settings

def test_context_creation():
    """测试创建流水线上下文。"""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    assert context.video_source == "test.mp4"
    assert context.source_language == "zh"
    assert context.target_language == "en"
    assert context.storage == {}

def test_context_storage():
    """测试在上下文中存储和检索数据。"""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    context.storage["test_key"] = "test_value"
    assert context.storage["test_key"] == "test_value"
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_pipeline/test_context.py -v
```

预期结果：FAIL - core/pipeline/context.py 不存在

**步骤 3：实现 PipelineContext**

创建：`core/pipeline/__init__.py`

```python
"""VideoVerse 的流水线引擎。"""
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.pipeline.registry import StepRegistry
from core.pipeline.engine import PipelineEngine

__all__ = ["PipelineStep", "PipelineContext", "StepRegistry", "PipelineEngine"]
```

创建：`core/pipeline/context.py`

```python
"""在步骤之间传递数据的流水线上下文。"""
from dataclasses import dataclass, field
from typing import Any, Dict
from core.config import Settings


@dataclass
class PipelineContext:
    """在流水线步骤之间传递的上下文。"""

    video_source: str
    source_language: str
    target_language: str
    config: Settings
    storage: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """从存储中获取值。"""
        return self.storage.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """在存储中设置值。"""
        self.storage[key] = value

    def has(self, key: str) -> bool:
        """检查存储中是否存在键。"""
        return key in self.storage
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_pipeline/test_context.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/pipeline/ tests/unit/test_pipeline/test_context.py
git commit -m "feat(pipeline): 添加 PipelineContext 用于数据传递"
```

---

### 任务 2.2：创建 PipelineStep 基类

**文件：**
- 创建：`core/pipeline/base.py`
- 测试：`tests/unit/test_pipeline/test_base.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_pipeline/test_base.py`

```python
import pytest
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.config import Settings


class DummyStep(PipelineStep):
    """测试步骤实现。"""

    @property
    def name(self) -> str:
        return "dummy_step"

    async def execute(self, context: PipelineContext):
        return "executed"


@pytest.mark.asyncio
async def test_step_name():
    """测试步骤有名称。"""
    step = DummyStep()
    assert step.name == "dummy_step"


@pytest.mark.asyncio
async def test_step_execute(pipeline_context):
    """测试步骤执行。"""
    step = DummyStep()
    result = await step.execute(pipeline_context)
    assert result == "executed"


@pytest.mark.asyncio
async def test_step_dependencies_default():
    """测试默认依赖为空列表。"""
    step = DummyStep()
    assert step.dependencies == []


@pytest.mark.asyncio
async def test_step_validate_default(pipeline_context):
    """测试默认验证返回 True。"""
    step = DummyStep()
    assert await step.validate(pipeline_context) is True


class StepWithDeps(DummyStep):
    """有依赖的步骤。"""

    @property
    def dependencies(self):
        return ["step_01", "step_02"]


def test_step_with_dependencies():
    """测试步骤可以声明依赖。"""
    step = StepWithDeps()
    assert step.dependencies == ["step_01", "step_02"]
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_pipeline/test_base.py -v
```

预期结果：FAIL - PipelineStep 不存在

**步骤 3：实现 PipelineStep**

创建：`core/pipeline/base.py`

```python
"""流水线步骤的基类。"""
from abc import ABC, abstractmethod
from typing import Any, List
from core.pipeline.context import PipelineContext


class PipelineStep(ABC):
    """流水线步骤的抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """唯一的步骤名称。"""
        pass

    @property
    def dependencies(self) -> List[str]:
        """此步骤依赖的步骤名称列表。"""
        return []

    @abstractmethod
    async def execute(self, context: PipelineContext) -> Any:
        """执行步骤逻辑。"""
        pass

    async def validate(self, context: PipelineContext) -> bool:
        """在执行前验证前置条件。"""
        return True
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_pipeline/test_base.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/pipeline/base.py tests/unit/test_pipeline/test_base.py
git commit -m "feat(pipeline): 添加 PipelineStep 基类"
```

---

### 任务 2.3：创建 StepRegistry

**文件：**
- 创建：`core/pipeline/registry.py`
- 测试：`tests/unit/test_pipeline/test_registry.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_pipeline/test_registry.py`

```python
import pytest
from core.pipeline.registry import StepRegistry
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext


class TestStep1(PipelineStep):
    @property
    def name(self):
        return "step_01"

    async def execute(self, context):
        return "step1_result"


class TestStep2(PipelineStep):
    @property
    def name(self):
        return "step_02"

    @property
    def dependencies(self):
        return ["step_01"]

    async def execute(self, context):
        return "step2_result"


def test_register_step():
    """测试注册步骤。"""
    registry = StepRegistry()
    step = TestStep1()
    registry.register("step_01", step)
    assert "step_01" in registry.list_steps()


def test_get_step():
    """测试检索已注册的步骤。"""
    registry = StepRegistry()
    step = TestStep1()
    registry.register("step_01", step)
    retrieved = registry.get("step_01")
    assert retrieved is step


def test_get_nonexistent_step():
    """测试获取不存在的步骤引发错误。"""
    registry = StepRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_list_steps():
    """测试列出所有已注册的步骤。"""
    registry = StepRegistry()
    step1 = TestStep1()
    step2 = TestStep2()
    registry.register("step_01", step1)
    registry.register("step_02", step2)
    steps = registry.list_steps()
    assert set(steps) == {"step_01", "step_02"}


def test_resolve_execution_order():
    """测试基于依赖关系解析步骤执行顺序。"""
    registry = StepRegistry()
    step1 = TestStep1()
    step2 = TestStep2()
    registry.register("step_01", step1)
    registry.register("step_02", step2)

    order = registry.resolve_execution_order(["step_02"])
    assert order == ["step_01", "step_02"]


def test_resolve_circular_dependencies():
    """测试循环依赖检测。"""
    from core.pipeline.base import PipelineStep

    class CircularA(PipelineStep):
        @property
        def name(self):
            return "a"

        @property
        def dependencies(self):
            return ["b"]

        async def execute(self, context):
            pass

    class CircularB(PipelineStep):
        @property
        def name(self):
            return "b"

        @property
        def dependencies(self):
            return ["a"]

        async def execute(self, context):
            pass

    registry = StepRegistry()
    registry.register("a", CircularA())
    registry.register("b", CircularB())

    with pytest.raises(ValueError, match="circular"):
        registry.resolve_execution_order(["a", "b"])
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_pipeline/test_registry.py -v
```

预期结果：FAIL - StepRegistry 不存在

**步骤 3：实现 StepRegistry**

创建：`core/pipeline/registry.py`

```python
"""管理流水线步骤的注册表。"""
from typing import Dict, List, Set
from core.pipeline.base import PipelineStep


class StepRegistry:
    """具有依赖解析功能的流水线步骤注册表。"""

    def __init__(self):
        self._steps: Dict[str, PipelineStep] = {}

    def register(self, name: str, step: PipelineStep) -> None:
        """注册一个步骤。"""
        self._steps[name] = step

    def get(self, name: str) -> PipelineStep:
        """获取已注册的步骤。"""
        if name not in self._steps:
            raise KeyError(f"步骤 '{name}' 未注册")
        return self._steps[name]

    def list_steps(self) -> List[str]:
        """列出所有已注册的步骤名称。"""
        return list(self._steps.keys())

    def resolve_execution_order(self, step_names: List[str]) -> List[str]:
        """
        基于依赖关系解析执行顺序。

        使用拓扑排序来按依赖关系排序步骤。
        """
        # 构建依赖图
        graph: Dict[str, Set[str]] = {name: set() for name in step_names}
        in_degree: Dict[str, int] = {name: 0 for name in step_names}

        for name in step_names:
            step = self.get(name)
            for dep in step.dependencies:
                if dep in step_names:
                    graph[dep].add(name)
                    in_degree[name] += 1

        # 使用 DFS 检测循环
        visiting = set()
        visited = set()

        def has_cycle(node: str) -> bool:
            if node in visiting:
                return True  # 检测到循环
            if node in visited:
                return False
            visiting.add(node)
            for neighbor in graph.get(node, set()):
                if has_cycle(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for node in step_names:
            if has_cycle(node):
                raise ValueError(f"检测到涉及步骤 '{node}' 的循环依赖")

        # 拓扑排序（Kahn 算法）
        queue = [name for name in step_names if in_degree[name] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(step_names):
            raise ValueError("无法解析执行顺序 - 可能存在循环")

        return result
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_pipeline/test_registry.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/pipeline/registry.py tests/unit/test_pipeline/test_registry.py
git commit -m "feat(pipeline): 添加带依赖解析的 StepRegistry"
```

---

### 任务 2.4：创建 PipelineEngine

**文件：**
- 创建：`core/pipeline/engine.py`
- 测试：`tests/unit/test_pipeline/test_engine.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_pipeline/test_engine.py`

```python
import pytest
from core.pipeline.engine import PipelineEngine
from core.pipeline.registry import StepRegistry
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.config import Settings


class MockStep(PipelineStep):
    """用于测试的模拟步骤。"""

    def __init__(self, name, result=None):
        self._name = name
        self._result = result or f"{name}_result"
        self.executed = False

    @property
    def name(self):
        return self._name

    async def execute(self, context):
        self.executed = True
        context.set(self._name, self._result)
        return self._result


@pytest.mark.asyncio
async def test_engine_run_single_step(pipeline_context):
    """测试运行单个步骤。"""
    registry = StepRegistry()
    step = MockStep("test_step")
    registry.register("test_step", step)

    engine = PipelineEngine(registry)
    result = await engine.run_step("test_step", pipeline_context)

    assert result == "test_step_result"
    assert step.executed
    assert pipeline_context.get("test_step") == "test_step_result"


@pytest.mark.asyncio
async def test_engine_run_multiple_steps(pipeline_context):
    """测试按顺序运行多个步骤。"""
    registry = StepRegistry()
    step1 = MockStep("step_01", "result1")
    step2 = MockStep("step_02", "result2")
    registry.register("step_01", step1)
    registry.register("step_02", step2)

    engine = PipelineEngine(registry)
    result_context = await engine.run(
        steps=["step_01", "step_02"],
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
    )

    assert step1.executed
    assert step2.executed
    assert result_context.get("step_01") == "result1"
    assert result_context.get("step_02") == "result2"


@pytest.mark.asyncio
async def test_engine_respects_dependencies(pipeline_context):
    """测试引擎自动解析依赖关系。"""
    from core.pipeline.base import PipelineStep

    class StepWithDeps(PipelineStep):
        def __init__(self, name, deps):
            self._name = name
            self._deps = deps
            self.executed = False

        @property
        def name(self):
            return self._name

        @property
        def dependencies(self):
            return self._deps

        async def execute(self, context):
            self.executed = True
            context.set(self._name, f"{self._name}_done")

    registry = StepRegistry()
    step_c = StepWithDeps("step_c", ["step_b"])
    step_b = StepWithDeps("step_b", ["step_a"])
    step_a = StepWithDeps("step_a", [])

    registry.register("step_a", step_a)
    registry.register("step_b", step_b)
    registry.register("step_c", step_c)

    engine = PipelineEngine(registry)
    await engine.run(
        steps=["step_c"],
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
    )

    # 验证执行顺序
    assert step_a.executed
    assert step_b.executed
    assert step_c.executed


@pytest.mark.asyncio
async def test_engine_validation(pipeline_context):
    """测试执行前的步骤验证。"""
    from core.pipeline.base import PipelineStep

    class FailingValidationStep(PipelineStep):
        @property
        def name(self):
            return "failing_step"

        async def validate(self, context):
            return False

        async def execute(self, context):
            return "should_not_run"

    registry = StepRegistry()
    step = FailingValidationStep()
    registry.register("failing_step", step)

    engine = PipelineEngine(registry)

    with pytest.raises(ValueError, match="validation failed"):
        await engine.run_step("failing_step", pipeline_context)
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_pipeline/test_engine.py -v
```

预期结果：FAIL - PipelineEngine 不存在

**步骤 3：实现 PipelineEngine**

创建：`core/pipeline/engine.py`

```python
"""流水线执行引擎。"""
from typing import List, Optional
from loguru import logger
from core.pipeline.registry import StepRegistry
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.config import get_settings


class PipelineEngine:
    """编排流水线步骤的执行。"""

    def __init__(self, registry: StepRegistry):
        self.registry = registry

    async def run_step(
        self,
        step_name: str,
        context: PipelineContext,
    ) -> any:
        """运行单个步骤。"""
        step = self.registry.get(step_name)

        logger.info(f"验证步骤：{step_name}")
        if not await step.validate(context):
            raise ValueError(f"步骤 '{step_name}' 验证失败")

        logger.info(f"执行步骤：{step_name}")
        result = await step.execute(context)
        logger.info(f"完成步骤：{step_name}")

        return result

    async def run(
        self,
        steps: List[str],
        video_source: str,
        source_language: str,
        target_language: str,
        config: Optional[Settings] = None,
    ) -> PipelineContext:
        """
        按依赖解析的顺序运行多个步骤。

        参数：
            steps: 要运行的步骤名称列表
            video_source: 输入视频源
            source_language: 源语言代码
            target_language: 目标语言代码
            config: 可选设置（如未提供则使用默认值）

        返回：
            包含所有步骤结果的 PipelineContext
        """
        if config is None:
            config = get_settings()

        context = PipelineContext(
            video_source=video_source,
            source_language=source_language,
            target_language=target_language,
            config=config,
            storage={},
        )

        # 基于依赖关系解析执行顺序
        execution_order = self.registry.resolve_execution_order(steps)

        logger.info(f"执行顺序：{' -> '.join(execution_order)}")

        # 运行每个步骤
        for step_name in execution_order:
            await self.run_step(step_name, context)

        logger.info("流水线执行完成")
        return context
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_pipeline/test_engine.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/pipeline/engine.py tests/unit/test_pipeline/test_engine.py
git commit -m "feat(pipeline): 添加 PipelineEngine 用于编排步骤执行"
```

---

## 第三阶段：工具模块迁移

### 任务 3.1：迁移装饰器

**文件：**
- 创建：`core/utils/decorators.py`
- 测试：`tests/unit/test_decorators.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_decorators.py`

```python
import pytest
import asyncio
from pathlib import Path
from core.utils.decorators import async_except_handler, async_check_file_exists


@pytest.mark.asyncio
async def test_async_except_handler_success():
    """测试带异常处理器的成功执行。"""
    @async_except_handler("测试操作", max_retries=2)
    async def successful_operation():
        return "success"

    result = await successful_operation()
    assert result == "success"


@pytest.mark.asyncio
async def test_async_except_handler_retry():
    """测试失败时的重试。"""
    call_count = 0

    @async_except_handler("测试操作", max_retries=3)
    async def failing_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("临时失败")
        return "success"

    result = await failing_operation()
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_async_except_handler_max_retries():
    """测试超过最大重试次数。"""
    @async_except_handler("测试操作", max_retries=2)
    async def always_failing():
        raise ValueError("总是失败")

    with pytest.raises(ValueError, match="总是失败"):
        await always_failing()


@pytest.mark.asyncio
async def test_async_check_file_exists_skip(tmp_path):
    """测试文件存在时跳过。"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    executed = []

    @async_check_file_exists(str(test_file))
    async def create_file():
        executed.append(True)
        return "created"

    result = await create_file()
    assert result == str(test_file)
    assert len(executed) == 0  # 函数未执行


@pytest.mark.asyncio
async def test_async_check_file_exists_execute(tmp_path):
    """测试文件不存在时执行。"""
    test_file = tmp_path / "new_file.txt"

    executed = []

    @async_check_file_exists(str(test_file))
    async def create_file():
        executed.append(True)
        test_file.write_text("created")
        return str(test_file)

    result = await create_file()
    assert result == str(test_file)
    assert len(executed) == 1  # 函数已执行
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_decorators.py -v
```

预期结果：FAIL - core/utils/ 中的装饰器模块不存在

**步骤 3：迁移装饰器**

首先检查文件是否存在：

```bash
ls core/utils/decorators.py 2>/dev/null || echo "文件不存在"
```

如果存在，查看内容。如果不存在，从 temp 创建：

创建：`core/utils/decorators.py`

```python
"""流水线步骤的异步装饰器。"""
import asyncio
import functools
import os
from pathlib import Path
from typing import Callable, TypeVar, Union
from loguru import logger

T = TypeVar("T")


def async_except_handler(message: str = "操作失败", max_retries: int = 5):
    """
    带指数退避重试的异步异常处理器装饰器。

    参数：
        message: 错误消息前缀
        max_retries: 最大重试次数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"{message}（尝试 {attempt + 1}/{max_retries}）：{e}。"
                            f"{wait_time}秒后重试..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{message} 在 {max_retries} 次尝试后：{e}")
            raise last_error
        return wrapper
    return decorator


def async_check_file_exists(output_path: Union[str, Path, Callable[..., Union[str, Path]]]):
    """
    异步检查点装饰器 - 如果输出文件存在则跳过执行。

    参数：
        output_path: 输出文件路径（字符串、Path 或返回路径的可调用对象）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 解析输出路径
            if callable(output_path):
                path = output_path(*args, **kwargs)
            else:
                path = output_path

            # 检查文件是否存在
            if os.path.exists(path):
                logger.info(f"跳过 {func.__name__}，输出文件存在：{path}")
                return str(path)

            # 执行函数
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_decorators.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/utils/decorators.py tests/unit/test_decorators.py
git commit -m "feat(utils): 迁移带测试的异步装饰器"
```

---

### 任务 3.2：迁移 LLM 工具

**文件：**
- 修改：`core/utils/llm.py`（如果存在）或创建
- 测试：`tests/unit/test_llm.py`

**步骤 1：检查现有 LLM 模块**

```bash
cat core/utils/llm.py | head -50
```

如果存在，我们将测试并可能重构。如果不存在，从 temp 创建。

**步骤 2：编写失败测试**

创建：`tests/unit/test_llm.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.utils.llm import LLMClient, get_llm_client


@pytest.mark.asyncio
async def test_llm_client_creation():
    """测试创建 LLM 客户端。"""
    client = LLMClient(
        api_key="test_key",
        base_url="http://test.com",
        model="gpt-4o"
    )
    assert client.api_key == "test_key"
    assert client.base_url == "http://test.com"
    assert client.model == "gpt-4o"


@pytest.mark.asyncio
async def test_llm_chat_completion(mock_llm_client):
    """测试聊天补全。"""
    with patch('core.utils.llm.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="测试响应"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        client = LLMClient(api_key="test", base_url="http://test", model="gpt-4o")
        response = await client.chat("你好")

        assert response == "测试响应"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_llm_client_singleton():
    """测试 LLM 客户端单例。"""
    from core.utils.llm import get_llm_client, _llm_client_instance

    # 重置单例
    _llm_client_instance.clear()

    client1 = get_llm_client()
    client2 = get_llm_client()

    assert client1 is client2
```

**步骤 3：运行测试验证失败**

```bash
pytest tests/unit/test_llm.py -v
```

预期结果：可能失败，取决于现有实现

**步骤 4：查看/更新 LLM 实现**

读取现有：`core/utils/llm.py`

基于现有代码，确保它具有：
- AsyncOpenAI 客户端
- 带有 get_llm_client() 的单例模式
- 适当的错误处理
- 类型提示

**步骤 5：运行测试验证通过**

```bash
pytest tests/unit/test_llm.py -v
```

预期结果：PASS

**步骤 6：提交**

```bash
git add core/utils/llm.py tests/unit/test_llm.py
git commit -m "feat(utils): 添加带单例模式的 LLM 客户端"
```

---

### 任务 3.3：迁移 Prompts 模块

**文件：**
- 创建：`core/utils/prompts.py`
- 测试：`tests/unit/test_prompts.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_prompts.py`

```python
import pytest
from core.utils.prompts import (
    get_split_prompt,
    get_summary_prompt,
    get_prompt_faithfulness,
    get_prompt_expressiveness,
    get_align_prompt,
)


def test_get_split_prompt():
    """测试分割提示词生成。"""
    prompt = get_split_prompt("测试文本", "zh")
    assert "测试文本" in prompt
    assert "zh" in prompt
    assert isinstance(prompt, str)


def test_get_summary_prompt():
    """测试摘要提示词生成。"""
    prompt = get_summary_prompt("测试内容", "en")
    assert "测试内容" in prompt
    assert isinstance(prompt, str)


def test_get_prompt_faithfulness():
    """测试直译提示词。"""
    prompt = get_prompt_faithfulness("原文", "en", {"term": "术语"})
    assert "原文" in prompt
    assert "en" in prompt
    assert isinstance(prompt, str)


def test_get_prompt_expressiveness():
    """测试意译提示词。"""
    prompt = get_prompt_expressiveness("直译结果", "原文", "en")
    assert "直译结果" in prompt
    assert "原文" in prompt
    assert isinstance(prompt, str)


def test_get_align_prompt():
    """测试对齐提示词。"""
    prompt = get_align_prompt("翻译文本", 10.0, 15.0)
    assert "翻译文本" in prompt
    assert "10.0" in prompt or "10" in prompt
    assert isinstance(prompt, str)
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_prompts.py -v
```

预期结果：FAIL - prompts 模块不存在

**步骤 3：从 temp 迁移 prompts**

检查源文件：

```bash
cat temp/tools/prompts.py
```

创建：`core/utils/prompts.py`

```python
"""VideoVerse 流水线的 AI 提示词模板。"""

def get_split_prompt(text: str, language: str) -> str:
    """
    生成语义文本分割的提示词。

    参数：
        text: 要分割的文本
        language: 语言代码

    返回：
        格式化的提示词
    """
    return f"""请将以下文本分割成有意义的段落。

语言：{language}
文本：{text}

返回分割的段落作为字符串的 JSON 列表。"""


def get_summary_prompt(text: str, target_language: str) -> str:
    """
    生成摘要和术语提取的提示词。

    参数：
        text: 要摘要的文本
        target_language: 翻译的目标语言

    返回：
        格式化的提示词
    """
    return f"""分析以下文本并提供：
1. 简要摘要（2-3 句话）
2. 翻译成 {target_language} 的关键术语

文本：{text}

返回带有 "summary" 和 "terminology" 键的 JSON。"""


def get_prompt_faithfulness(
    text: str,
    target_language: str,
    terminology: dict = None
) -> str:
    """
    生成直译的提示词。

    参数：
        text: 要翻译的文本
        target_language: 目标语言代码
        terminology: 可选的术语词典

    返回：
        格式化的提示词
    """
    term_str = ""
    if terminology:
        term_str = f"\n术语：{terminology}"

    return f"""将以下文本翻译成 {target_language}。
专注于对原意的直译。{term_str}

文本：{text}

仅返回翻译。"""


def get_prompt_expressiveness(
    literal_translation: str,
    original_text: str,
    target_language: str
) -> str:
    """
    生成意译优化的提示词。

    参数：
        literal_translation: 直译结果
        original_text: 原始源文本
        target_language: 目标语言代码

    返回：
        格式化的提示词
    """
    return f"""优化以下翻译，使其在 {target_language} 中更自然和富有表现力，
同时保持准确性。

原文：{original_text}
直译：{literal_translation}

仅返回优化后的翻译。"""


def get_align_prompt(
    text: str,
    start_time: float,
    end_time: float
) -> str:
    """
    生成字幕对齐的提示词。

    参数：
        text: 要对齐的文本
        start_time: 开始时间戳
        end_time: 结束时间戳

    返回：
        格式化的提示词
    """
    return f"""调整以下字幕文本以适应
时间窗口 [{start_time:.2f}s - {end_time:.2f}s]。

文本：{text}

返回调整后的文本（如有必要则缩短）。"""
```

**注意：** 以上是简化版本。从 `temp/tools/prompts.py` 复制完整实现。

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_prompts.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/utils/prompts.py tests/unit/test_prompts.py
git commit -m "feat(utils): 迁移带测试的提示词模板"
```

---

## 第四阶段：ASR 步骤重构

### 任务 4.1：将 ASR 步骤重构为插件

**文件：**
- 创建：`core/steps/__init__.py`
- 创建：`core/steps/step_02_asr.py`
- 测试：`tests/unit/test_steps/test_step_02_asr.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_steps/test_step_02_asr.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.steps.step_02_asr import ASRStep
from core.pipeline.context import PipelineContext
from core.config import Settings


@pytest.mark.asyncio
async def test_asr_step_name():
    """测试 ASR 步骤有正确的名称。"""
    step = ASRStep()
    assert step.name == "step_02_asr"


@pytest.mark.asyncio
async def test_asr_step_dependencies():
    """测试 ASR 步骤依赖。"""
    step = ASRStep()
    assert "step_01_download" in step.dependencies


@pytest.mark.asyncio
async def test_asr_step_validate():
    """测试 ASR 步骤验证。"""
    step = ASRStep()
    context = MagicMock()
    context.storage = {"video_path": "/path/to/video.mp4"}

    with patch("pathlib.Path.exists", return_value=True):
        result = await step.validate(context)
        assert result is True


@pytest.mark.asyncio
async def test_asr_step_validate_missing_video():
    """测试缺少视频时的 ASR 步骤验证。"""
    step = ASRStep()
    context = MagicMock()
    context.storage = {}

    result = await step.validate(context)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asr_step_execute_mock():
    """测试带模拟 ASR 的 ASR 步骤执行。"""
    step = ASRStep()

    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=Settings(),
        storage={"video_path": "test.mp4"}
    )

    with patch("core.steps.step_02_asr.process_transcription") as mock_process:
        mock_process.return_value = MagicMock()
        with patch.object(step, "_save_results", return_value="/path/to/output.xlsx"):
            result = await step.execute(context)

            assert "asr_result" in context.storage
            mock_process.assert_called_once()
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_steps/test_step_02_asr.py -v
```

预期结果：FAIL - 步骤不是插件形式

**步骤 3：创建 ASR 步骤插件**

创建：`core/steps/__init__.py`

```python
"""VideoVerse 的流水线步骤。"""
# 步骤将在这里导出
```

创建：`core/steps/step_02_asr.py`

```python
"""步骤 02：ASR - 自动语音识别。"""
from pathlib import Path
from typing import List
from loguru import logger
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.config import get_settings

# 导入 ASR 函数
from core.asr.common import process_transcription, save_results
from core.asr.ffmpeg_local import ffmpeg_video_to_audio
from core.asr.demucs_local import demucs_audio
from core.asr.pydub_local import normalize_audio_volume, split_audio
from core.asr.whisperx_local import transcribe_audio

settings = get_settings()


class ASRStep(PipelineStep):
    """ASR 处理步骤 - 将音频转录为文本。"""

    def __init__(self, use_demucs: bool = True):
        self._use_demucs = use_demucs

    @property
    def name(self) -> str:
        return "step_02_asr"

    @property
    def dependencies(self) -> List[str]:
        return ["step_01_download"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证视频文件是否存在。"""
        video_path = context.get("video_path")
        if not video_path:
            logger.error("上下文中没有 video_path")
            return False
        return Path(video_path).exists()

    async def execute(self, context: PipelineContext) -> str:
        """
        执行 ASR 处理。

        返回：
            带有转录结果的输出 Excel 文件路径
        """
        video_path = context.get("video_path")
        language = context.source_language

        logger.info(f"开始 ASR 处理：{video_path}")

        # 2.1：提取音频
        mp3_path = ffmpeg_video_to_audio(video_path)
        logger.info(f"音频已提取：{mp3_path}")

        # 2.2：分离人声（可选）
        if self._use_demucs:
            vocal_audio = demucs_audio(mp3_path)
        else:
            vocal_audio = mp3_path

        # 2.3：标准化音频
        vocal_normalized = normalize_audio_volume(vocal_audio)

        # 2.4：将音频分割成片段
        segments = split_audio(vocal_normalized)
        logger.info(f"音频已分割成 {len(segments)} 个片段")

        # 2.5：转录每个片段
        all_results = []
        for start, end in segments:
            result = transcribe_audio(vocal_normalized, vocal_audio, start, end)
            all_results.append(result)

        # 2.6：合并结果
        combined_result = {"segments": []}
        for result in all_results:
            combined_result["segments"].extend(result["segments"])

        # 2.7：处理并保存
        df = process_transcription(combined_result)

        from core.paths import paths
        output_path = paths.cleaned_chunks
        df = save_results(df, str(output_path))

        # 在上下文中存储结果
        context.set("asr_result", str(output_path))
        context.set("asr_dataframe", df)

        logger.success(f"ASR 处理完成：{output_path}")
        return str(output_path)


def create_step(use_demucs: bool = True) -> ASRStep:
    """ASR 步骤的工厂函数。"""
    return ASRStep(use_demucs=use_demucs)
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_steps/test_step_02_asr.py -v
```

预期结果：PASS（适当模拟）

**步骤 5：提交**

```bash
git add core/steps/ tests/unit/test_steps/
git commit -m "feat(steps): 添加带测试的 ASR 步骤作为插件"
```

---

### 任务 4.2：重构 NLP 分割步骤

**文件：**
- 创建：`core/steps/step_03_nlp_split.py`
- 测试：`tests/unit/test_steps/test_step_03_nlp_split.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_steps/test_step_03_nlp_split.py`

```python
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from core.steps.step_03_nlp_split import NLPSplitStep
from core.pipeline.context import PipelineContext
from core.config import Settings


@pytest.fixture
def mock_dataframe():
    """创建模拟 DataFrame。"""
    return pd.DataFrame({
        "text": ["测试句子1", "测试句子2", "测试句子3"]
    })


@pytest.mark.asyncio
async def test_nlp_step_name():
    """测试 NLP 步骤名称。"""
    step = NLPSplitStep()
    assert step.name == "step_03_nlp_split"


@pytest.mark.asyncio
async def test_nlp_step_dependencies():
    """测试 NLP 步骤依赖。"""
    step = NLPSplitStep()
    assert "step_02_asr" in step.dependencies


@pytest.mark.asyncio
async def test_nlp_step_validate_with_asr(pipeline_context, mock_dataframe):
    """测试有 ASR 结果时验证通过。"""
    step = NLPSplitStep()
    pipeline_context.set("asr_dataframe", mock_dataframe)

    result = await step.validate(pipeline_context)
    assert result is True


@pytest.mark.asyncio
async def test_nlp_step_execute_mock(pipeline_context, mock_dataframe):
    """测试带模拟 NLP 处理的执行。"""
    step = NLPSplitStep()
    pipeline_context.set("asr_dataframe", mock_dataframe)

    with patch("core.steps.step_03_nlp_split.process_nlp_split") as mock_nlp:
        mock_nlp.return_value = "/path/to/nlp_output.txt"

        result = await step.execute(pipeline_context)

        assert "nlp_split" in pipeline_context.storage
        assert result == "/path/to/nlp_output.txt"
        mock_nlp.assert_called_once()
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_steps/test_step_03_nlp_split.py -v
```

预期结果：FAIL

**步骤 3：实现 NLP 分割步骤**

创建：`core/steps/step_03_nlp_split.py`

```python
"""步骤 03：NLP 分割 - 按语言边界分割文本。"""
from typing import List
from loguru import logger
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

# 导入 NLP 函数
from core.nlp.jieba_spacy_split import process_nlp_split


class NLPSplitStep(PipelineStep):
    """基于 NLP 的文本分割步骤。"""

    @property
    def name(self) -> str:
        return "step_03_nlp_split"

    @property
    def dependencies(self) -> List[str]:
        return ["step_02_asr"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证 ASR 结果是否存在。"""
        df = context.get("asr_dataframe")
        if df is None:
            logger.error("上下文中没有 asr_dataframe")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """
        执行 NLP 分割。

        返回：
            带有分割结果的输出文本文件路径
        """
        df = context.get("asr_dataframe")
        language = context.source_language

        logger.info("开始 NLP 分割")

        # 处理 NLP 分割
        output_path = process_nlp_split(df, language)

        # 存储结果
        context.set("nlp_split", output_path)
        context.set("nlp_result", output_path)

        logger.success(f"NLP 分割完成：{output_path}")
        return output_path


def create_step() -> NLPSplitStep:
    """NLP 分割步骤的工厂函数。"""
    return NLPSplitStep()
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_steps/test_step_03_nlp_split.py -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/steps/step_03_nlp_split.py tests/unit/test_steps/test_step_03_nlp_split.py
git commit -m "feat(steps): 添加 NLP 分割步骤作为插件"
```

---

## 第五阶段：TTS 后端迁移

### 任务 5.1：创建 TTS 基类和 Edge TTS

**文件：**
- 创建：`core/tts/__init__.py`
- 创建：`core/tts/base.py`
- 创建：`core/tts/edge.py`
- 测试：`tests/unit/test_tts/test_base.py`、`tests/unit/test_tts/test_edge.py`

**步骤 1：编写失败测试**

创建：`tests/unit/test_tts/test_base.py`

```python
import pytest
from core.tts.base import TTSBackend


class DummyTTS(TTSBackend):
    """测试 TTS 后端。"""

    async def synthesize(self, text: str, output_path: str):
        with open(output_path, "wb") as f:
            f.write(b"dummy audio")


@pytest.mark.asyncio
async def test_tts_backend_name():
    """测试后端有名称。"""
    backend = DummyTTS()
    assert backend.name == "dummy"


@pytest.mark.asyncio
async def test_tts_backend_synthesize(tmp_path):
    """测试合成创建输出文件。"""
    backend = DummyTTS()
    output_file = tmp_path / "test.mp3"

    await backend.synthesize("你好", str(output_file))

    assert output_file.exists()
    assert output_file.read_bytes() == b"dummy audio"
```

创建：`tests/unit/test_tts/test_edge.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from core.tts.edge import EdgeTTSBackend


@pytest.mark.asyncio
async def test_edge_tts_name():
    """测试 Edge TTS 后端名称。"""
    backend = EdgeTTSBackend(voice="zh-CN-XiaoxiaoNeural")
    assert backend.name == "edge"


@pytest.mark.asyncio
async def test_edge_tts_synthesize_mock(tmp_path):
    """测试带模拟的 Edge TTS 合成。"""
    backend = EdgeTTSBackend(voice="zh-CN-XiaoxiaoNeural")
    output_file = tmp_path / "test.mp3"

    with patch("edge_tts.Communicate") as mock_communicate:
        mock_comm = AsyncMock()
        mock_comm.save = AsyncMock()
        mock_communicate.return_value = mock_comm

        await backend.synthesize("测试", str(output_file))

        mock_communicate.assert_called_once()
        mock_comm.save.assert_called_once()
```

**步骤 2：运行测试验证失败**

```bash
pytest tests/unit/test_tts/ -v
```

预期结果：FAIL - 模块不存在

**步骤 3：实现 TTS 基类和 Edge 后端**

创建：`core/tts/__init__.py`

```python
"""VideoVerse 的 TTS 后端。"""
from core.tts.base import TTSBackend
from core.tts.edge import EdgeTTSBackend

__all__ = ["TTSBackend", "EdgeTTSBackend"]
```

创建：`core/tts/base.py`

```python
"""TTS 后端的基类。"""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSBackend(ABC):
    """TTS 后端的抽象基类。"""

    def __init__(self, voice: str = ""):
        self._voice = voice

    @property
    def name(self) -> str:
        """后端名称。"""
        return self.__class__.__name__.replace("TTSBackend", "").lower()

    @property
    def voice(self) -> str:
        """当前语音。"""
        return self._voice

    @abstractmethod
    async def synthesize(self, text: str, output_path: str) -> None:
        """
        从文本合成语音。

        参数：
            text: 输入文本
            output_path: 保存音频文件的位置
        """
        pass
```

创建：`core/tts/edge.py`

```python
"""Edge TTS 后端。"""
import edge_tts
from loguru import logger
from core.tts.base import TTSBackend


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS 后端。"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        super().__init__(voice)
        logger.info(f"Edge TTS 已初始化，语音：{voice}")

    async def synthesize(self, text: str, output_path: str) -> None:
        """
        使用 Edge TTS 合成语音。

        参数：
            text: 输入文本
            output_path: 输出音频文件路径
        """
        logger.info(f"使用 Edge TTS 合成：{text[:50]}...")

        communicate = edge_tts.Communicate(text, self._voice)
        await communicate.save(output_path)

        logger.success(f"音频已保存到：{output_path}")


def create_backend(voice: str = "zh-CN-XiaoxiaoNeural") -> EdgeTTSBackend:
    """工厂函数。"""
    return EdgeTTSBackend(voice)
```

**步骤 4：运行测试验证通过**

```bash
pytest tests/unit/test_tts/ -v
```

预期结果：PASS

**步骤 5：提交**

```bash
git add core/tts/ tests/unit/test_tts/
git commit -m "feat(tts): 添加 TTS 基类和 Edge 后端"
```

---

## 第六阶段：集成测试

### 任务 6.1：创建端到端流水线测试

**文件：**
- 测试：`tests/integration/test_pipeline.py`

**步骤 1：编写集成测试**

创建：`tests/integration/test_pipeline.py`

```python
import pytest
from pathlib import Path
from core.pipeline.engine import PipelineEngine
from core.pipeline.registry import StepRegistry
from core.steps.step_02_asr import create_step as create_asr_step
from core.steps.step_03_nlp_split import create_step as create_nlp_step


@pytest.mark.integration
@pytest.mark.slow
class TestPipelineIntegration:
    """完整流水线的集成测试。"""

    @pytest.mark.asyncio
    async def test_asr_to_nlp_flow(self, test_video_dir):
        """测试 ASR -> NLP 流程。"""
        # 此测试需要实际的视频文件
        video_file = test_video_dir / "demo.mp4"
        if not video_file.exists():
            pytest.skip("未找到测试视频 - 将 demo.mp4 添加到 tests/fixtures/video/")

        # 创建注册表
        registry = StepRegistry()

        # 创建模拟下载步骤（仅设置 video_path）
        from core.pipeline.base import PipelineStep

        class MockDownloadStep(PipelineStep):
            @property
            def name(self):
                return "step_01_download"

            async def execute(self, context):
                context.set("video_path", str(video_file))
                return str(video_file)

        registry.register("step_01_download", MockDownloadStep())
        registry.register("step_02_asr", create_asr_step(use_demucs=False))  # 跳过 demucs 以提高速度
        registry.register("step_03_nlp_split", create_nlp_step())

        # 运行流水线
        engine = PipelineEngine(registry)
        context = await engine.run(
            steps=["step_03_nlp_split"],  # 将运行 download 和 asr 作为依赖
            video_source=str(video_file),
            source_language="zh",
            target_language="en",
        )

        # 验证
        assert context.has("video_path")
        assert context.has("asr_result")
        assert context.has("nlp_split")

        # 检查文件存在
        assert Path(context.get("asr_result")).exists()
        assert Path(context.get("nlp_split")).exists()


@pytest.mark.integration
@pytest.mark.gpu
@pytest.mark.asyncio
async def test_full_asr_with_gpu(self, test_video_dir):
    """测试带 GPU 加速的完整 ASR 流程。"""
    pytest.skip("需要 GPU - 手动运行：pytest -m gpu")
```

**步骤 2：运行集成测试**

```bash
pytest tests/integration/test_pipeline.py -v
```

预期结果：如果没有测试视频则跳过，或如果视频存在则通过

**步骤 3：提交**

```bash
git add tests/integration/
git commit -m "test(integration): 添加端到端流水线测试"
```

---

## 第七阶段：文档和完成

### 任务 7.1：更新 .env.example

**文件：**
- 修改：`.env.example`

**步骤 1：使用所有新选项更新 .env.example**

```bash
cat > .env.example << 'EOF'
# ==================== LLM API 配置 ====================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4096

# ==================== 模型路径 ====================
# 包含已下载模型的目录（不要设置为空以启用自动下载）
MODEL_CACHE_DIR=models

# WhisperX 模型路径（如果使用本地模型）
WHISPER_MODEL=large-v3
WHISPER_MODEL_DIR=
WHISPER_ZH_MODEL=

# Wav2Vec2 模型路径（用于中文对齐）
WAV2VEC2_MODEL=

# ==================== 路径配置 ====================
# 所有生成文件的输出目录
OUTPUT_DIR=output

# 中间文件的临时目录
TEMP_DIR=temp

# ==================== 下载行为 ====================
# 设置为 'true' 以禁用自动模型下载（仅使用本地模型）
DISABLE_AUTO_DOWNLOAD=false

# HuggingFace 镜像（用于在中国加速下载）
HF_ENDPOINT=https://hf-mirror.com

# ==================== TTS 配置 ====================
# TTS 方法：edge、azure、openai、fish、gpt_sovits
TTS_METHOD=edge

# Edge TTS 语音
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural

# TTS 速度调整因子
SPEED_FACTOR_MIN=0.8
SPEED_FACTOR_ACCEPT=1.0
SPEED_FACTOR_MAX=1.2

# ==================== ASR 配置 ====================
# ASR 运行时：local、api、elevenlabs
WHISPER_RUNTIME=local

# ==================== 视频配置 ====================
# YouTube 下载分辨率
YOUTUBE_RESOLUTION=1080

# 允许的视频格式
ALLOWED_VIDEO_FORMATS=mp4,mkv,webm,avi

# ==================== 字幕配置 ====================
# 将字幕烧录到视频中
BURN_SUBTITLES=true

# 最大字幕长度（Netflix 标准）
SUBTITLE_MAX_LENGTH=75
EOF
```

**步骤 2：提交**

```bash
git add .env.example
git commit -m "docs: 使用所有配置选项更新 .env.example"
```

---

### 任务 7.2：创建测试 README

**文件：**
- 创建：`tests/README.md`

**步骤 1：创建测试文档**

```bash
cat > tests/README.md << 'EOF'
# VideoVerse 测试套件

## 运行测试

### 运行所有测试
```bash
pytest
```

### 仅运行单元测试
```bash
pytest -m unit
```

### 仅运行集成测试
```bash
pytest -m integration
```

### 跳过慢速测试
```bash
pytest -m "not slow"
```

### 运行带覆盖率的测试
```bash
pytest --cov=core --cov-report=html
```

### 运行特定测试文件
```bash
pytest tests/unit/test_config.py -v
```

## 测试组织

```
tests/
├── unit/              # 快速、隔离的单元测试
│   ├── test_config.py
│   ├── test_paths.py
│   ├── test_pipeline/
│   ├── test_asr/
│   ├── test_nlp/
│   └── test_steps/
└── integration/       # 较慢的多组件测试
    └── test_pipeline.py
```

## 测试标记

- `unit`：快速单元测试（每个 < 1 秒）
- `integration`：测试组件交互的集成测试
- `slow`：耗时 > 10 秒的测试（模型加载、实际处理）
- `gpu`：需要 CUDA GPU 的测试
- `llm`：需要真实 LLM API 密钥的测试

## 测试数据

将测试 fixtures 放置在：
- `tests/fixtures/audio/` - 音频样本
- `tests/fixtures/video/` - 视频样本
- `tests/fixtures/models/` - 模拟模型输出

## CI/CD

在 CI 环境中，测试运行时使用：
- `-m "not gpu and not slow"` - 跳过 GPU 和慢速测试
- `--cov=core` - 生成覆盖率报告
- `--strict-markers` - 确保所有标记都已定义
EOF
```

**步骤 2：提交**

```bash
git add tests/README.md
git commit -m "docs: 添加测试套件文档"
```

---

### 任务 7.3：更新主 README

**文件：**
- 修改：`README.md`

**步骤 1：将测试部分添加到 README**

添加到 README.md：

```markdown
## 测试

项目使用 pytest 进行测试。详情参见 [tests/README.md](tests/README.md)。

快速开始：
```bash
# 仅运行单元测试
pytest -m unit

# 运行带覆盖率的测试
pytest --cov=core --cov-report=html
```

## 架构

流水线使用基于插件的架构：

- `PipelineStep`：所有处理步骤的抽象基类
- `PipelineContext`：在步骤之间传递的数据
- `StepRegistry`：注册和解析步骤依赖关系
- `PipelineEngine`：编排执行

每个步骤都是独立可测试的，可以被跳过/覆盖。
```

**步骤 2：提交**

```bash
git add README.md
git commit -m "docs: 使用测试和架构信息更新 README"
```

---

### 任务 7.4：最终验证

**步骤 1：运行完整测试套件**

```bash
pytest -m "not slow" -v
```

预期结果：所有非慢速测试通过

**步骤 2：运行代码质量检查**

```bash
ruff check core/
ruff format --check core/
```

预期结果：无错误

**步骤 3：验证导入工作**

```python
python -c "from core.pipeline import PipelineEngine, StepRegistry, PipelineContext; print('导入成功')"
```

预期结果：无导入错误

**步骤 4：最终提交**

```bash
git add .
git commit -m "feat: 完成流水线重构，包含插件架构和测试套件"
```

---

## 总结

此计划将 VideoVerse 流水线从单体 `temp/` 结构重构为模块化、可测试的 `core/` 架构，包括：

1. **插件系统**：每个处理步骤都是 `PipelineStep` 插件
2. **依赖解析**：通过 `StepRegistry` 自动依赖排序
3. **全面测试**：pytest 套件，包含单元、集成和慢速测试
4. **最佳实践**：TDD 方法、类型提示、文档、CI/CD 就绪

**预计总时间**：跨越 7 个阶段 15-20 小时
**测试覆盖率目标**：核心模块 >80%
**提交频率**：每个任务 = 1 次提交，便于回滚
