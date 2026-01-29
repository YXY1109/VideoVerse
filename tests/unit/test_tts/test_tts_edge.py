"""Test Edge TTS backend."""
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.tts.edge import EdgeTTSBackend


@pytest.mark.asyncio
async def test_edge_tts_name():
    """Test Edge TTS backend name."""
    backend = EdgeTTSBackend(voice="zh-CN-XiaoxiaoNeural")
    assert backend.name == "edge"


@pytest.mark.asyncio
async def test_edge_tts_synthesize_mock():
    """Test Edge TTS synthesis with mock."""
    backend = EdgeTTSBackend(voice="zh-CN-XiaoxiaoNeural")

    with patch("edge_tts.Communicate") as mock_communicate:
        mock_comm = AsyncMock()
        mock_comm.save = AsyncMock()
        mock_communicate.return_value = mock_comm

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test.mp3"

            await backend.synthesize("测试", str(output_file))

            mock_communicate.assert_called_once_with("测试", "zh-CN-XiaoxiaoNeural")
            mock_comm.save.assert_called_once()
