"""
步骤 12: 音频合并

合并 TTS 音频片段
"""
import asyncio
import subprocess
from pathlib import Path

from ..config import get_settings
from ..utils.paths import AUDIO_SEGS_DIR, AUDIO_DIR
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def merge_audio_sync(audio_dir: Path, output_file: Path) -> None:
    """同步合并音频（使用 ffmpeg）"""
    # 使用 ffmpeg 合并音频
    # TODO: 实现完整的音频合并逻辑
    pass


async def step_12_merge_audio(audio_segments_dir: str) -> str:
    """
    流水线第十二步：合并音频

    Args:
        audio_segments_dir: 音频片段目录路径

    Returns:
        合并后的音频文件路径
    """
    logger.info("Starting audio merge")

    output_file = AUDIO_DIR / "merged_audio.wav"

    # 使用 asyncio.to_thread 包装阻塞操作
    await asyncio.to_thread(
        merge_audio_sync,
        Path(audio_segments_dir),
        output_file
    )

    logger.info(f"Audio merge complete: {output_file}")
    return str(output_file)
