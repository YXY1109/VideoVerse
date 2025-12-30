"""
步骤 13: 配音合成

将配音音频与视频合成
"""
import asyncio
import subprocess
from pathlib import Path

from src.config import get_settings
from src.utils.paths import INPUT_VIDEO_FILE, OUTPUT_VIDEO_DUBBED

from loguru import logger
settings = get_settings()


def merge_video_audio_sync(video_path: str, audio_path: str, output_path: str) -> None:
    """同步合成视频和音频（使用 ffmpeg）"""
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        str(output_path)
    ]
    subprocess.run(cmd, check=True)


async def step_13_dubbing(video_path: str, dubbed_audio_path: str) -> str:
    """
    流水线第十三步：配音合成

    Args:
        video_path: 原视频文件路径
        dubbed_audio_path: 配音音频文件路径

    Returns:
        配音后的视频文件路径
    """
    logger.info("Starting video dubbing")

    # 使用 asyncio.to_thread 包装阻塞操作
    await asyncio.to_thread(
        merge_video_audio_sync,
        video_path,
        dubbed_audio_path,
        str(OUTPUT_VIDEO_DUBBED)
    )

    logger.info(f"Video dubbing complete: {OUTPUT_VIDEO_DUBBED}")
    return str(OUTPUT_VIDEO_DUBBED)
