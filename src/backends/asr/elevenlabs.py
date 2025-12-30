"""
ElevenLabs ASR 后端（异步版本）

使用 ElevenLabs API 进行语音识别
"""
import asyncio
import json
import os
import tempfile
from typing import Optional

import httpx
import librosa
import soundfile as sf

from ...config import get_settings
from ...utils.paths import LOG_DIR
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# ISO 639-2 to ISO 639-1 映射
ISO_639_2_TO_1 = {
    "eng": "en",
    "fra": "fr",
    "deu": "de",
    "ita": "it",
    "spa": "es",
    "rus": "ru",
    "kor": "ko",
    "jpn": "ja",
    "zho": "zh",
    "yue": "zh"
}

SPLIT_GAP = 1


def elev2whisper(elev_json, word_level_timestamp=False):
    """ElevenLabs 格式转换为 Whisper 格式"""
    words = elev_json.get("words", [])
    if not words:
        return {"segments": []}

    segments, seg = [], {
        "text": "",
        "start": words[0]["start"],
        "end": words[0]["end"],
        "speaker_id": words[0]["speaker_id"],
        "words": []
    }

    for prev, nxt in zip(words, words[1:] + [None]):
        seg["text"] += prev["text"]
        seg["end"] = prev["end"]
        if word_level_timestamp:
            seg["words"].append({"text": prev["text"], "start": prev["start"], "end": prev["end"]})
        if nxt is None or (nxt["start"] - prev["end"] > SPLIT_GAP) or (nxt["speaker_id"] != seg["speaker_id"]):
            seg["text"] = seg["text"].strip()
            if not word_level_timestamp:
                seg.pop("words", None)
            segments.append(seg)
            if nxt is not None:
                seg = {
                    "text": "",
                    "start": nxt["start"],
                    "end": nxt["end"],
                    "speaker_id": nxt["speaker_id"],
                    "words": []
                }
    return {"segments": segments}


async def transcribe_audio(
    raw_audio_path: str,
    vocal_audio_path: str,
    start: Optional[float] = None,
    end: Optional[float] = None,
) -> dict:
    """
    异步转录音频（ElevenLabs API）

    Args:
        raw_audio_path: 原始音频路径
        vocal_audio_path: 人声音频路径
        start: 开始时间（秒）
        end: 结束时间（秒）

    Returns:
        转录结果
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"elevenlabs_transcribe_{start}_{end}.json"

    # 检查缓存
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info(f"Processing audio transcription: {vocal_audio_path}")

    # 加载音频
    y, sr = await asyncio.to_thread(librosa.load, vocal_audio_path, sr=16000)
    audio_duration = len(y) / sr

    if start is None or end is None:
        start = 0
        end = audio_duration

    # 切片音频
    start_sample = int(start * sr)
    end_sample = int(end * sr)
    y_slice = y[start_sample:end_sample]

    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_filepath = temp_file.name
        await asyncio.to_thread(sf.write, temp_filepath, y_slice, sr, format='MP3')

    try:
        api_key = settings.elevenlabs_api_key
        base_url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": api_key}

        json_data = {
            "model_id": "scribe_v1",
            "timestamps_granularity": "word",
            "language_code": settings.whisper_language,
            "diarize": True,
            "num_speakers": None,
            "tag_audio_events": False
        }

        # 异步请求
        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(temp_filepath, 'rb') as audio_file:
                files = {"file": (os.path.basename(temp_filepath), audio_file, 'audio/mpeg')}
                response = await client.post(base_url, headers=headers, data=json_data, files=files)

        logger.info(f"API response status: {response.status_code}")
        result = response.json()

        # 保存检测到的语言
        detected_language = ISO_639_2_TO_1.get(result["language_code"], result["language_code"])
        # TODO: 更新 detected_language

        # 调整时间戳
        if start is not None and 'words' in result:
            for word in result['words']:
                if 'start' in word:
                    word['start'] += start
                if 'end' in word:
                    word['end'] += start

        parsed_result = elev2whisper(result)

        # 保存结果
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(parsed_result, f, indent=4, ensure_ascii=False)

        logger.info("Transcription completed")
        return parsed_result
    finally:
        # 清理临时文件
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
