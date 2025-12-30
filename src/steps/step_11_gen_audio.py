"""
步骤 11: TTS 音频生成

使用 TTS 后端生成配音音频
"""
import asyncio
from pathlib import Path

from src.config import get_settings
from src.utils.paths import AUDIO_SEGS_DIR
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


async def generate_tts_audio_async(text: str, voice: str, index: int) -> tuple[int, str]:
    """异步生成单条 TTS 音频"""
    # TODO: 根据 settings.tts_method 选择不同的 TTS 后端
    # - azure: 从 core/tts_backend/azure_tts.py 迁移
    # - openai: 从 core/tts_backend/openai_tts.py 迁移
    # - edge: 从 core/tts_backend/edge_tts.py 迁移
    # - fish: 从 core/tts_backend/fish_tts.py 迁移
    # 等等

    # 简化版实现
    logger.info(f"Generating TTS audio {index}: {text[:30]}...")
    await asyncio.sleep(0.1)  # 模拟异步操作

    output_file = AUDIO_SEGS_DIR / f"seg_{index}.wav"
    return index, str(output_file)


async def step_11_gen_audio(audio_tasks_file: str) -> str:
    """
    流水线第十一步：生成 TTS 音频

    Args:
        audio_tasks_file: 音频任务文件路径

    Returns:
        音频输出目录路径
    """
    logger.info("Starting TTS audio generation")

    # 确保输出目录存在
    AUDIO_SEGS_DIR.mkdir(parents=True, exist_ok=True)

    # TODO: 从音频任务文件读取需要生成的文本
    tasks = []  # 从文件读取的任务列表

    if tasks:
        # 使用 asyncio.gather 并发生成音频
        tts_results = await asyncio.gather(*[
            generate_tts_audio_async(task.text, task.voice, i)
            for i, task in enumerate(tasks)
        ])

        logger.info(f"Generated {len(tts_results)} audio segments")

    logger.info(f"TTS audio generation complete: {AUDIO_SEGS_DIR}")
    return str(AUDIO_SEGS_DIR)
