<div align="center">

# VideoVerse

# 逐帧连接世界

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

</div>

> **项目来源**: 本项目最初代码来自 [VideoLingo](https://github.com/Huanshere/VideoLingo)，感谢原作者的开源贡献。

## 🌟 项目概述

**VideoVerse** 是一个基于 AI 的视频翻译、本地化和配音工具，能够生成 Netflix 级别的高质量单行字幕。通过完整的 12 步 AI 处理流水线，实现从视频下载到最终配音的全自动化处理。

### 核心特性

- 🎥 **视频下载** - 支持 YouTube 及本地视频文件
- 🎙️ **词级语音识别** - 基于 WhisperX 的高精度 ASR，支持词级时间轴对齐
- 📝 **智能字幕分割** - NLP + AI 双重分割，保持语义完整
- 📚 **术语库管理** - AI 自动提取 + 自定义术语，确保翻译一致性
- 🔄 **三步翻译流程** - 直译 → 反思 → 意译，打造电影级翻译质量
- ✅ **Netflix 标准** - 严格单行字幕，最长 75 字符
- 🗣️ **多 TTS 支持** - 9 种配音后端（GPT-SoVITS、Azure、OpenAI 等）
- 🚀 **Streamlit UI** - 一键启动，支持 7 种界面语言
- 📦 **批处理模式** - 支持批量处理多个视频
- 🔄 **断点续传** - 详细日志记录，支持从任意步骤恢复

### 与同类项目的区别

**仅使用单行字幕、卓越的翻译质量、无缝的配音体验、高度模块化的 12 步流水线架构**

## 🏗️ 12 步处理流水线

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
│  │ ⑥ 多步翻译   │ →  │ ⑦ 字幕分割   │ →  │ ⑧ 时间轴对齐  │             │
│  │ (直译-反思-意译)│               │    │             │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                        ┌─────────────┐             │
│                                        │ ⑨ 字幕烧录   │ → 带字幕视频  │
│                                        └─────────────┘             │
│                                                                     │
│  配音处理                                                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ ⑩ 音频任务   │ →  │ ⑪ TTS生成   │ →  │ ⑫ 音频合成   │ → 配音视频  │
│  └─────────────┘    │ (9种后端)   │    └─────────────┘             │
│                     └─────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
VideoVerse/
├── st.py                      # Streamlit 主入口
├── config.yaml                # 主配置文件
├── pyproject.toml             # 项目依赖
│
├── core/                      # 核心处理模块（12步流水线）
│   ├── _1_ytdlp.py           # ① YouTube 视频下载
│   ├── _2_asr.py             # ② WhisperX 语音识别
│   ├── _3_1_split_nlp.py     # ③ NLP 句子分割
│   ├── _3_2_split_meaning.py # ④ AI 语义分割
│   ├── _4_1_summarize.py     # ⑤ 内容摘要 + 术语提取
│   ├── _4_2_translate.py     # ⑥ 多步翻译
│   ├── _5_split_sub.py       # ⑦ 字幕长度优化
│   ├── _6_gen_sub.py         # ⑧ 字幕时间轴对齐
│   ├── _7_sub_into_vid.py    # ⑨ 字幕烧录
│   ├── _8_1_audio_task.py    # ⑩ 音频任务生成
│   ├── _10_gen_audio.py      # ⑪ TTS 音频生成
│   ├── _11_merge_audio.py    # ⑫ 音频合并
│   ├── _12_dub_to_vid.py     # ⑫ 最终配音合成
│   │
│   ├── asr_backend/          # ASR 后端（3种）
│   │   ├── whisperX_local.py    # WhisperX 本地
│   │   ├── whisperX_302.py      # WhisperX 302.ai
│   │   └── elevenlabs_asr.py    # ElevenLabs ASR
│   │
│   ├── tts_backend/          # TTS 后端（9种）
│   │   ├── azure_tts.py          # Azure TTS
│   │   ├── openai_tts.py         # OpenAI TTS
│   │   ├── edge_tts.py           # Edge TTS
│   │   ├── fish_tts.py           # Fish TTS
│   │   ├── gpt_sovits_tts.py     # GPT-SoVITS
│   │   ├── sf_cosyvoice2.py      # CosyVoice2
│   │   └── custom_tts.py         # 自定义 TTS
│   │
│   ├── spacy_utils/          # NLP 工具
│   ├── st_utils/             # Streamlit UI 工具
│   └── utils/                # 核心工具函数
│       ├── ask_gpt.py        # LLM API 调用
│       └── config_utils.py   # 配置管理
│
├── batch/                     # 批处理模块
│   ├── OneKeyBatch.bat       # 一键批处理脚本
│   ├── tasks_setting.xlsx    # 批处理任务配置
│   └── README.zh.md          # 批处理使用说明
│
└── translations/              # 多语言翻译（已弃用）
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

### UI 界面语言（7种）

🇨🇳 简体中文 | 🇬🇧 英语 | 🇭🇰 繁体中文 | 🇯🇵 日语 | 🇪🇸 西班牙语 | 🇷🇺 俄语 | 🇫🇷 法语

### 输入语言支持（8种）

🇺🇸 英语 🤩 | 🇷🇺 俄语 😊 | 🇫🇷 法语 🤩 | 🇩🇪 德语 🤩 | 🇮🇹 意大利语 🤩 | 🇪🇸 西班牙语 🤩 | 🇯🇵 日语 😐 | 🇨🇳 中文* 😊

> *中文使用独立的增强标点 whisper 模型

**翻译支持所有语言，配音语言取决于所选的 TTS 方法。**

## 🛠️ 技术栈

### 核心
- **Python 3.10+** - 基础运行环境
- **Streamlit 1.52** - Web UI 框架

### AI / ML
- **WhisperX 3.7** - 词级语音识别与强制对齐
- **Spacy 3.7** - NLP 自然语言处理
- **Transformers 4.48** - HuggingFace 模型支持
- **PyTorch 2.1** - 深度学习框架

### 音视频处理
- **MoviePy 1.0** - 视频编辑
- **Librosa 0.10** - 音频分析
- **Pydub 0.25** - 音频处理
- **OpenCV 4.10** - 图像处理
- **PyAV 15.1** - 音视频编解码
- **yt-dlp** - YouTube 视频下载

### LLM 集成
- **OpenAI 1.55** - LLM API 客户端（兼容格式）
- **json-repair** - JSON 响应自动修复

### TTS 后端（9种）

1. **Azure TTS** - 微软 Azure 文本转语音
2. **OpenAI TTS** - OpenAI 文本转语音
3. **Fish TTS** - 开源高质量 TTS
4. **SiliconFlow FishTTS** - SiliconFlow 托管版本
5. **GPT-SoVITS** - 声音克隆 TTS
6. **Edge TTS** - Microsoft Edge 免费TTS
7. **CosyVoice2** - 阿里开源 TTS
8. **F5TTS** - 高质量 TTS
9. **自定义 TTS** - 可扩展接口

### ASR 后端（3种）

1. **WhisperX 本地** - large-v3 模型本地运行
2. **WhisperX 302.ai** - 云端 API
3. **ElevenLabs ASR** - 商业 ASR 服务

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

# 2. 使用 uv 初始化项目（Python 3.10）
uv init -p 3.10
uv sync

# 3. 安装 PyTorch（CUDA 11.8 版本）
uv pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118

# 4. 安装 demucs（音频分离）
uv pip install git+https://github.com/adefossez/demucs.git

# 5. 安装 numpy
uv pip install numpy==1.26.4
```

### 启动应用

```bash
streamlit run st.py
```

## ⚙️ 配置说明

主要配置文件为 `config.yaml`，关键配置项：

```yaml
# LLM API 配置
api:
  key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4.1"

# 翻译目标语言（自然语言描述）
target_language: "中文（简体）"

# WhisperX 设置
whisper:
  model: "large-v3"        # 模型选择
  language: "auto"         # 识别语言
  runtime: "local"         # local/302/elevenlabs

# 字幕设置
subtitle:
  max_length: 75           # 每行最大字符数
  target_multiplier: 1.2   # 目标语言长度倍数

# 配音设置
tts_method: "azure_tts"    # TTS 方法选择
speed_factor:              # 音频速度范围 [1.0, 1.4]
```

完整配置说明请参考 [config.yaml](./config.yaml) 文件。

## 🔌 API 支持

VideoVerse 支持 OpenAI 兼容 API 格式和多种 TTS 接口：

- **大语言模型**: `claude-3-5-sonnet`、`gpt-4.1`、`deepseek-v3`、`gemini-2.0-flash`...（按性能排序）
- **WhisperX**: 本地运行 whisperX (large-v3) 或使用 302.ai API
- **TTS**: `azure_tts`、`openai_tts`、`fish_tts`、`gpt_sovits`、`edge_tts`、`custom_tts` 等

> **提示**: VideoVerse 与 **[302.ai](https://gpt302.saaslink.net/C2oHR9)** 兼容 - 一个 API 密钥访问所有服务（LLM、WhisperX、TTS）。或者使用 Ollama 和 Edge-TTS 本地免费运行，无需 API！

## 📦 批处理模式

批处理模式支持批量处理多个视频：

1. 编辑 `batch/tasks_setting.xlsx` 配置文件
   - `Video File`: YouTube 链接或本地文件路径
   - `Source Language`: 源语言
   - `Target Language`: 目标语言
   - `Dubbing`: 是否配音（0/1）

2. 运行批处理脚本
   ```bash
   # Windows
   batch\OneKeyBatch.bat
   ```

3. 查看处理结果
   - 成功：输出文件在 `output/` 目录
   - 失败：文件移至 `output/ERROR/`，状态记录回 Excel

详细说明请参考 [批处理文档](./batch/README.zh.md)。

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
├── output_dub.mp4                    # 最终配音视频
└── ERROR/                            # 失败的任务
```

## ⚠️ 当前限制

1. **WhisperX 转录性能**可能会受视频背景噪音影响，因为它使用 wav2vac 模型进行对齐。对于背景音乐较大的视频，请启用语音分离增强功能。此外，以数字或特殊字符结尾的字幕可能会被提前截断。

2. **使用较弱模型可能导致流程中的错误**，因为响应需要严格的 JSON 格式要求。如果发生此错误，请删除 `output` 文件夹并使用不同的 LLM 重试。

3. **配音功能可能无法达到 100% 完美**，由于语言之间的语速和语调差异，以及翻译步骤的影响。不过，本项目已对语速进行了大量的工程处理，以确保最佳的配音效果。

4. **多语言视频转录识别将仅保留主要语言**。这是因为 whisperX 在强制对齐词级字幕时使用单语言的专用模型，会删除无法识别的语言。

5. **目前无法分别为多个角色配音**，因为 whisperX 的说话人区分能力不够可靠。

## 📄 许可证

本项目基于 Apache 2.0 许可证开源。特别感谢以下开源项目的贡献：

[whisperX](https://github.com/m-bain/whisperX)、[yt-dlp](https://github.com/yt-dlp/yt-dlp)、[json_repair](https://github.com/mangiucugna/json_repair)、[BELLE](https://github.com/LianjiaTech/BELLE)

---

<p align="center">如果你觉得 VideoVerse 有帮助，请给我一个 ⭐️！</p>
