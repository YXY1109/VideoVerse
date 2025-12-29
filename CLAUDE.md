# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**VideoVerse** 是一个基于 AI 的视频翻译、本地化和配音工具，fork 自 [VideoLingo](https://github.com/Huanshere/VideoLingo)。它实现了一个 12 步的 AI 处理流水线，用于自动化视频翻译和配音，生成 Netflix 级别的高质量单行字幕。

## 核心架构

### 12 步处理流水线

项目采用模块化流水线架构，每一步独立运行，通过中间文件传递数据：

```
core/_1_ytdlp.py          # ① YouTube 视频下载
core/_2_asr.py            # ② WhisperX 词级 ASR + 时间轴对齐
core/_3_1_split_nlp.py    # ③ NLP 句子分割 (Spacy)
core/_3_2_split_meaning.py # ④ AI 语义分割
core/_4_1_summarize.py    # ⑤ 内容摘要 + 术语提取
core/_4_2_translate.py    # ⑥ 多步翻译 (直译 → 反思 → 意译)
core/_5_split_sub.py      # ⑦ 字幕长度优化 (最长 75 字符)
core/_6_gen_sub.py        # ⑧ 时间轴对齐
core/_7_sub_into_vid.py   # ⑨ 字幕烧录
core/_8_1_audio_task.py   # ⑩ 音频任务生成
core/_10_gen_audio.py     # ⑪ TTS 音频生成
core/_11_merge_audio.py   # ⑫ 音频合并
core/_12_dub_to_vid.py    # ⑫ 最终配音合成
```

### 架构设计模式

- **管道模式**: 每步独立处理，通过 `output/log/` 中的文件通信
- **策略模式**: ASR (`core/asr_backend/`) 和 TTS (`core/tts_backend/`) 支持多种后端
- **装饰器模式**: `core/utils/decorator.py` 中的 `@check_file_exists` 实现断点续传
- **配置驱动**: 所有设置集中在 `config.yaml`

### 模块组织

```
core/
├── asr_backend/          # ASR 后端: whisperX_local, whisperX_302, elevenlabs_asr
├── tts_backend/          # TTS 后端: azure, openai, fish, gpt_sovits, edge, cosyvoice2, f5tts, custom
├── spacy_utils/          # NLP 分割工具
├── st_utils/             # Streamlit UI 组件
├── utils/
│   ├── ask_gpt.py        # LLM API 调用 (OpenAI 兼容)
│   ├── config_utils.py   # 线程安全的 load_key()/update_key()
│   ├── decorator.py      # @except_handler, @check_file_exists
│   └── models.py         # 文件路径定义
├── prompts.py            # AI Prompt 模板
└── translate_lines.py    # 三步翻译逻辑
```

## 常用开发命令

### 环境配置

```bash
# 使用 uv 安装依赖 (Python 3.10-3.12)
uv sync

# PyTorch 使用 CUDA 11.8 索引 (在 pyproject.toml 中配置)
```

### 运行应用

```bash
# Streamlit UI 模式 (主入口)
streamlit run main.py

# 批处理模式
python batch/utils/batch_processor.py
# Windows 系统:
batch\OneKeyBatch.bat
```

### 配置管理

- 所有配置在 `config.yaml`
- 使用 `core.utils.config_utils` 中的 `load_key("path.to.key")` 和 `update_key("path.to.key", value)`
- 支持嵌套键: `load_key("api.model")`
- 配置操作是线程安全的

## 重要实现说明

### 断点续传能力

每个流水线步骤使用 `@check_file_exists(file_path)` 装饰器。如果输出文件已存在，该步骤会被跳过。要重新运行某步骤，删除 `output/log/` 中对应的输出文件。

### AI Prompts

所有 Prompt 集中在 `core/prompts.py`。遵循现有模式保持一致性。项目使用三步翻译流程：
1. 直译 (Literal translation)
2. 反思 (Reflection - 自我修正)
3. 意译 (Free translation - 润色)

### LLM 集成

使用 `core/utils/ask_gpt.py` 进行 OpenAI 兼容的 API 调用。在 `config.yaml` 中配置：
```yaml
api:
  key: 'your-api-key'
  base_url: 'https://api.openai.com/v1'  # 或兼容端点
  model: 'gpt-4o'
  llm_support_json: true
  max_tokens: 8192
```

### 添加新的 TTS/ASR 后端

1. 在 `core/tts_backend/` 或 `core/asr_backend/` 中创建新文件
2. 遵循现有接口模式 (如 `azure_tts.py`, `whisperX_local.py`)
3. 在 UI 配置中更新 `tts_method` 选项

### 批处理模式

任务在 `batch/tasks_setting.xlsx` 中定义：
- `Video File`: YouTube URL 或本地文件名
- `Source Language`: 源语言代码
- `Target Language`: 自然语言描述
- `Dubbing`: 0 不配音, 1 配音

失败的任务移至 `output/ERROR/`，状态记录回 Excel。

## 文件路径约定

- 输出文件: `output/` 目录
- 中间日志: `output/log/`
- 音频: `output/audio/`
- 模型缓存: `_model_cache/` (通过 `model_dir` 配置)
- 参考音频: `output/audio/refers/`

## 依赖

主要依赖 (见 `pyproject.toml`):
- **Python**: 3.10-3.12
- **Streamlit**: 1.52.2 (Web UI)
- **WhisperX**: 3.2.0 (带对齐的 ASR)
- **Spacy**: 3.7.4 (NLP)
- **PyTorch**: 2.1.2 with CUDA 11.8
- **MoviePy**: 1.0.3 (视频编辑)
- **OpenAI**: 1.55.3 (LLM 客户端)

### 本地依赖

- `files/demucs-main/` - Demucs 人声分离
- `files/en_core_web_md-3.7.1-py3-none-any.whl` - Spacy 英语模型

## 语言支持

### 输入语言 (8 种)
英语 (最佳)、俄语、法语、德语、意大利语、西班牙语、日语、中文 (使用增强模型)

### UI 语言 (7 种)
zh-CN, en, zh-HK, ja, es, ru, fr (通过 `display_language` 配置)

## 代码风格说明

- 使用从项目根目录开始的绝对导入: `from core.utils import load_key`
- `core/utils/decorator.py` 中的装饰器用于重试和文件检查
- 配置操作需要线程安全 (使用 `threading.Lock`)
- `core/prompts.py` 中的 Prompt 使用 load_key() 动态插入语言
