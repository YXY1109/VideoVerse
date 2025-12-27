# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VideoLingo is an AI-powered video translation, localization, and dubbing tool that generates Netflix-quality single-line subtitles. It processes videos through a 12-step pipeline from YouTube download through transcription, translation, subtitle generation, and final dubbing.

## Development Setup

```bash
# Environment setup (requires Python 3.10)
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py

# Run Streamlit UI
streamlit run st.py

# Docker (requires CUDA 12.4 and NVIDIA Driver >550)
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## 12-Step Pipeline Architecture

The core pipeline is implemented in `core/` with numbered modules (`_1_ytdlp.py` through `_12_dub_to_vid.py`):

**Video & Audio Processing (Steps 1-2):**
1. `_1_ytdlp.py` - YouTube video download via yt-dlp
2. `_2_asr.py` - WhisperX word-level transcription (supports local/cloud/elevenlabs backends)

**Text Processing (Steps 3-7):**
3. `_3_1_split_nlp.py` - Spacy-based NLP sentence splitting
4. `_3_2_split_meaning.py` - LLM-based semantic sentence splitting
5. `_4_1_summarize.py` - Content summarization for translation context
6. `_4_2_translate.py` - Multi-step translation (Translate-Reflect-Adaptation pattern)
7. `_5_split_sub.py` - Subtitle length optimization
8. `_6_gen_sub.py` - Timeline alignment for single-line subtitles
9. `_7_sub_into_vid.py` - Subtitle burning into video

**Dubbing Pipeline (Steps 8-12):**
10. `_8_1_audio_task.py` - Audio task generation
11. `_8_2_dub_chunks.py` - Audio chunk preparation
12. `_9_refer_audio.py` - Reference audio extraction
13. `_10_gen_audio.py` - TTS audio generation
14. `_11_merge_audio.py` - Audio merging with speed adjustment
15. `_12_dub_to_vid.py` - Final dubbing to video

## Configuration System

All settings are managed through `config.yaml` using the utility functions in `core/utils/config_utils.py`:
- `load_key(key)` - Thread-safe YAML config reading (supports dot notation like `'api.key'`)
- `update_key(key, value)` - Thread-safe YAML config writing

Key configuration sections:
- `api.*` - LLM API settings (OpenAI-compatible format)
- `whisper.*` - ASR backend configuration (local/cloud/elevenlabs)
- `tts_method` - TTS backend selection (azure_tts, openai_tts, gpt_sovits, fish_tts, edge_tts, custom_tts)
- `target_language` - Translation target (natural language description)

## LLM Integration

The `core/utils/ask_gpt.py` module provides:
- Response caching system (logs stored in `output/gpt_log/`)
- OpenAI-compatible API client
- JSON response parsing with `json_repair` for error recovery
- Exception handling with retry logic via decorator pattern

Use `ask_gpt(prompt, resp_type="json", log_title="operation_name")` for all LLM calls.

## TTS Backends

TTS implementations are in `core/tts_backend/`:
- Each TTS module exports a `{name}_tts(text, save_path)` function
- `tts_main.py` orchestrates TTS calls with retry logic and GPT text correction
- Add new TTS backends by implementing the standard interface and updating `tts_main.py`

## NLP Language Support

Spacy models are configured in `config.yaml` under `spacy_model_map`. Language-specific utilities:
- `language_split_with_space` - Languages using space as word separator
- `language_split_without_space` - Languages without space separator (zh, ja)
- `get_joiner(language)` in `config_utils.py` returns appropriate word joiner

## Batch Processing

The batch mode (`batch/` folder) processes multiple videos using `tasks_setting.xlsx`:
- Columns: Video File, Source Language, Target Language, Dubbing (0/1)
- Execute via `batch/OneKeyBatch.bat`
- Failed videos moved to `output/ERROR` with status logged to Excel

## File Structure Conventions

Intermediate files are stored in `output/` with specific naming:
- `_2_cleaned_chunks.json` - Post-transcription cleaned text
- `_3_2_split_by_meaning.txt` - Semantically split sentences
- `_5_split_for_sub.json` - Subtitle-optimized segments
- `output/log/terminology.json` - AI-extracted terminology (editable if `pause_before_translate: true`)

## Important Constraints

1. **Single-line subtitles only** - Core design principle for Netflix-quality output
2. **Translation requires strong LLMs** - Weak models may fail JSON parsing requirements
3. **No multi-speaker dubbing** - WhisperX speaker diarization is not reliable enough
4. **Main language retention** - Multilingual videos keep only the primary language
