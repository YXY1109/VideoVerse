import asyncio
import io
import json
from typing import Optional

import httpx
import librosa
import soundfile as sf

from src.config import get_settings
from src.utils.paths import LOG_DIR

from loguru import logger
settings = get_settings()


async def transcribe_audio(
        raw_audio_path: str,
        vocal_audio_path: str,
        start: Optional[float] = None,
        end: Optional[float] = None,
) -> dict:
    """
    异步转录音频（302 WhisperX API）

    Args:
        raw_audio_path: 原始音频路径
        vocal_audio_path: 人声音频路径
        start: 开始时间（秒）
        end: 结束时间（秒）

    Returns:
        转录结果
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"whisperx302_{start}_{end}.json"

    # 检查缓存
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    language = settings.whisper_language
    url = "https://api.302.ai/302/whisperx"

    # 使用 asyncio.to_thread 处理音频加载
    y, sr = await asyncio.to_thread(librosa.load, vocal_audio_path, sr=16000)
    audio_duration = len(y) / sr

    if start is None or end is None:
        start = 0
        end = audio_duration

    start_sample = int(start * sr)
    end_sample = int(end * sr)
    y_slice = y[start_sample:end_sample]

    # 准备音频数据
    audio_buffer = io.BytesIO()
    await asyncio.to_thread(sf.write, audio_buffer, y_slice, sr, format='WAV', subtype='PCM_16')
    audio_buffer.seek(0)

    files = {'audio_input': ('audio_slice.wav', audio_buffer, 'application/octet-stream')}
    data = {"processing_type": "align", "language": language, "output": "raw"}

    logger.info(f"Transcribing audio with language: {language}...")

    # 使用 httpx 异步请求
    async with httpx.AsyncClient(timeout=300.0) as client:
        headers = {'Authorization': f'Bearer {settings.whisperx_302_api_key}'}
        response = await client.post(url, headers=headers, data=data, files=files)

    response_json = response.json()

    # 更新检测到的语言
    if 'language' in response_json:
        # TODO: 更新 detected_language 到配置
        pass

    # 调整时间戳
    if start is not None:
        for segment in response_json.get('segments', []):
            segment['start'] += start
            segment['end'] += start
            for word in segment.get('words', []):
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start

    # 保存结果
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=4, ensure_ascii=False)

    logger.info(f"Transcription completed")
    return response_json
