import asyncio
import logging
import subprocess
from pathlib import Path

from ...config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def synthesize(text: str, save_path: str, voice: str = None) -> None:
    """
    异步合成语音（Edge TTS）

    Args:
        text: 要转换的文本
        save_path: 保存路径
        voice: 音色（可选，默认使用配置）
    """
    if voice is None:
        voice = settings.edge_tts_voice

    # 创建输出目录
    speech_file_path = Path(save_path)
    speech_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Edge TTS 不支持异步，使用 asyncio.to_thread
    cmd = ["edge-tts", "--voice", voice, "--text", text, "--write-media", str(speech_file_path)]
    await asyncio.to_thread(subprocess.run, cmd, check=True)

    logger.info(f"Audio saved to {speech_file_path}")
