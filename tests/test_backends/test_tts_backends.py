"""
TTS 后端测试

测试各种 TTS 后端接口
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAzureTTSBackend:
    """测试 Azure TTS 后端"""

    @pytest.mark.asyncio
    async def test_generate_audio_basic(self):
        """测试基本音频生成"""
        with patch('src.backends.tts.azure.generate_audio_impl', return_value='/path/to/audio.mp3') as mock_impl:
            from src.backends.tts import azure

            result = await azure.generate_audio("Hello world", "output.mp3", "zh-CN-XiaoxiaoNeural")

            mock_impl.assert_called_once()
            assert result == '/path/to/audio.mp3'


class TestOpenAITTSBackend:
    """测试 OpenAI TTS 后端"""

    @pytest.mark.asyncio
    async def test_generate_audio_openai(self):
        """测试 OpenAI TTS"""
        with patch('src.backends.tts.openai.generate_audio_impl', return_value='/path/to/audio.mp3') as mock_impl:
            from src.backends.tts import openai

            result = await openai.generate_audio("Hello world", "output.mp3", "alloy")

            mock_impl.assert_called_once()
            assert result == '/path/to/audio.mp3'


class TestEdgeTTSBackend:
    """测试 Edge TTS 后端"""

    @pytest.mark.asyncio
    async def test_generate_audio_edge(self):
        """测试 Edge TTS"""
        with patch('src.backends.tts.edge.generate_audio_impl', return_value='/path/to/audio.mp3') as mock_impl:
            from src.backends.tts import edge

            result = await edge.generate_audio("Hello world", "output.mp3", "zh-CN-XiaoxiaoNeural")

            mock_impl.assert_called_once()
            assert result == '/path/to/audio.mp3'


class TestFishTTSBackend:
    """测试 Fish TTS 后端"""

    @pytest.mark.asyncio
    async def test_generate_audio_fish(self):
        """测试 Fish TTS"""
        with patch('src.backends.tts.fish.generate_audio_impl', return_value='/path/to/audio.mp3') as mock_impl:
            from src.backends.tts import fish

            result = await fish.generate_audio("Hello world", "output.mp3", "fish_voice")

            mock_impl.assert_called_once()
            assert result == '/path/to/audio.mp3'


@pytest.mark.integration
class TestTTSBackendsIntegration:
    """集成测试: TTS 后端"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    @pytest.mark.asyncio
    async def test_real_azure_tts(self):
        """测试真实的 Azure TTS（跳过）"""
        pass

    @pytest.mark.skip(reason="需要真实的 API Key")
    @pytest.mark.asyncio
    async def test_real_openai_tts(self):
        """测试真实的 OpenAI TTS（跳过）"""
        pass

    @pytest.mark.skip(reason="需要网络连接")
    @pytest.mark.asyncio
    async def test_real_edge_tts(self):
        """测试真实的 Edge TTS（跳过）"""
        pass
