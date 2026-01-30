# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

VideoVerse 是一个基于 AI 的视频翻译和配音工具，使用 13 步处理流水线从 YouTube 或本地视频生成带字幕和配音的视频。

**注意**: 项目已完成从 `src/` 到 `core/` 的架构迁移，新架构采用 PipelineStep 模式。

### 核心技术栈
- **Python 3.10-3.12** (uv 包管理)
- **PipelineStep 架构**: 清晰的依赖管理和数据传递
- **AI/ML**: WhisperX 3.2 (词级ASR), Spacy 3.7 (可选 NLP), PyTorch 2.1 (CUDA 11.8)
- **配置管理**: pydantic-settings + 环境变量
- **视频处理**: MoviePy, Librosa, PyAV

### 常用命令

```bash
# 安装依赖
uv sync

# 运行基础测试
python tests/test_basic.py

# 验证流水线步骤
python tests/verify_pipeline.py

# 运行示例流水线
python examples/run_pipeline.py
```

### 环境变量配置

项目使用 `.env` 文件配置，通过 `pydantic-settings` 加载 (见 `core/config.py`)。最小配置：

```bash
# LLM API (必需)
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# TTS (可选, edge 免费)
TTS_METHOD=edge
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural

# ASR (可选, local 默认)
WHISPER_RUNTIME=local
WHISPER_MODEL=large-v3
```

完整配置参考 `.env.example`。

### 项目结构（新架构）

```
core/                       # 核心源代码
├── __init__.py            # 统一导出
├── config.py              # pydantic-settings 配置
├── paths.py               # PathManager 路径管理
│
├── pipeline/              # 流水线框架
│   ├── base.py            # PipelineStep 基类
│   ├── context.py         # PipelineContext
│   ├── registry.py        # StepRegistry
│   └── engine.py          # PipelineEngine
│
├── steps/                 # 13 个处理步骤 (PipelineStep 类)
│   ├── step_01_download.py
│   ├── step_02_asr.py
│   ├── step_03_nlp_split.py
│   ├── step_04_meaning_split.py
│   ├── step_05_summarize.py
│   ├── step_06_translate.py
│   ├── step_07_split_sub.py
│   ├── step_08_gen_sub.py
│   ├── step_09_burn_sub.py
│   ├── step_10_audio_task.py
│   ├── step_11_gen_audio.py
│   ├── step_12_merge_audio.py
│   └── step_13_dubbing.py
│
├── tts/                   # TTS 后端
│   ├── base.py            # TTSBackend 基类
│   ├── edge.py
│   ├── azure.py
│   ├── openai.py
│   ├── fish.py
│   └── gpt_sovits.py
│
└── utils/                 # 工具函数
    ├── cache.py           # 缓存管理
    ├── llm.py             # LLM API
    ├── decorators.py      # 装饰器
    ├── common.py          # 通用工具
    └── prompts.py         # 简化 Prompt

tools/                     # 工具模块（根目录）
├── prompts.py             # 完整 AI Prompt 模板
├── translate_lines.py     # 翻译逻辑
└── spacy_utils/           # NLP 工具（可选依赖）
    ├── __init__.py        # 优雅处理 spacy 缺失
    └── ...

temp/                      # 旧实现（用于对比验证）
├── steps/                 # 旧的步骤实现
└── backends/              # 旧的后端实现
```

### PipelineStep 架构

新架构使用 PipelineStep 模式：

```python
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

class MyStep(PipelineStep):
    @property
    def name(self) -> str:
        return "step_XX_name"

    @property
    def dependencies(self) -> list[str]:
        return ["step_XX_previous"]  # 依赖的前置步骤

    async def validate(self, context: PipelineContext) -> bool:
        # 验证前置条件
        return True

    async def execute(self, context: PipelineContext) -> str:
        # 执行步骤逻辑
        result = do_work()
        context.set("result_key", result)
        return result_path

def create_step() -> MyStep:
    return MyStep()
```

