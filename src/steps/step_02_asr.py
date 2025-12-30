"""
步骤 02: 语音识别 (ASR)

将音频转录为文本，使用 WhisperX 或其他 ASR 后端
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
from pydub import AudioSegment
from pydub.silence import detect_silence
from pydub.utils import mediainfo

from src.config import get_settings
from src.utils.paths import (
    OUTPUT_DIR,
    AUDIO_DIR,
    RAW_AUDIO_FILE,
    VOCAL_AUDIO_FILE,
    CLEANED_CHUNKS,
)
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


def normalize_audio_volume(audio_path: str, output_path: str, target_db: float = -20.0, format: str = "wav") -> str:
    """标准化音频音量"""
    audio = AudioSegment.from_file(audio_path)
    change_in_dBFS = target_db - audio.dBFS
    normalized_audio = audio.apply_gain(change_in_dBFS)
    normalized_audio.export(output_path, format=format)
    logger.info(f"Audio normalized from {audio.dBFS:.1f}dB to {target_db:.1f}dB")
    return output_path


def convert_video_to_audio_sync(video_file: str, output_path: str = RAW_AUDIO_FILE) -> None:
    """同步转换视频为音频"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(output_path):
        logger.info(f"Converting video to audio: {video_file} -> {output_path}")
        subprocess.run([
            'ffmpeg', '-y', '-i', video_file, '-vn',
            '-c:a', 'libmp3lame', '-b:a', '32k',
            '-ar', '16000',
            '-ac', '1',
            '-metadata', 'encoding=UTF-8', str(output_path)
        ], check=True, stderr=subprocess.PIPE)
        logger.info(f"Audio conversion complete: {output_path}")


def split_audio_sync(audio_file: str, target_len: float = 30 * 60, win: float = 60) -> List[Tuple[float, float]]:
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

    logger.info(f"Audio split into {len(segments)} segments")
    return segments


def fix_mojibake_text(text: str) -> str:
    """修复 faster-whisper 输出的乱码中文文本"""
    if not text:
        return text

    # 已经包含中文，直接返回
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return text

    # 尝试多种编码修复方式
    encoding_attempts = [
        ('latin-1', 'utf-8'),
        ('iso-8859-1', 'utf-8'),
        ('cp1252', 'utf-8'),
        ('gbk', 'utf-8'),
        ('gb2312', 'utf-8'),
        ('big5', 'utf-8'),
    ]

    for encode_from, decode_to in encoding_attempts:
        try:
            fixed = text.encode(encode_from).decode(decode_to)
            if any('\u4e00' <= c <= '\u9fff' for c in fixed):
                logger.info(f"Fixed encoding using {encode_from} -> {decode_to}")
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
            continue

    return text


def process_transcription(result: Dict) -> pd.DataFrame:
    """处理转录结果"""
    all_words = []
    for segment in result['segments']:
        speaker_id = segment.get('speaker_id', None)

        for word in segment['words']:
            word["word"] = fix_mojibake_text(word["word"])

            if len(word["word"]) > 30:
                logger.warning(f"Detected word longer than 30 characters, skipping: {word['word']}")
                continue

            word["word"] = word["word"].replace('»', '').replace('«', '')

            if 'start' not in word and 'end' not in word:
                if all_words:
                    word_dict = {
                        'text': word["word"],
                        'start': all_words[-1]['end'],
                        'end': all_words[-1]['end'],
                        'speaker_id': speaker_id
                    }
                    all_words.append(word_dict)
                else:
                    next_word = next((w for w in segment['words'] if 'start' in w and 'end' in w), None)
                    if next_word:
                        word_dict = {
                            'text': word["word"],
                            'start': next_word["start"],
                            'end': next_word["end"],
                            'speaker_id': speaker_id
                        }
                        all_words.append(word_dict)
                    else:
                        raise Exception(f"No next word with timestamp found: {word}")
            else:
                word_dict = {
                    'text': f'{word["word"]}',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                    'speaker_id': speaker_id
                }
                all_words.append(word_dict)

    return pd.DataFrame(all_words)


def save_results_sync(df: pd.DataFrame, output_path: str = CLEANED_CHUNKS) -> None:
    """同步保存结果"""
    os.makedirs(output_path.parent, exist_ok=True)

    initial_rows = len(df)
    df = df[df['text'].str.len() > 0]
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        logger.info(f"Removed {removed_rows} row(s) with empty text")

    long_words = df[df['text'].str.len() > 30]
    if not long_words.empty:
        logger.warning(f"Detected {len(long_words)} word(s) longer than 30 characters. Removing them.")
        df = df[df['text'].str.len() <= 30]

    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(output_path, index=False)
    logger.info(f"Results saved to {output_path}")


