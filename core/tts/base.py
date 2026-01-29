"""Base class for TTS backends."""
from abc import ABC, abstractmethod
from pathlib import Path


class TTSBackend(ABC):
    """Abstract base class for TTS backends."""

    def __init__(self, voice: str = ""):
        self._voice = voice

    @property
    def name(self) -> str:
        """Backend name."""
        return self.__class__.__name__.replace("TTSBackend", "").lower()

    @property
    def voice(self) -> str:
        """Current voice."""
        return self._voice

    @abstractmethod
    async def synthesize(self, text: str, output_path: str) -> None:
        """
        Synthesize speech from text.

        Args:
            text: Input text
            output_path: Where to save the audio file
        """
        pass
