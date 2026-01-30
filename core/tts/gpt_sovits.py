"""GPT-SoVITS TTS backend.

从 temp/backends/tts/gpt_sovits.py 迁移并转换为同步架构。
"""

import asyncio
from pathlib import Path

import httpx
from loguru import logger

from core.tts.base import TTSBackend

GPT_SOVITS_HOST = "http://127.0.0.1:9880"


class GPTSoVITSBackend(TTSBackend):
    """GPT-SoVITS TTS backend (local server)."""

    def __init__(self, voice: str = "", reference_audio: str = ""):
        super().__init__(voice)
        self._reference_audio = reference_audio
        logger.info("GPT-SoVITS TTS initialized")

    async def _ensure_server_running(self) -> None:
        """Ensure GPT-SoVITS server is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{GPT_SOVITS_HOST}/ping")
            if response.status_code != 200:
                raise RuntimeError("GPT-SoVITS server not responding")
        except Exception:
            # Start server (Windows)
            import subprocess
            subprocess.Popen(
                ["python", "api.py"],
                cwd="core/tts_backend/GPT-SoVITS/api",
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            # Wait for server to start
            for _ in range(50):
                await asyncio.sleep(1)
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(f"{GPT_SOVITS_HOST}/ping")
                    if response.status_code == 200:
                        break
                except Exception:
                    continue
            else:
                raise RuntimeError("Failed to start GPT-SoVITS server")

    async def synthesize(self, text: str, output_path: str, refer_audio: str | None = None) -> None:
        """
        Synthesize speech using GPT-SoVITS.

        Args:
            text: Input text
            output_path: Output audio file path
            refer_audio: Optional reference audio for voice cloning
        """
        logger.info(f"Synthesizing with GPT-SoVITS: {text[:50]}...")

        await self._ensure_server_running()

        # Create output directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        url = f"{GPT_SOVITS_HOST}/tts"
        data = {
            "text": text,
            "text_language": "auto",
        }

        # Use provided refer_audio or fall back to init reference_audio
        ref_audio = refer_audio or self._reference_audio
        if ref_audio:
            data["refer_audio_path"] = ref_audio

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=data)

        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.success(f"Audio saved to: {output_path}")


def create_backend(voice: str = "", reference_audio: str = "") -> GPTSoVITSBackend:
    """Factory function for GPT-SoVITS backend."""
    return GPTSoVITSBackend(voice, reference_audio)


# Synchronous wrapper for compatibility
def synthesize_sync(text: str, save_path: str, reference_audio: str = None) -> None:
    """Synchronous wrapper for GPT-SoVITS."""
    backend = GPTSoVITSBackend("", reference_audio or "")
    asyncio.run(backend.synthesize(text, save_path))