async def demucs_audio(input_audio: str, output_audio: str) -> None:
    """异步人声分离（Demucs）"""
    logger.info(f"Demucs vocal separation: {input_audio} -> {output_audio}")

    # 获取当前 Python 解释器路径
    python_exe = sys.executable

    # 获取输入文件名（不含扩展名）
    input_name = Path(input_audio).stem

    # Demucs 输出路径: {AUDIO_DIR}/htdemucs/{input_name}/vocals.mp3
    demucs_out_dir = AUDIO_DIR / "htdemucs" / input_name
    vocals_file = demucs_out_dir / "vocals.mp3"

    # 使用 --two-stems vocals 只分离人声，--mp3 输出 mp3 格式
    await asyncio.to_thread(
        lambda: subprocess.run([
            python_exe, '-m', 'demucs.separate',
            '-n', 'htdemucs',
            '--two-stems', 'vocals',
            '--mp3',
            '--out', str(AUDIO_DIR),
            str(input_audio)
        ], check=True)
    )

    # 移动文件到目标位置
    if vocals_file.exists():
        import shutil
        shutil.move(str(vocals_file), str(output_audio))
        # 清理 demucs 输出目录
        if demucs_out_dir.exists():
            shutil.rmtree(demucs_out_dir.parent, ignore_errors=True)
        logger.info(f"Moved {vocals_file} to {output_audio}")
    else:
        raise FileNotFoundError(f"Demucs output not found: {vocals_file}")


async def transcribe_audio(
    audio_file: str,
    vocal_audio: str,
    start: float,
    end: float,
    runtime: str
) -> Dict:
    """异步转录音频片段"""
    # 根据 runtime 选择不同的 ASR 后端
    if runtime == "local":
        from src.backends.asr import whisperx_local
        return await whisperx_local.transcribe_audio(audio_file, vocal_audio, start, end)
    elif runtime == "cloud":
        from src.backends.asr import whisperx_api
        return await whisperx_api.transcribe_audio(audio_file, vocal_audio, start, end)
    elif runtime == "elevenlabs":
        from src.backends.asr import elevenlabs
        return await elevenlabs.transcribe_audio(audio_file, vocal_audio, start, end)
    else:
        raise ValueError(f"Unknown ASR runtime: {runtime}")


@async_check_file_exists(CLEANED_CHUNKS)
async def step_02_asr(video_path: str, source_language: str = "en") -> str:
    """
    流水线第二步：语音识别

    Args:
        video_path: 视频文件路径
        source_language: 源语言代码

    Returns:
        转录结果文件路径
    """
    logger.info(f"Starting ASR for video: {video_path}")

    # 1. 转换视频为音频
    await asyncio.to_thread(convert_video_to_audio_sync, video_path)

    # 2. Demucs 人声分离
    if settings.demucs:
        await demucs_audio(str(RAW_AUDIO_FILE), str(VOCAL_AUDIO_FILE))
        vocal_audio = await asyncio.to_thread(
            normalize_audio_volume,
            str(VOCAL_AUDIO_FILE),
            str(VOCAL_AUDIO_FILE),
            format="mp3"
        )
    else:
        vocal_audio = str(RAW_AUDIO_FILE)

    # 3. 分割音频
    segments = await asyncio.to_thread(split_audio_sync, str(RAW_AUDIO_FILE))

    # 4. 转录音频片段
    runtime = settings.whisper_runtime
    logger.info(f"Transcribing with {runtime} mode")

    all_results = []
    for start, end in segments:
        result = await transcribe_audio(str(RAW_AUDIO_FILE), vocal_audio, start, end, runtime)
        all_results.append(result)

    # 5. 合并结果
    combined_result = {'segments': []}
    for result in all_results:
        combined_result['segments'].extend(result['segments'])

    # 6. 处理和保存结果
    df = process_transcription(combined_result)
    await asyncio.to_thread(save_results_sync, df)

    logger.info(f"ASR complete: {CLEANED_CHUNKS}")
    return str(CLEANED_CHUNKS)


if __name__ == '__main__':
    # 测试
    import asyncio
    video_path = "output/test_video.mp4"
    result = asyncio.run(step_02_asr(video_path))
    logger.info(f"ASR result: {result}")
