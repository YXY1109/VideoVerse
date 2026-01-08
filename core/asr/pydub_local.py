import os
from typing import Tuple, List

from loguru import logger
from pydub import AudioSegment
from pydub.silence import detect_silence
from pydub.utils import mediainfo


def normalize_audio_volume(audio_path: str, target_db: float = -20.0) -> str:
    """标准化音频音量"""
    name, ext = os.path.splitext(audio_path)
    output_path = name + "_normalized" + ext
    if os.path.exists(output_path):
        logger.warning(f"Normalized audio already exists: {output_path}")
        return output_path

    audio = AudioSegment.from_file(audio_path)
    change_in_dbfs = target_db - audio.dBFS
    normalized_audio = audio.apply_gain(change_in_dbfs)
    normalized_audio.export(output_path, format=ext[1:])
    logger.success(f"Audio normalized from {audio.dBFS:.1f}dB to {target_db:.1f}dB")
    return output_path


def split_audio(audio_file: str, target_len: float = 30 * 60, win: float = 60) -> List[Tuple[float, float]]:
    """同步分割音频"""
    logger.info(f"Splitting audio: {audio_file}")
    audio = AudioSegment.from_file(audio_file)
    duration = float(mediainfo(audio_file)["duration"])
    if duration <= target_len + win:
        return [(0, duration)]

    segments, pos = [], 0.0
    safe_margin = 0.5

    while pos < duration:
        if duration - pos <= target_len:
            segments.append((pos, duration))
            break

        threshold = pos + target_len
        ws, we = int((threshold - win) * 1000), int((threshold + win) * 1000)

        silence_regions = detect_silence(audio[ws:we], min_silence_len=int(safe_margin * 1000), silence_thresh=-30)
        silence_regions = [(s / 1000 + (threshold - win), e / 1000 + (threshold - win)) for s, e in silence_regions]
        valid_regions = [
            (start, end) for start, end in silence_regions
            if (end - start) >= (safe_margin * 2) and threshold <= start + safe_margin <= threshold + win
        ]

        if valid_regions:
            start, end = valid_regions[0]
            split_at = start + safe_margin
        else:
            logger.warning(f"No valid silence regions found at {threshold}s, using threshold")
            split_at = threshold

        segments.append((pos, split_at))
        pos = split_at

    logger.success(f"Audio split into {len(segments)} segments")
    return segments
