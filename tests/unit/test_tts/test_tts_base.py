"""Test TTS base class."""
import tempfile
from pathlib import Path

import pytest

from core.tts.base import TTSBackend


class Dummy(TTSBackend):
    """Test TTS backend."""

    async def synthesize(self, text: str, output_path: str):
        with open(output_path, "wb") as f:
            f.write(b"dummy audio")


@pytest.mark.asyncio
async def test_tts_backend_name():
    """Test backend has a name."""
    backend = Dummy()
    assert backend.name == "dummy"


@pytest.mark.asyncio
async def test_tts_backend_synthesize():
    """Test synthesis creates output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = Dummy()
        output_file = Path(tmpdir) / "test.mp3"

        await backend.synthesize("Hello", str(output_file))

        assert output_file.exists()
        assert output_file.read_bytes() == b"dummy audio"


def test_tts_backend_voice_property():
    """Test voice property."""
    backend = Dummy(voice="test-voice")
    assert backend.voice == "test-voice"
