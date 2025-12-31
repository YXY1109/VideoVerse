import asyncio
import os
import subprocess
import time
from typing import Optional

import librosa
import torch
import whisperx

from src.config import get_settings
from src.utils.paths import LOG_DIR

from loguru import logger

settings = get_settings()


# 本地实现函数
def check_hf_mirror():
    """检查最快的 HuggingFace 镜像"""
    mirrors = {'Official': 'huggingface.co', 'Mirror': 'hf-mirror.com'}
    fastest_url = f"https://{mirrors['Official']}"
    best_time = float('inf')
    logger.info("Checking HuggingFace mirrors...")
    for name, domain in mirrors.items():
        if os.name == 'nt':
            cmd = ['ping', '-n', '1', '-w', '3000', domain]
        else:
            cmd = ['ping', '-c', '1', '-W', '3', domain]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        response_time = time.time() - start
        if result.returncode == 0:
            if response_time < best_time:
                best_time = response_time
                fastest_url = f"https://{domain}"
            logger.info(f"{name}: {response_time:.2f}s")
    if best_time == float('inf'):
        logger.warning("All mirrors failed, using default")
    logger.info(f"Selected mirror: {fastest_url} ({best_time:.2f}s)")
    return fastest_url


def transcribe_audio_impl(raw_audio_file, vocal_audio_file, start, end):
    """
    WhisperX 本地转录实现（同步版本）

    此函数包含实际的 WhisperX 处理逻辑
    """
    os.environ['HF_ENDPOINT'] = check_hf_mirror()
    WHISPER_LANGUAGE = settings.whisper_language
    MODEL_DIR = settings.model_cache_dir
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Starting WhisperX using device: {device}")

    if device == "cuda":
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        batch_size = 16 if gpu_mem > 8 else 2
        compute_type = "float16" if torch.cuda.is_bf16_supported() else "int8"
        logger.info(f"GPU memory: {gpu_mem:.2f} GB, Batch size: {batch_size}, Compute type: {compute_type}")
    else:
        batch_size = 1
        compute_type = "int8"
        logger.info(f"Batch size: {batch_size}, Compute type: {compute_type}")
    logger.info(f"Starting WhisperX for segment {start:.2f}s to {end:.2f}s")

    if WHISPER_LANGUAGE == 'zh':
        model_name = "Huan69/Belle-whisper-large-v3-zh-punct-fasterwhisper"
        local_model = os.path.join(MODEL_DIR, "Belle-whisper-large-v3-zh-punct-fasterwhisper")
    else:
        model_name = settings.whisper_model
        local_model = os.path.join(MODEL_DIR, model_name)

    if os.path.exists(local_model):
        logger.info(f"Loading local WHISPER model: {local_model}")
        model_name = local_model
    else:
        logger.info(f"Using WHISPER model from HuggingFace: {model_name}")

    vad_options = {"vad_onset": 0.500, "vad_offset": 0.363}
    asr_options = {"temperatures": [0], "initial_prompt": "", }
    whisper_language = None if 'auto' in WHISPER_LANGUAGE else WHISPER_LANGUAGE
    logger.debug("You can ignore warning of `Model was trained with torch 1.10.0+cu102, yours is 2.0.0+cu118...`")
    model = whisperx.load_model(model_name, device, compute_type=compute_type, language=whisper_language,
                                vad_options=vad_options, asr_options=asr_options, download_root=MODEL_DIR)

    def load_audio_segment(audio_file, start, end):
        audio, _ = librosa.load(audio_file, sr=16000, offset=start, duration=end - start, mono=True)
        return audio

    raw_audio_segment = load_audio_segment(raw_audio_file, start, end)
    vocal_audio_segment = load_audio_segment(vocal_audio_file, start, end)

    # -------------------------
    # 1. transcribe raw audio
    # -------------------------
    transcribe_start_time = time.time()
    logger.info("Starting transcribe (you will see progress bar)...")
    result = model.transcribe(raw_audio_segment, batch_size=batch_size, print_progress=True)
    transcribe_time = time.time() - transcribe_start_time
    logger.info(f"Transcribe time: {transcribe_time:.2f}s")

    # Free GPU resources
    del model
    torch.cuda.empty_cache()

    # Note: Detected language is saved to settings in the async wrapper
    if result['language'] == 'zh' and WHISPER_LANGUAGE not in ['auto', 'zh']:
        raise ValueError("Please specify the transcription language as zh and try again!")

    # -------------------------
    # 2. align by vocal audio
    # -------------------------
    align_start_time = time.time()
    # Align timestamps using vocal audio
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, vocal_audio_segment, device,
                            return_char_alignments=False)
    align_time = time.time() - align_start_time
    logger.info(f"Align time: {align_time:.2f}s")

    # Free GPU resources again
    torch.cuda.empty_cache()
    del model_a

    # Fix encoding for Chinese text (faster-whisper bug)
    def fix_text_encoding(text: str) -> str:
        """修复 faster-whisper 输出的乱码中文"""
        if not text or any('\u4e00' <= c <= '\u9fff' for c in text):
            return text

        # 尝试常见的编码修复
        for enc in ['latin-1', 'iso-8859-1', 'cp1252', 'gbk', 'gb2312']:
            try:
                fixed = text.encode(enc).decode('utf-8')
                if any('\u4e00' <= c <= '\u9fff' for c in fixed):
                    return fixed
            except:
                continue
        return text

    # Adjust timestamps and fix encoding
    for segment in result['segments']:
        segment['start'] += start
        segment['end'] += start
        for word in segment['words']:
            if 'start' in word:
                word['start'] += start
            if 'end' in word:
                word['end'] += start
            # 修复单词文本的编码问题
            if 'word' in word:
                word['word'] = fix_text_encoding(word['word'])
    return result


async def transcribe_audio(
        raw_audio_path: str,
        vocal_audio_path: str,
        start: Optional[float] = None,
        end: Optional[float] = None,
) -> dict:
    """
    异步转录音频（本地 WhisperX）

    Args:
        raw_audio_path: 原始音频路径
        vocal_audio_path: 人声音频路径
        start: 开始时间（秒）
        end: 结束时间（秒）

    Returns:
        转录结果
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"whisperx_local_{start}_{end}.json"

    # 检查缓存
    if log_file.exists():
        import json
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # WhisperX 本地推理不支持异步，使用 asyncio.to_thread
    result = await asyncio.to_thread(
        transcribe_audio_impl, raw_audio_path, vocal_audio_path, start, end
    )

    # 保存结果
    import json
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    return result
