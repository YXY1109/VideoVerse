<div align="center">

# VideoVerse

# 逐帧连接世界

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

> **项目来源**: 本项目最初代码来自 [VideoLingo](https://github.com/Huanshere/VideoLingo)，感谢原作者的开源贡献。

## 🌟 项目概述

**VideoVerse** 是一个基于 AI 的视频翻译、本地化和配音工具，能够生成 Netflix 级别的高质量单行字幕。通过完整的 13 步处理流水线，实现从视频下载到最终配音的全自动化处理。

### 核心特性

- 🎥 **视频下载** - 支持 YouTube 及本地视频文件
- 🎙️ **词级语音识别** - 基于 WhisperX 的高精度 ASR，支持词级时间轴对齐
- 📝 **智能字幕分割** - NLP + AI 双重分割，保持语义完整
- 📚 **术语库管理** - AI 自动提取 + 自定义术语，确保翻译一致性
- 🔄 **三步翻译流程** - 直译 → 反思 → 意译，打造电影级翻译质量
- ✅ **Netflix 标准** - 严格单行字幕，最长 75 字符
- 🗣️ **多 TTS 支持** - 5 种配音后端（GPT-SoVITS、Azure、OpenAI、Fish、Edge）
- ⚡ **模块化架构** - PipelineStep 模式，清晰依赖管理
- 🌐 **环境变量配置** - 使用 pydantic-settings 管理配置
- 🔄 **断点续传** - 详细日志记录，支持从任意步骤恢复

### 与同类项目的区别

**仅使用单行字幕、卓越的翻译质量、无缝的配音体验、高度模块化的 PipelineStep 流水线架构**

## 🏗️ 13 步处理流水线

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VideoVerse 处理流程                           │
├─────────────────────────────────────────────────────────────────────┤
│  视频与音频处理                                                      │
│  ┌─────────────┐    ┌─────────────┐                                 │
│  │ ① 视频下载   │ →  │ ② 语音识别   │ (WhisperX 词级时间轴)           │
│  └─────────────┘    └─────────────┘                                 │
│                                                                     │
│  文本处理                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ ③ NLP分割   │ →  │ ④ AI分割    │ →  │ ⑤ 内容摘要   │             │
│  └─────────────┘    └─────────────┘    │ + 术语提取   │             │
│                                        └─────────────┘             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ ⑥ 多步翻译   │ →  │ ⑦ 字幕分割   │ →  │ ⑧ 字幕生成   │             │
│  │ (直译-反思-意译)│               │    │             │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│  ┌─────────────┐                                                       │
│  │ ⑨ 字幕烧录   │ → 带字幕视频                                         │
│  └─────────────┘                                                       │
│                                                                     │
│  配音处理                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ ⑩ 音频任务   │ →  │ ⑪ TTS生成   │ →  │ ⑫ 音频合并   │             │
│  └─────────────┘    │ (5种后端)   │    └─────────────┘             │
│                     └─────────────┘                                 │
│  ┌─────────────┐                                                       │
│  │ ⑬ 配音合成   │ → 配音视频                                           │
│  └─────────────┘                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
VideoVerse/
├── pyproject.toml              # 项目依赖
├── .env.example                # 环境变量配置示例
├── README.md                   # 项目文档
│
├── core/                       # 核心源代码（新架构）
│   ├── __init__.py            # 统一导出
│   ├── config.py              # pydantic-settings 配置管理
│   ├── paths.py               # PathManager 路径管理
│   │
│   ├── pipeline/              # 流水线框架
│   │   ├── base.py            # PipelineStep 基类
│   │   ├── context.py         # PipelineContext 数据传递
│   │   ├── registry.py        # StepRegistry 依赖解析
│   │   └── engine.py          # PipelineEngine 执行编排
│   │
│   ├── steps/                 # 处理步骤模块（13步）
│   │   ├── step_01_download.py    # ① YouTube 视频下载
│   │   ├── step_02_asr.py         # ② WhisperX 语音识别
│   │   ├── step_03_nlp_split.py   # ③ NLP 句子分割
│   │   ├── step_04_meaning_split.py # ④ AI 语义分割
│   │   ├── step_05_summarize.py    # ⑤ 内容摘要 + 术语提取
│   │   ├── step_06_translate.py    # ⑥ 多步翻译
│   │   ├── step_07_split_sub.py    # ⑦ 字幕长度优化
│   │   ├── step_08_gen_sub.py      # ⑧ 字幕时间轴对齐
│   │   ├── step_09_burn_sub.py     # ⑨ 字幕烧录
│   │   ├── step_10_audio_task.py   # ⑩ 音频任务生成
│   │   ├── step_11_gen_audio.py    # ⑪ TTS 音频生成
│   │   ├── step_12_merge_audio.py  # ⑫ 音频合并
│   │   └── step_13_dubbing.py      # ⑬ 最终配音合成
│   │
│   ├── tts/                   # TTS 后端（5种）
│   │   ├── base.py            # TTSBackend 基类
│   │   ├── edge.py            # Edge TTS
│   │   ├── azure.py           # Azure TTS
│   │   ├── openai.py          # OpenAI TTS
│   │   ├── fish.py            # Fish TTS
│   │   └── gpt_sovits.py      # GPT-SoVITS
│   │
│   └── utils/                 # 核心工具函数
│       ├── cache.py           # 缓存管理
│       ├── llm.py             # LLM API 调用
│       ├── decorators.py      # 装饰器
│       ├── common.py          # 通用工具
│       └── prompts.py         # Prompt 模板
│
├── tools/                     # 工具模块（根目录）
│   ├── prompts.py             # 完整 AI Prompt 模板
│   ├── translate_lines.py     # 翻译逻辑
│   └── spacy_utils/           # NLP 工具
│       ├── __init__.py        # 可选依赖处理
│       ├── load_nlp_model.py
│       ├── split_by_mark.py
│       └── ...
│
├── temp/                      # 旧实现（用于对比验证）
│   ├── steps/                 # 旧的步骤实现
│   └── backends/              # 旧的后端实现
│
├── tests/                     # 测试脚本
│   ├── test_basic.py          # 基础测试
│   ├── verify_pipeline.py     # 流水线验证
│   └── compare_outputs.py     # 输出对比
│
├── examples/                  # 使用示例
│   └── run_pipeline.py        # 流水线运行示例
│
├── files/                     # 本地依赖
│   ├── demucs-main/          # Demucs 人声分离
│   └── *.whl                 # Spacy 模型包
│
└── output/                    # 输出目录
    ├── log/                   # 日志和中间文件
    ├── audio/                 # 音频处理
    ├── output_sub.mp4         # 带字幕的视频
    └── output_dub.mp4         # 最终配音视频
```

## 🎥 演示

<table>
<tr>
<td width="33%">

### 双语字幕
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Cosy2 声音克隆
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS 我的声音
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

## 🌍 语言支持

### 输入语言支持（8种）

🇺🇸 英语 🤩 | 🇷🇺 俄语 😊 | 🇫🇷 法语 🤩 | 🇩🇪 德语 🤩 | 🇮🇹 意大利语 🤩 | 🇪🇸 西班牙语 🤩 | 🇯🇵 日语 😐 | 🇨🇳 中文* 😊

> *中文使用独立的增强标点 whisper 模型

**翻译支持所有语言，配音语言取决于所选的 TTS 方法。**

## 🛠️ 技术栈

### 核心
- **Python 3.10-3.12** - 基础运行环境
- **pydantic-settings** - 环境变量配置管理
- **python-dotenv** - .env 文件加载

### 架构
- **PipelineStep 模式** - 清晰的步骤依赖管理
- **PipelineContext** - 步骤间数据传递
- **StepRegistry** - 依赖解析和执行编排
- **工厂模式** - 组件创建和配置

### AI / ML
- **WhisperX 3.2** - 词级语音识别与强制对齐
- **Spacy 3.7** - NLP 自然语言处理（可选依赖）
- **Transformers 4.48** - HuggingFace 模型支持
- **PyTorch 2.1** - 深度学习框架 (CUDA 11.8)

### 音视频处理
- **MoviePy 1.0** - 视频编辑
- **Librosa 0.10** - 音频分析
- **Pydub 0.25** - 音频处理
- **OpenCV 4.10** - 图像处理
- **PyAV 13.0** - 音视频编解码
- **yt-dlp** - YouTube 视频下载

### LLM 集成
- **OpenAI 1.55** - LLM API 客户端（兼容格式）
- **json-repair** - JSON 响应自动修复

### TTS 后端（5种）

1. **Azure TTS** - 微软 Azure 文本转语音
2. **OpenAI TTS** - OpenAI 文本转语音
3. **Fish TTS** - 开源高质量 TTS
4. **GPT-SoVITS** - 声音克隆 TTS
5. **Edge TTS** - Microsoft Edge 免费TTS

### ASR 后端

1. **WhisperX 本地** - large-v3 模型本地运行

## 📦 环境配置

### Windows NVIDIA GPU 用户前置准备

在安装之前，请先完成以下步骤：
1. 安装 [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
2. 安装 [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
3. 将 `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` 添加到系统 PATH
4. 重启电脑

### FFmpeg 依赖

FFmpeg 是必需的依赖，请通过包管理器安装：
- Windows: `choco install ffmpeg` (通过 [Chocolatey](https://chocolatey.org/))
- macOS: `brew install ffmpeg` (通过 [Homebrew](https://brew.sh/))
- Linux: `sudo apt install ffmpeg` (Debian/Ubuntu)

### 使用 uv 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/VideoVerse.git
cd VideoVerse

# 2. 复制环境变量配置
cp .env.example .env

# 3. 编辑 .env 填入 API 密钥
# 至少需要配置 OPENAI_API_KEY

# 4. 使用 uv 安装依赖（Python 3.10）
uv sync
```

## ⚙️ 配置说明

项目使用环境变量配置，主要配置项在 `.env` 文件中：

### 快速配置

```bash
# 最小配置 - 仅需 LLM API
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 选择 TTS 方法（推荐免费方案）
TTS_METHOD=edge
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural

# 选择 ASR 方法
WHISPER_RUNTIME=local
WHISPER_MODEL=large-v3
```

### 完整配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥 | - |
| `OPENAI_API_BASE` | LLM API 端点 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | LLM 模型名称 | `gpt-4o` |
| `TARGET_LANGUAGE` | 目标语言代码 | `en` |
| `WHISPER_RUNTIME` | ASR 运行模式 (`local`/`api`) | `local` |
| `WHISPER_MODEL` | Whisper 模型 | `large-v3` |
| `TTS_METHOD` | TTS 方法 (`azure`/`openai`/`edge`/`fish`/`gpt_sovits`) | `edge` |
| `BURN_SUBTITLES` | 是否烧录字幕 (`true`/`false`) | `true` |
| `SUBTITLE_MAX_LENGTH` | 字幕最大字符数 | `75` |

完整配置请参考 [`.env.example`](.env.example) 文件。

## 🔌 Python API

VideoVerse 提供了基于 PipelineStep 的模块化 API：

### 基础使用

```python
import asyncio
from core.pipeline import PipelineEngine, StepRegistry
from core.config import get_settings
from core.paths import paths
from core.steps import (
    create_download_step,
    create_asr_step,
    create_nlp_split_step,
)

async def main():
    # 获取配置
    settings = get_settings()

    # 创建注册表并注册步骤
    registry = StepRegistry()
    registry.register("step_01_download", create_download_step())
    registry.register("step_02_asr", create_asr_step())
    registry.register("step_03_nlp_split", create_nlp_split_step())

    # 创建流水线引擎
    engine = PipelineEngine(registry)

    # 运行流水线
    context = await engine.run(
        steps=["step_01_download", "step_02_asr", "step_03_nlp_split"],
        video_source="https://youtube.com/watch?v=xxx",
        source_language="en",
        target_language="zh",
    )

    print(f"Output: {context.get('nlp_split_result')}")

asyncio.run(main())
```

### 运行完整流水线

```python
from core.steps import (
    create_download_step, create_asr_step, create_nlp_split_step,
    create_meaning_split_step, create_summarize_step, create_translate_step,
    create_split_sub_step, create_gen_sub_step, create_burn_sub_step,
    create_audio_task_step, create_gen_audio_step, create_merge_audio_step,
    create_dubbing_step,
)

# 注册所有步骤
for name, create_func in [
    ("step_01_download", create_download_step),
    ("step_02_asr", create_asr_step),
    # ... 所有步骤
]:
    registry.register(name, create_func())

# 运行完整流水线
context = await engine.run(
    steps=[f"step_{i:02d}_{name}" for i, name in enumerate(steps, 1)],
    video_source="video.mp4",
    source_language="en",
    target_language="zh",
)
```

更多示例请参考 [`examples/run_pipeline.py`](examples/run_pipeline.py)。

## 🔌 API 支持

VideoVerse 支持 OpenAI 兼容 API 格式和多种 TTS 接口：

- **大语言模型**: `claude-3-5-sonnet`、`gpt-4o`、`deepseek-v3`、`gemini-2.0-flash`...
- **WhisperX**: 本地运行 whisperX (large-v3)
- **TTS**: `azure_tts`、`openai_tts`、`fish_tts`、`gpt_sovits`、`edge_tts`

> **提示**: VideoVerse 与 **[302.ai](https://gpt302.saaslink.net/C2oHR9)** 兼容 - 一个 API 密钥访问所有服务（LLM、WhisperX、TTS）。或者使用 Ollama 和 Edge-TTS 本地免费运行，无需 API！

## 📂 输出文件结构

```
output/
├── log/                              # 日志和中间文件
│   ├── cleaned_chunks.xlsx          # 清理后的转录文本
│   ├── split_by_nlp.txt              # NLP 分割结果
│   ├── split_by_meaning.txt          # 语义分割结果
│   ├── terminology.json              # 提取的术语表
│   ├── translation_results.xlsx      # 翻译结果
│   └── gpt_log/                      # LLM 调用日志
│
├── audio/                            # 音频处理
│   ├── raw.mp3                       # 原始音频
│   ├── vocal.mp3                     # 人声音频
│   ├── refers/                       # 参考音频
│   ├── segs/                         # TTS 生成的音频片段
│   └── tts_tasks.xlsx                # TTS 任务表
│
├── output_sub.mp4                    # 带字幕的视频
└── output_dub.mp4                    # 最终配音视频
```

## ⚠️ 当前限制

1. **WhisperX 转录性能**可能会受视频背景噪音影响，因为它使用 wav2vac 模型进行对齐。对于背景音乐较大的视频，请启用语音分离增强功能。此外，以数字或特殊字符结尾的字幕可能会被提前截断。

2. **使用较弱模型可能导致流程中的错误**，因为响应需要严格的 JSON 格式要求。如果发生此错误，请删除 `output` 文件夹并使用不同的 LLM 重试。

3. **配音功能可能无法达到 100% 完美**，由于语言之间的语速和语调差异，以及翻译步骤的影响。不过，本项目已对语速进行了大量的工程处理，以确保最佳的配音效果。

4. **多语言视频转录识别将仅保留主要语言**。这是因为 whisperX 在强制对齐词级字幕时使用单语言的专用模型，会删除无法识别的语言。

5. **目前无法分别为多个角色配音**，因为 whisperX 的说话人区分能力不够可靠。

## 🧪 测试

项目提供多种测试脚本：

### 基础测试

```bash
# 运行基础测试（不需要额外依赖）
python tests/test_basic.py
```

### 流水线验证

```bash
# 验证所有步骤
python tests/verify_pipeline.py
```

### 输出对比

```bash
# 对比新旧实现输出
python tests/compare_outputs.py --temp-dir output/temp --core-dir output/core
```

## 🏗️ 架构

流水线使用基于 PipelineStep 的模块化架构：

```
core/pipeline/
├── base.py         # PipelineStep 抽象基类
├── context.py      # PipelineContext 数据传递
├── registry.py     # StepRegistry 依赖管理
└── engine.py       # PipelineEngine 执行编排

core/steps/         # 处理步骤 (PipelineStep 实现)
├── step_XX_xxx.py  # 每个步骤独立实现
└── __init__.py     # 导出所有步骤和工厂函数
```

**核心组件**:

- **PipelineStep**: 步骤基类，定义 `name`, `dependencies`, `validate()`, `execute()`
- **PipelineContext**: 在步骤之间传递数据的上下文对象
- **StepRegistry**: 注册步骤并解析依赖关系
- **PipelineEngine**: 按依赖顺序执行步骤

**优势**:

- 清晰的依赖管理
- 独立的步骤测试
- 支持步骤跳过和重试
- 更好的错误处理

## 📚 文档

- [迁移指南](docs/MIGRATION.md) - 从旧架构迁移到新架构
- [测试文档](tests/README.md) - 测试说明

## 📄 许可证

本项目基于 Apache 2.0 许可证开源。特别感谢以下开源项目的贡献：

[whisperX](https://github.com/m-bain/whisperX)、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[json_repair](https://github.com/mangiucugna/json_repair)、[BELLE](https://github.com/LianjiaTech/BELLE)

---

<p align="center">如果你觉得 VideoVerse 有帮助，请给我一个 ⭐️！</p>
