"""Azure TTS backend.

从 temp/backends/tts/azure.py 迁移并转换为同步架构。
"""

import asyncio
from pathlib import Path

import httpx
from loguru import logger

from core.config import get_settings
from core.tts.base import TTSBackend

settings = get_settings()


class AzureTTSBackend(TTSBackend):
    """Microsoft Azure TTS backend."""

    def __init__(self, voice: str = "", api_key: str = ""):
        super().__init__(voice or settings.azure_tts_voice)
        self._api_key = api_key or settings.azure_tts_api_key
        self._url = "https://api.302.ai/cognitiveservices/v1"
        logger.info(f"Azure TTS initialized with voice: {self._voice}")

    async def synthesize(self, text: str, output_path: str, refer_audio: str | None = None) -> None:
        """
        Synthesize speech using Azure TTS.

        Args:
            text: Input text
            output_path: Output audio file path
            refer_audio: Not used for Azure TTS (kept for compatibility)
        """
        logger.info(f"Synthesizing with Azure TTS: {text[:50]}...")

        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Build SSML payload
        payload = f"""<speak version='1.0' xml:lang='zh-CN'><voice name='{self._voice}'>{text}</voice></speak>"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
            "Content-Type": "application/ssml+xml"
        }

        # Make request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._url, headers=headers, content=payload)

        # Write to file
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.success(f"Audio saved to: {output_path}")


def create_backend(voice: str = "", api_key: str = "") -> AzureTTSBackend:
    """Factory function for Azure TTS backend."""
    return AzureTTSBackend(voice, api_key)


# Synchronous wrapper for compatibility
def synthesize_sync(text: str, save_path: str, voice: str = None) -> None:
    """Synchronous wrapper for Azure TTS."""
    backend = AzureTTSBackend(voice or "")
    asyncio.run(backend.synthesize(text, save_path))
