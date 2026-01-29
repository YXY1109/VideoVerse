"""Edge TTS backend."""
import edge_tts
from loguru import logger

from core.tts.base import TTSBackend


class EdgeTTSBackend(TTSBackend):
    """Microsoft Edge TTS backend."""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        super().__init__(voice)
        logger.info(f"Edge TTS initialized with voice: {voice}")

    async def synthesize(self, text: str, output_path: str) -> None:
        """
        Synthesize speech using Edge TTS.

        Args:
            text: Input text
            output_path: Output audio file path
        """
        logger.info(f"Synthesizing with Edge TTS: {text[:50]}...")

        communicate = edge_tts.Communicate(text, self._voice)
        await communicate.save(output_path)

        logger.success(f"Audio saved to: {output_path}")


def create_backend(voice: str = "zh-CN-XiaoxiaoNeural") -> EdgeTTSBackend:
    """Factory function."""
    return EdgeTTSBackend(voice)
