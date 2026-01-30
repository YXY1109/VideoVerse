# VideoVerse 迁移指南

本文档说明从旧的 `src/` 目录结构迁移到新的 `core/` 目录结构的变更。

## 架构变更

### 目录结构变化

**旧结构 (`src/`)**:
```
src/
├── pipeline.py           # 主流水线
├── api.py                # Python API
├── config.py             # 配置管理
├── steps/                # 13 个处理步骤 (函数形式)
├── backends/             # ASR/TTS 后端
├── tools/                # 工具模块
└── utils/                # 核心工具
```

**新结构 (`core/`)**:
```
core/
├── __init__.py           # 统一导出
├── config.py             # 配置管理 (pydantic-settings)
├── paths.py              # 路径管理 (PathManager)
├── pipeline/             # 流水线框架
│   ├── base.py           # PipelineStep 基类
│   ├── context.py        # PipelineContext
│   ├── registry.py       # StepRegistry
│   └── engine.py         # PipelineEngine
├── steps/                # 13 个处理步骤 (PipelineStep 类)
│   ├── step_01_download.py
│   ├── step_02_asr.py
│   └── ...
├── tts/                  # TTS 后端
│   ├── base.py           # TTSBackend 基类
│   ├── edge.py
│   ├── azure.py
│   ├── openai.py
│   ├── fish.py
│   └── gpt_sovits.py
└── utils/                # 工具函数
    ├── cache.py
    ├── llm.py
    ├── decorators.py
    ├── common.py
    └── prompts.py

tools/                    # 工具模块 (移至根目录)
├── prompts.py            # 完整 Prompt 模板
├── translate_lines.py    # 翻译逻辑
└── spacy_utils/          # NLP 工具
    ├── __init__.py       # 可选依赖处理
    ├── load_nlp_model.py
    ├── split_by_mark.py
    └── ...
```

### 架构模式变更

**旧架构**:
- 步骤是独立的函数 (`step_XX_xxx()`)
- 通过装饰器 (`@async_check_file_exists`) 实现缓存
- 异步架构 (`asyncio`, `httpx`)

**新架构**:
- 步骤是 `PipelineStep` 类
- 通过 `PipelineContext` 传递数据
- 同步架构（可选择异步执行）
- 更清晰的依赖管理

## 代码迁移

### 步骤函数迁移

**旧代码** (`src/steps/01_download.py`):
```python
from src.utils.decorators import async_check_file_exists

@async_check_file_exists(VIDEO_PATH)
async def step_01_download(video_url: str = None) -> str:
    # 实现代码
    pass
```

**新代码** (`core/steps/step_01_download.py`):
```python
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

class DownloadStep(PipelineStep):
    @property
    def name(self) -> str:
        return "step_01_download"

    @property
    def dependencies(self) -> list[str]:
        return []

    async def validate(self, context: PipelineContext) -> bool:
        # 验证逻辑
        return True

    async def execute(self, context: PipelineContext) -> str:
        # 执行逻辑
        return result_path

def create_step() -> DownloadStep:
    return DownloadStep()
```

### 流水线执行变更

**旧代码**:
```python
from src.pipeline import run_pipeline

await run_pipeline(
    video_source="video.mp4",
    source_language="en",
    target_language="zh"
)
```

**新代码**:
```python
from core.pipeline import PipelineEngine, StepRegistry
from core.steps import create_download_step, create_asr_step

# 创建注册表
registry = StepRegistry()
registry.register("step_01_download", create_download_step())
registry.register("step_02_asr", create_asr_step())

# 创建引擎
engine = PipelineEngine(registry)

# 运行流水线
context = await engine.run(
    steps=["step_01_download", "step_02_asr"],
    video_source="video.mp4",
    source_language="en",
    target_language="zh"
)
```

## 配置迁移

### 配置类变更

**旧配置** (`src/config.py`):
```python
class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        # ...

def get_settings():
    return Settings()
```

**新配置** (`core/config.py`):
```python
from pydantic_settings import BaseSettings, Field

class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    tts_method: Literal["edge", "azure", "openai", "fish", "gpt_sovits"] = "edge"
    # ...

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

## 可选依赖处理

新架构对可选依赖（如 spacy）进行了优雅处理：

```python
# tools/spacy_utils/__init__.py
try:
    from tools.spacy_utils.load_nlp_model import init_nlp
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    init_nlp = None  # 占位函数

# 使用时检查
if SPACY_AVAILABLE:
    init_nlp()
else:
    logger.warning("Spacy not available, skipping NLP processing")
```

## 导入路径变更

| 旧导入路径 | 新导入路径 |
|----------|----------|
| `from src.config import get_settings` | `from core.config import get_settings` |
| `from src.utils.paths import VIDEO_PATH` | `from core.paths import paths` |
| `from src.tools.prompts import get_split_prompt` | `from tools.prompts import get_split_prompt` |
| `from src.backends.tts.edge_tts import EdgeTTSBackend` | `from core.tts import EdgeTTSBackend, create_edge_backend` |

## 兼容性说明

### 向后兼容

项目保留了 `temp/` 目录，包含原始实现用于：
- 功能对比验证
- 作为参考实现
- 逐步迁移验证

### 测试验证

使用 `tests/compare_outputs.py` 验证新旧实现输出一致性：

```bash
python tests/compare_outputs.py --temp-dir output/temp --core-dir output/core
```

## 迁移步骤

1. **更新导入**: 将所有 `from src.` 改为 `from core.`
2. **更新步骤调用**: 使用 `PipelineEngine` 替代直接函数调用
3. **更新配置**: 使用 `pydantic-settings` 加载环境变量
4. **测试验证**: 运行测试确保功能一致
5. **清理**: 验证通过后删除 `temp/` 目录

## 新功能

### PipelineStep 模式

- 清晰的依赖声明
- 内置验证逻辑
- 更好的错误处理
- 支持步骤跳过和重试

### 统一导出

```python
from core import (
    # 配置
    get_settings,
    # 流水线
    PipelineEngine,
    StepRegistry,
    PipelineContext,
    # TTS
    create_edge_backend,
    create_azure_backend,
    # 步骤工厂
    create_download_step,
    create_asr_step,
    # ...
)
```

### 更好的路径管理

```python
from core.paths import paths

# 使用 PathManager 单例
video_path = paths.video_path
audio_dir = paths.audio_dir
output_file = paths.output_video_with_sub
```
