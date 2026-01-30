"""Fish TTS backend.

从 temp/backends/tts/fish.py 迁移并转换为同步架构。
"""

import asyncio
from pathlib import Path

import httpx
from loguru import logger

from core.config import get_settings
from core.tts.base import TTSBackend

settings = get_settings()


class FishTTSBackend(TTSBackend):
    """Fish TTS backend."""

    def __init__(self, voice: str = "", api_key: str = ""):
        super().__init__(voice or "AD学姐")
        self._api_key = api_key or settings.fish_tts_api_key
        self._url = "https://api.302.ai/fish-audio/v1/tts"
        logger.info(f"Fish TTS initialized with voice: {self._voice}")

    async def synthesize(self, text: str, output_path: str, refer_audio: str | None = None) -> None:
        """
        Synthesize speech using Fish TTS.

        Args:
            text: Input text
            output_path: Output audio file path
            refer_audio: Optional reference audio for voice cloning
        """
        logger.info(f"Synthesizing with Fish TTS: {text[:50]}...")

        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        headers = {"Authorization": f"Bearer {self._api_key}"}
        json_data = {
            "text": text,
            "character": self._voice
        }

        # Add reference audio if provided
        if refer_audio:
            json_data["refer_audio"] = refer_audio

        # Make request
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self._url, headers=headers, json=json_data)

        # Fish TTS returns audio URL, need to download
        result = response.json()
        audio_url = result.get("audio_url")

        if audio_url:
            async with httpx.AsyncClient() as download_client:
                audio_response = await download_client.get(audio_url)
                with open(output_path, "wb") as f:
                    f.write(audio_response.content)

        logger.success(f"Audio saved to: {output_path}")


def create_backend(voice: str = "", api_key: str = "") -> FishTTSBackend:
    """Factory function for Fish TTS backend."""
    return FishTTSBackend(voice, api_key)


# Synchronous wrapper for compatibility
def synthesize_sync(text: str, save_path: str, voice: str = None) -> None:
    """Synchronous wrapper for Fish TTS."""
    backend = FishTTSBackend(voice or "")
    asyncio.run(backend.synthesize(text, save_path))
