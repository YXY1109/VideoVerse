"""
ASR 后端测试

测试各种 ASR 后端接口
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWhisperXLocalBackend:
    """测试 WhisperX 本地后端"""

    @pytest.mark.asyncio
    async def test_transcribe_audio_basic(self):
        """测试基本转录"""
        with patch('src.backends.asr.whisperx_local.transcribe_audio_impl', return_value={'segments': []}) as mock_impl:
            from src.backends.asr import whisperx_local

            result = await whisperx_local.transcribe_audio("audio.mp3", "vocal.mp3", 0, 100)

            mock_impl.assert_called_once()
            assert result == {'segments': []}


class TestWhisperXAPIBackend:
    """测试 WhisperX API 后端"""

    @pytest.mark.asyncio
    async def test_transcribe_audio_api(self):
        """测试 API 转录"""
        with patch('src.backends.asr.whisperx_api.transcribe_audio_impl', return_value={'segments': []}) as mock_impl:
            from src.backends.asr import whisperx_api

            result = await whisperx_api.transcribe_audio("audio.mp3", "vocal.mp3", 0, 100)

            mock_impl.assert_called_once()
            assert result == {'segments': []}


class TestElevenLabsBackend:
    """测试 ElevenLabs 后端"""

    @pytest.mark.asyncio
    async def test_transcribe_audio_elevenlabs(self):
        """测试 ElevenLabs 转录"""
        with patch('src.backends.asr.elevenlabs.transcribe_audio_impl', return_value={'segments': []}) as mock_impl:
            from src.backends.asr import elevenlabs

            result = await elevenlabs.transcribe_audio("audio.mp3", "vocal.mp3", 0, 100)

            mock_impl.assert_called_once()
            assert result == {'segments': []}


@pytest.mark.integration
class TestASRBackendsIntegration:
    """集成测试: ASR 后端"""

    @pytest.mark.skip(reason="需要真实的 WhisperX 模型")
    @pytest.mark.asyncio
    async def test_real_whisperx_local(self):
        """测试真实的 WhisperX 本地转录（跳过）"""
        pass

    @pytest.mark.skip(reason="需要 API Key")
    @pytest.mark.asyncio
    async def test_real_whisperx_api(self):
        """测试真实的 WhisperX API（跳过）"""
        pass
