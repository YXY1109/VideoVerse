"""
步骤 09: 烧录字幕

将字幕烧录到视频中
"""
import asyncio
import subprocess
from pathlib import Path

from src.config import get_settings
from src.utils.paths import INPUT_VIDEO_FILE, OUTPUT_VIDEO_WITH_SUB
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


def burn_subtitles_sync(video_path: str, subtitle_path: str, output_path: str) -> None:
    """同步烧录字幕（使用 ffmpeg）"""
    # MoviePy 不支持异步，使用 subprocess 调用 ffmpeg
    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', f"subtitles={subtitle_path}",
        '-c:a', 'copy',
        str(output_path)
    ]
    subprocess.run(cmd, check=True)


@async_check_file_exists(OUTPUT_VIDEO_WITH_SUB)
async def step_09_burn_sub(video_path: str, subtitle_path: str) -> str:
    """
    流水线第九步：烧录字幕

    Args:
        video_path: 视频文件路径
        subtitle_path: 字幕文件路径

    Returns:
        烧录字幕后的视频路径
    """
    logger.info("Starting subtitle burning")

    # 使用 asyncio.to_thread 包装阻塞操作
    await asyncio.to_thread(
        burn_subtitles_sync,
        video_path,
        subtitle_path,
        str(OUTPUT_VIDEO_WITH_SUB)
    )

    logger.info(f"Subtitle burning complete: {OUTPUT_VIDEO_WITH_SUB}")
    return str(OUTPUT_VIDEO_WITH_SUB)
