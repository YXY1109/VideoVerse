"""VideoVerse TTS backends."""

from core.tts.base import TTSBackend
from core.tts.edge import EdgeTTSBackend, create_backend as create_edge_backend
from core.tts.azure import AzureTTSBackend, create_backend as create_azure_backend
from core.tts.openai import OpenAITTSBackend, create_backend as create_openai_backend
from core.tts.fish import FishTTSBackend, create_backend as create_fish_backend
from core.tts.gpt_sovits import GPTSoVITSBackend, create_backend as create_gpt_sovits_backend

__all__ = [
    "TTSBackend",
    "EdgeTTSBackend",
    "AzureTTSBackend",
    "OpenAITTSBackend",
    "FishTTSBackend",
    "GPTSoVITSBackend",
    "create_edge_backend",
    "create_azure_backend",
    "create_openai_backend",
    "create_fish_backend",
    "create_gpt_sovits_backend",
]
