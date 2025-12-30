"""
步骤 11: TTS 音频生成

使用 TTS 后端生成配音音频
"""
import asyncio
import os
import soundfile as sf
from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.utils.paths import AUDIO_SEGS_DIR, AUDIO_REFERS_DIR, AUDIO_TASKS, VOCAL_AUDIO_FILE
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


def time_to_samples(time_str: str, sr: int) -> int:
    """统一时间转换函数"""
    h, m, s = time_str.split(':')
    s, ms = s.split(',') if ',' in s else (s, '0')
    seconds = int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
    return int(seconds * sr)


def extract_audio_sync(audio_data, sr: int, start_time: str, end_time: str, out_file: Path) -> None:
    """同步提取音频片段"""
    start = time_to_samples(start_time, sr)
    end = time_to_samples(end_time, sr)
    sf.write(out_file, audio_data[start:end], sr)


async def generate_refer_audio_async(df: pd.DataFrame, vocal_audio_file: Path, refers_dir: Path) -> None:
    """异步生成参考音频片段"""
    # 确保输出目录存在
    refers_dir.mkdir(parents=True, exist_ok=True)

    # 读取音频数据
    data, sr = await asyncio.to_thread(sf.read, vocal_audio_file)

    # 并发提取所有音频片段
    tasks = []
    for _, row in df.iterrows():
        out_file = refers_dir / f"{row['number']}.wav"
        task = asyncio.to_thread(
            extract_audio_sync,
            data, sr,
            row['start_time'],
            row['end_time'],
            out_file
        )
        tasks.append(task)

    await asyncio.gather(*tasks)
    logger.info(f"Generated {len(tasks)} reference audio segments in {refers_dir}")


async def generate_tts_audio_async(text: str, index: int, refer_audio: Path = None) -> tuple:
    """异步生成单条 TTS 音频"""
    tts_method = settings.tts_method.lower()

    # 根据 TTS 方法选择相应的后端
    if tts_method == 'azure':
        from src.backends.tts.azure_tts import azure_tts_sync
        output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
        await asyncio.to_thread(azure_tts_sync, text, str(output_file))
        return index, str(output_file)

    elif tts_method == 'openai':
        from src.backends.tts.openai_tts import openai_tts_sync
        output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
        await asyncio.to_thread(openai_tts_sync, text, str(output_file))
        return index, str(output_file)

    elif tts_method == 'edge':
        from src.backends.tts.edge_tts import edge_tts_sync
        output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
        await asyncio.to_thread(edge_tts_sync, text, str(output_file))
        return index, str(output_file)

    elif tts_method == 'fish':
        from src.backends.tts.fish_tts import fish_tts_sync
        output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
        await asyncio.to_thread(fish_tts_sync, text, str(output_file), refer_audio)
        return index, str(output_file)

    elif tts_method == 'gpt_sovits':
        from src.backends.tts.gpt_sovits_tts import gpt_sovits_tts_sync
        output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
        await asyncio.to_thread(gpt_sovits_tts_sync, text, str(output_file), refer_audio)
        return index, str(output_file)

    else:
        raise ValueError(f"Unsupported TTS method: {tts_method}")


async def step_11_gen_audio(audio_tasks_file: str = None) -> str:
    """
    流水线第十一步：生成 TTS 音频

    Args:
        audio_tasks_file: 音频任务文件路径

    Returns:
        音频输出目录路径
    """
    logger.info("Starting TTS audio generation")

    if audio_tasks_file is None:
        audio_tasks_file = str(AUDIO_TASKS)

    # 确保输出目录存在
    AUDIO_SEGS_DIR.mkdir(parents=True, exist_ok=True)

    # 检查是否需要先生成参考音频
    if not os.path.exists(AUDIO_REFERS_DIR) or not list(AUDIO_REFERS_DIR.glob('*.wav')):
        logger.info("Generating reference audio segments...")

        # 读取音频任务
        df = await asyncio.to_thread(pd.read_excel, audio_tasks_file)

        # 先确保人声音频存在
        if VOCAL_AUDIO_FILE.exists():
            await generate_refer_audio_async(df, VOCAL_AUDIO_FILE, AUDIO_REFERS_DIR)
        else:
            logger.warning(f"Vocal audio file not found: {VOCAL_AUDIO_FILE}")

    # 读取音频任务
    df = await asyncio.to_thread(pd.read_excel, audio_tasks_file)

    # 检查是否已存在所有音频片段
    existing_segs = len(list(AUDIO_SEGS_DIR.glob('seg_*.wav')))
    if existing_segs >= len(df):
        logger.info(f"Audio segments already exist ({existing_segs} files), skipping generation")
        return str(AUDIO_SEGS_DIR)

    # 生成 TTS 音频
    tasks = []
    for _, row in df.iterrows():
        refer_audio = AUDIO_REFERS_DIR / f"{row['number']}.wav"
        if refer_audio.exists():
            task = generate_tts_audio_async(row['text'], row['number'], refer_audio)
        else:
            task = generate_tts_audio_async(row['text'], row['number'], None)
        tasks.append(task)

    # 使用信号量限制并发数
    semaphore = asyncio.Semaphore(settings.max_workers)

    async def bounded_task(task):
        async with semaphore:
            return await task

    bounded_tasks = [bounded_task(task) for task in tasks]
    results = await asyncio.gather(*bounded_tasks)

    logger.info(f"Generated {len(results)} audio segments")
    logger.info(f"TTS audio generation complete: {AUDIO_SEGS_DIR}")
    return str(AUDIO_SEGS_DIR)
