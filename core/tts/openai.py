"""OpenAI TTS backend.

从 temp/backends/tts/openai.py 迁移并转换为同步架构。
"""

import asyncio
from pathlib import Path

from loguru import logger
from openai import AsyncOpenAI

from core.config import get_settings
from core.tts.base import TTSBackend

settings = get_settings()


class OpenAITTSBackend(TTSBackend):
    """OpenAI TTS backend."""

    def __init__(self, voice: str = "", api_key: str = ""):
        super().__init__(voice or settings.openai_tts_voice)
        self._api_key = api_key or settings.openai_tts_api_key
        self._base_url = "https://api.302.ai/v1"
        logger.info(f"OpenAI TTS initialized with voice: {self._voice}")

    async def synthesize(self, text: str, output_path: str, refer_audio: str | None = None) -> None:
        """
        Synthesize speech using OpenAI TTS.

        Args:
            text: Input text
            output_path: Output audio file path
            refer_audio: Not used for OpenAI TTS (kept for compatibility)
        """
        logger.info(f"Synthesizing with OpenAI TTS: {text[:50]}...")

        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Create client
        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url
        )

        try:
            # Generate speech
            response = await client.audio.speech.create(
                model="tts-1",
                voice=self._voice,
                input=text
            )

            # Write to file
            with open(output_path, "wb") as f:
                async for chunk in response.iter_bytes():
                    f.write(chunk)

            logger.success(f"Audio saved to: {output_path}")
        finally:
            await client.close()


def create_backend(voice: str = "", api_key: str = "") -> OpenAITTSBackend:
    """Factory function for OpenAI TTS backend."""
    return OpenAITTSBackend(voice, api_key)


# Synchronous wrapper for compatibility
def synthesize_sync(text: str, save_path: str, voice: str = None) -> None:
    """Synchronous wrapper for OpenAI TTS."""
    backend = OpenAITTSBackend(voice or "")
    asyncio.run(backend.synthesize(text, save_path))