### 流水线执行

```python
from core.pipeline import PipelineEngine, StepRegistry
from core.steps import create_download_step, create_asr_step

# 创建注册表并注册步骤
registry = StepRegistry()
registry.register("step_01_download", create_download_step())
registry.register("step_02_asr", create_asr_step())

# 创建引擎
engine = PipelineEngine(registry)

# 运行流水线
context = await engine.run(
    steps=["step_02_asr"],  # 会自动解析依赖，包含 step_01_download
    video_source="video.mp4",
    source_language="en",
    target_language="zh",
)
```

### 架构要点

1. **PipelineStep 模式**: 所有步骤继承自 `PipelineStep`，声明依赖和验证逻辑
2. **依赖解析**: `StepRegistry` 自动解析步骤依赖关系
3. **数据传递**: 使用 `PipelineContext` 在步骤间传递数据
4. **可选依赖处理**: spacy 等可选依赖优雅处理（见 `tools/spacy_utils/__init__.py`）
5. **配置驱动**: 使用 `pydantic-settings` 从环境变量加载配置

### 语言检测与分割

- **中文**: 使用 jieba 分词，`whisper_language=zh` 时使用 Belle-whisper-large-v3-zh-punct 模型
- **其他语言**: 使用对应 Spacy 模型 (`en_core_web_md` 等)，见 `core/config.py` 中的 `spacy_model_map`

### LLM 提示词管理

完整 Prompt 模板在 `tools/prompts.py` 中：
- `get_split_prompt()` - 语义分割
- `get_summary_prompt()` - 摘要和术语提取
- `get_prompt_faithfulness()` - 直译
- `get_prompt_expressiveness()` - 意译
- `get_align_prompt()` - 字幕对齐

简化版本在 `core/utils/prompts.py` 中。

### 输出目录结构

```
output/
├── log/                   # 日志和中间文件
│   ├── cleaned_chunks.xlsx      # 转录文本
│   ├── split_by_nlp.txt         # NLP 分割
│   ├── split_by_meaning.txt     # 语义分割
│   ├── terminology.json         # 术语表
│   ├── translation_results.xlsx # 翻译结果
│   └── gpt_log/                 # LLM 调用日志
├── audio/                 # 音频处理
│   ├── raw.mp3            # 原始音频
│   ├── vocal.mp3          # 人声音频
│   ├── refers/            # 参考音频
│   ├── segs/              # TTS 片段
│   └── tts_tasks.xlsx     # TTS 任务表
├── output_sub.mp4         # 带字幕视频
└── output_dub.mp4         # 配音视频
```

### 注意事项

1. **可选依赖**: spacy、jieba 等依赖可选，缺失时使用占位函数
2. **TTS 后端**: 所有 TTS 后端支持 `refer_audio` 参数（用于声音克隆）
3. **路径管理**: 使用 `core.paths.paths` 单例访问所有路径
4. **字幕格式**: 严格单行字幕，最长 75 字符 (Netflix 标准)

### 依赖说明

- PyTorch 使用 CUDA 11.8 版本，通过 `[tool.uv.sources]` 从 PyTorch index 安装
- Demucs 和 Spacy 模型使用本地路径 (`files/` 目录)
- 某些包使用 override dependencies (av>=13.0.0, tokenizers)

### 迁移说明

项目已从 `src/` 迁移到 `core/`，详见 [`docs/MIGRATION.md`](docs/MIGRATION.md)。

**导入路径变更**:
- `from src.config import get_settings` → `from core.config import get_settings`
- `from src.utils.paths import VIDEO_PATH` → `from core.paths import paths`
- `from src.tools.prompts import get_split_prompt` → `from tools.prompts import get_split_prompt`
- `from src.backends.tts.edge_tts import EdgeTTSBackend` → `from core.tts import EdgeTTSBackend, create_edge_backend`
