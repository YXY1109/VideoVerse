# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

VideoVerse 是一个基于 AI 的视频翻译和配音工具，使用 13 步异步处理流水线从 YouTube 或本地视频生成带字幕和配音的视频。

### 核心技术栈
- **Python 3.10-3.12** (uv 包管理)
- **异步架构**: httpx + asyncio + aiocache
- **AI/ML**: WhisperX 3.2 (词级ASR), Spacy 3.7 (NLP), PyTorch 2.1 (CUDA 11.8)
- **配置管理**: pydantic-settings + 环境变量
- **视频处理**: MoviePy, Librosa, PyAV

### 常用命令

```bash
# 安装依赖
uv sync

# 运行 API (异步调用)
python -c "import asyncio; from videoverse.api import process_video_async; asyncio.run(process_video_async('video_url', 'en', 'zh'))"

# 运行 API (同步调用)
python -c "from videoverse import process_video; process_video('video_url', 'en', 'zh')"
```

### 环境变量配置

项目使用 `.env` 文件配置，通过 `pydantic-settings` 加载 (见 `src/config.py`)。最小配置：

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

### 13 步异步流水线架构

```
src/
├── pipeline.py           # 主流水线 (run_pipeline)
├── api.py                # Python API 接口
├── config.py             # pydantic-settings 配置
│
├── steps/                # 13 个处理步骤 (每个文件包含 step_XX_xxx 函数)
│   ├── 01_download.py    # YouTube 下载 (yt-dlp)
│   ├── 02_asr.py         # 语音识别 (WhisperX 词级时间轴)
│   ├── 03_nlp_split.py   # NLP 分割 (Spacy)
│   ├── 04_meaning_split.py # AI 语义分割
│   ├── 05_summarize.py   # 摘要 + 术语提取
│   ├── 06_translate.py   # 多步翻译 (直译→反思→意译)
│   ├── 07_split_sub.py   # 字幕长度优化
│   ├── 08_gen_sub.py     # 字幕时间轴对齐
│   ├── 09_burn_sub.py    # 字幕烧录
│   ├── 10_audio_task.py  # 音频任务生成
│   ├── 11_gen_audio.py   # TTS 音频生成
│   ├── 12_merge_audio.py # 音频合并
│   └── 13_dubbing.py     # 最终配音合成
│
├── backends/             # ASR/TTS 后端 (策略模式)
│   ├── asr/              # ASR: whisperx_local, whisperx_api, elevenlabs
│   └── tts/              # TTS: azure, openai, edge, fish, gpt_sovits
│
├── tools/                # 工具模块
│   ├── prompts.py        # AI Prompt 模板
│   ├── translate_lines.py # 三步翻译逻辑
│   └── spacy_utils/      # NLP 分割工具
│
└── utils/                # 核心工具
    ├── llm.py            # 异步 LLM API (OpenAI 兼容)
    ├── http.py           # 异步 HTTP 客户端
    ├── cache.py          # 异步缓存
    ├── decorators.py     # 装饰器 (@async_check_file_exists, @async_except_handler)
    ├── paths.py          # 路径常量
    └── common.py         # 通用工具
```

### 架构要点

1. **异步优先**: 所有 I/O 操作使用异步 (`asyncio`, `httpx`, `AsyncOpenAI`)
2. **策略模式**: ASR/TTS 后端可通过 `TTS_METHOD`/`WHISPER_RUNTIME` 环境变量切换
3. **缓存机制**: LLM 调用结果缓存 (`utils/cache.py`)，支持断点续传
4. **装饰器**: `@async_check_file_exists` 跳过已存在文件，`@async_except_handler` 自动重试
5. **配置驱动**: 使用 `pydantic-settings` 从环境变量加载配置，`get_settings()` 获取单例

### 语言检测与分割

- **中文**: 使用 jieba 分词，`whisper_language=zh` 时使用 Belle-whisper-large-v3-zh-punct-fasterwhisper 模型
- **其他语言**: 使用对应 Spacy 模型 (`en_core_web_md` 等)，见 `config.py` 中的 `spacy_model_map`

### LLM 提示词管理

所有 AI Prompt 模板在 `src/tools/prompts.py` 中定义：
- `get_split_prompt()` - 语义分割
- `get_summary_prompt()` - 摘要和术语提取
- `get_prompt_faithfulness()` - 直译
- `get_prompt_expressiveness()` - 意译
- `get_align_prompt()` - 字幕对齐

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

1. **中文编码**: WhisperX faster-whisper 存在中文乱码 bug，在 `whisperx_local.py:transcribe_audio_impl()` 中有修复逻辑
2. **GPU 内存**: WhisperX 根据 GPU 内存自动调整 batch_size (8GB+ 用 16，否则用 2)
3. **HuggingFace 镜像**: 自动检测最快的 HF 镜像 (官方 / hf-mirror.com)
4. **字幕格式**: 严格单行字幕，最长 75 字符 (Netflix 标准)
5. **配音速度**: 使用 `speed_factor_min/accept/max` 控制配音速度调整

### 依赖说明

- PyTorch 使用 CUDA 11.8 版本，通过 `[tool.uv.sources]` 从 PyTorch index 安装
- Demucs 和 Spacy 模型使用本地路径 (`files/` 目录)
- 某些包使用 override dependencies (av>=13.0.0, tokenizers)
