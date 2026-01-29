"""VideoVerse TTS backends."""
from core.tts.base import TTSBackend
from core.tts.edge import EdgeTTSBackend

__all__ = ["TTSBackend", "EdgeTTSBackend"]
