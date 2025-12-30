"""
步骤 12: 音频合并

合并 TTS 音频片段
"""
import asyncio
import os
import subprocess
from pathlib import Path

import pandas as pd
from pydub import AudioSegment

from src.config import get_settings
from src.utils.paths import AUDIO_SEGS_DIR, AUDIO_DIR, AUDIO_TASKS
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()

DUB_VOCAL_FILE = AUDIO_DIR / "dub.mp3"
DUB_SUB_FILE = AUDIO_DIR / "dub.srt"
OUTPUT_FILE_TEMPLATE = AUDIO_SEGS_DIR / "{}.wav"


def load_and_flatten_data_sync(excel_file: str) -> tuple:
    """同步加载并展平 Excel 数据"""
    df = pd.read_excel(excel_file)

    # 处理 lines 列
    lines = []
    for line in df['lines'].tolist():
        if isinstance(line, str):
            lines.extend(eval(line))
        else:
            lines.extend(line)

    # 处理 new_sub_times 列
    new_sub_times = []
    for time in df['new_sub_times'].tolist():
        if isinstance(time, str):
            new_sub_times.extend(eval(time))
        else:
            new_sub_times.extend(time)

    return df, lines, new_sub_times


def get_audio_files_sync(df: pd.DataFrame) -> list:
    """同步生成音频文件路径列表"""
    audios = []
    for index, row in df.iterrows():
        number = row['number']
        line_count = len(eval(row['lines']) if isinstance(row['lines'], str) else row['lines'])
        for line_index in range(line_count):
            temp_file = OUTPUT_FILE_TEMPLATE / f"{number}_{line_index}.wav"
            audios.append(str(temp_file))
    return audios


def process_audio_segment_sync(audio_file: str) -> AudioSegment:
    """同步处理单个音频片段（MP3 压缩）"""
    temp_file = f"{audio_file}_temp.mp3"
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-i', audio_file,
        '-ar', '16000',
        '-ac', '1',
        '-b:a', '64k',
        temp_file
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    audio_segment = AudioSegment.from_mp3(temp_file)
    os.remove(temp_file)
    return audio_segment


async def merge_audio_segments_async(audios: list, new_sub_times: list, sample_rate: int) -> AudioSegment:
    """异步合并音频片段"""
    merged_audio = AudioSegment.silent(duration=0, frame_rate=sample_rate)

    for i, (audio_file, time_range) in enumerate(zip(audios, new_sub_times)):
        if not os.path.exists(audio_file):
            logger.warning(f"File {audio_file} does not exist, skipping...")
            continue

        audio_segment = await asyncio.to_thread(process_audio_segment_sync, audio_file)
        start_time, end_time = time_range

        # 添加静音片段
        if i > 0:
            prev_end = new_sub_times[i - 1][1]
            silence_duration = start_time - prev_end
            if silence_duration > 0:
                silence = AudioSegment.silent(
                    duration=int(silence_duration * 1000),
                    frame_rate=sample_rate
                )
                merged_audio += silence
        elif start_time > 0:
            silence = AudioSegment.silent(
                duration=int(start_time * 1000),
                frame_rate=sample_rate
            )
            merged_audio += silence

        merged_audio += audio_segment

    return merged_audio


async def create_srt_subtitle_async() -> None:
    """异步创建 SRT 字幕文件"""
    df, lines, new_sub_times = await asyncio.to_thread(load_and_flatten_data_sync, str(AUDIO_TASKS))

    with open(DUB_SUB_FILE, 'w', encoding='utf-8') as f:
        for i, ((start_time, end_time), line) in enumerate(zip(new_sub_times, lines), 1):
            start_str = f"{int(start_time // 3600):02d}:{int((start_time % 3600) // 60):02d}:{int(start_time % 60):02d},{int((start_time * 1000) % 1000):03d}"
            end_str = f"{int(end_time // 3600):02d}:{int((end_time % 3600) // 60):02d}:{int(end_time % 60):02d},{int((end_time * 1000) % 1000):03d}"

            f.write(f"{i}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{line}\n\n")

    logger.info(f"Subtitle file created: {DUB_SUB_FILE}")


async def step_12_merge_audio(audio_segments_dir: str = None) -> str:
    """
    流水线第十二步：合并音频

    Args:
        audio_segments_dir: 音频片段目录路径

    Returns:
        合并后的音频文件路径
    """
    logger.info("Starting audio merge")

    if audio_segments_dir is None:
        audio_segments_dir = str(AUDIO_SEGS_DIR)

    # 加载数据
    df, lines, new_sub_times = await asyncio.to_thread(load_and_flatten_data_sync, str(AUDIO_TASKS))
    logger.info(f"Loaded data: {len(lines)} lines")

    # 获取音频文件列表
    audios = await asyncio.to_thread(get_audio_files_sync, df)
    logger.info(f"Found {len(audios)} audio segments")

    # 生成字幕文件
    await create_srt_subtitle_async()

    # 检查第一个音频文件是否存在
    if audios and not os.path.exists(audios[0]):
        logger.warning(f"First audio file {audios[0]} does not exist, skipping merge")
        return str(DUB_VOCAL_FILE)

    sample_rate = 16000
    logger.info(f"Sample rate: {sample_rate}Hz")

    # 合并音频
    logger.info("Starting audio merge process...")
    merged_audio = await merge_audio_segments_async(audios, new_sub_times, sample_rate)

    # 导出最终音频文件
    await asyncio.to_thread(
        lambda: merged_audio
        .set_frame_rate(16000)
        .set_channels(1)
        .export(DUB_VOCAL_FILE, format="mp3", parameters=["-b:a", "64k"])
    )

    logger.info(f"Audio merge complete: {DUB_VOCAL_FILE}")
    return str(DUB_VOCAL_FILE)
