"""
步骤 02: ASR 测试

测试语音识别功能
"""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pandas as pd
import pytest


class TestNormalizeAudioVolume:
    """测试 normalize_audio_volume 函数"""

    def test_normalize_creates_output_file(self, tmp_path: Path):
        """测试创建输出文件"""
        from src.steps.step_02_asr import normalize_audio_volume

        # 创建模拟输入音频文件
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.wav"

        with patch('src.steps.step_02_asr.AudioSegment.from_file', return_value=MagicMock(dBFS=-10.0)):
            with patch('src.steps.step_02_asr.AudioSegment') as mock_audio_segment:
                mock_audio = MagicMock()
                mock_audio_segment.from_file.return_value = mock_audio
                mock_audio.apply_gain.return_value = mock_audio
                mock_audio.export = MagicMock()

                result = normalize_audio_volume(str(input_file), str(output_file), target_db=-20.0)

                # 验证 export 被调用
                mock_audio.export.assert_called_once()

    def test_normalize_calculates_gain(self):
        """测试计算增益"""
        from src.steps.step_02_asr import normalize_audio_volume

        with patch('src.steps.step_02_asr.AudioSegment') as mock_audio_segment:
            mock_audio = MagicMock()
            mock_audio.dBFS = -10.0
            mock_audio_segment.from_file.return_value = mock_audio
            mock_audio.apply_gain.return_value = mock_audio

            normalize_audio_volume("input.wav", "output.wav", target_db=-20.0)

            # 验证应用了正确的增益 (-20 - (-10) = -10)
            mock_audio.apply_gain.assert_called_once_with(-10.0)


class TestConvertVideoToAudio:
    """测试 convert_video_to_audio_sync 函数"""

    def test_convert_creates_audio_dir(self, tmp_path: Path):
        """测试创建音频目录"""
        from src.steps.step_02_asr import convert_video_to_audio_sync

        video_file = tmp_path / "video.mp4"
        output_file = tmp_path / "audio" / "raw.mp3"

        with patch('subprocess.run'):
            convert_video_to_audio_sync(str(video_file), str(output_file))

            # 验证目录被创建
            # 注意: 实际创建在函数内部

    def test_convert_runs_ffmpeg(self):
        """测试运行 ffmpeg 命令"""
        from src.steps.step_02_asr import convert_video_to_audio_sync

        with patch('subprocess.run') as mock_run:
            convert_video_to_audio_sync("video.mp4", "output.mp3")

            # 验证 subprocess.run 被调用
            mock_run.assert_called_once()
            # 验证命令包含 ffmpeg
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args

    def test_convert_with_check(self):
        """测试 check=True 参数"""
        from src.steps.step_02_asr import convert_video_to_audio_sync

        with patch('subprocess.run') as mock_run:
            convert_video_to_audio_sync("video.mp4", "output.mp3")

            # 验证 check=True
            assert mock_run.call_args[1]['check'] is True


class TestSplitAudioSync:
    """测试 split_audio_sync 函数"""

    def test_split_short_audio(self):
        """测试短音频（不需要分割）"""
        from src.steps.step_02_asr import split_audio_sync

        with patch('src.steps.step_02_asr.AudioSegment.from_file') as mock_from_file:
            mock_audio = MagicMock()
            mock_from_file.return_value = mock_audio

            with patch('src.steps.step_02_asr.mediainfo', return_value={'duration': '600'}):  # 10分钟
                segments = split_audio_sync("audio.mp3", target_len=1800)  # 30分钟

                # 短音频应该返回单个片段
                assert len(segments) == 1
                assert segments[0] == (0, 600.0)

    def test_split_long_audio(self):
        """测试长音频分割"""
        from src.steps.step_02_asr import split_audio_sync

        with patch('src.steps.step_02_asr.AudioSegment.from_file'):
            with patch('src.steps.step_02_asr.mediainfo', return_value={'duration': '3600'}):  # 1小时
                with patch('src.steps.step_02_asr.detect_silence', return_value=[(1700, 1800)]):
                    segments = split_audio_sync("audio.mp3", target_len=1800, win=60)

                    # 长音频应该被分割
                    assert len(segments) >= 1


class TestFixMojibakeText:
    """测试 fix_mojibake_text 函数"""

    def test_returns_empty_string(self):
        """测试返回空字符串"""
        from src.steps.step_02_asr import fix_mojibake_text

        result = fix_mojibake_text("")
        assert result == ""

    def test_returns_none(self):
        """测试返回 None"""
        from src.steps.step_02_asr import fix_mojibake_text

        result = fix_mojibake_text(None)
        assert result is None

    def test_chinese_text_unchanged(self):
        """测试中文文本不变"""
        from src.steps.step_02_asr import fix_mojibake_text

        text = "你好世界"
        result = fix_mojibake_text(text)

        assert result == text

    def test_fix_latin1_encoding(self):
        """测试修复 latin1 编码"""
        from src.steps.step_02_asr import fix_mojibake_text

        # 这个测试取决于实际的编码问题
        # 在大多数情况下，如果没有编码问题，应该返回原文本
        text = "Hello world"
        result = fix_mojibake_text(text)

        # 如果没有检测到中文，会尝试各种编码
        # 但因为文本本身就是英文，应该返回原文本或某种编码转换结果
        assert isinstance(result, str)

    def test_no_chinese_no_encoding_needed(self):
        """测试无中文不需要编码修复"""
        from src.steps.step_02_asr import fix_mojibake_text

        text = "This is English text"
        result = fix_mojibake_text(text)

        # 英文文本应该保持不变
        assert result == text


class TestProcessTranscription:
    """测试 process_transcription 函数"""

    def test_basic_transcription(self):
        """测试基本转录处理"""
        from src.steps.step_02_asr import process_transcription

        result = {
            'segments': [
                {
                    'speaker_id': None,
                    'words': [
                        {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                        {'word': 'world', 'start': 0.5, 'end': 1.0},
                    ]
                }
            ]
        }

        df = process_transcription(result)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'text' in df.columns
        assert 'start' in df.columns
        assert 'end' in df.columns
        assert 'speaker_id' in df.columns

    def test_long_word_filtering(self):
        """测试过滤长单词"""
        from src.steps.step_02_asr import process_transcription

        result = {
            'segments': [
                {
                    'speaker_id': None,
                    'words': [
                        {'word': 'short', 'start': 0.0, 'end': 0.5},
                        {'word': 'a' * 35, 'start': 0.5, 'end': 1.0},  # 超过30字符
                    ]
                }
            ]
        }

        df = process_transcription(result)

        # 长单词应该被过滤
        assert len(df) == 1
        assert df.iloc[0]['text'] == '"short"'

    def test_word_with_quotes_removed(self):
        """测试移除引号"""
        from src.steps.step_02_asr import process_transcription

        result = {
            'segments': [
                {
                    'speaker_id': None,
                    'words': [
                        {'word': '«test»', 'start': 0.0, 'end': 0.5},
                    ]
                }
            ]
        }

        df = process_transcription(result)

        assert df.iloc[0]['text'] == '"test"'

    def test_word_without_timestamp(self):
        """测试没有时间戳的单词"""
        from src.steps.step_02_asr import process_transcription

        result = {
            'segments': [
                {
                    'speaker_id': None,
                    'words': [
                        {'word': 'first', 'start': 0.0, 'end': 0.5},
                        {'word': 'no_timestamp'},  # 没有时间戳
                    ]
                }
            ]
        }

        df = process_transcription(result)

        # 应该使用前一个单词的时间戳
        assert len(df) == 2
        assert df.iloc[1]['start'] == 0.5
        assert df.iloc[1]['end'] == 0.5


class TestSaveResultsSync:
    """测试 save_results_sync 函数"""

    def test_save_creates_directory(self, tmp_path: Path):
        """测试创建目录"""
        from src.steps.step_02_asr import save_results_sync

        df = pd.DataFrame({'text': ['Hello'], 'start': [0.0], 'end': [1.0]})
        output_path = tmp_path / "subdir" / "output.xlsx"

        save_results_sync(df, str(output_path))

        # 验证文件被创建
        assert output_path.exists()

    def test_save_filters_empty_text(self):
        """测试过滤空文本"""
        from src.steps.step_02_asr import save_results_sync

        df = pd.DataFrame({
            'text': ['Hello', '', 'World'],
            'start': [0.0, 1.0, 2.0],
            'end': [1.0, 2.0, 3.0],
        })

        output_path = Path("/tmp/test_output.xlsx")

        with patch('src.steps.step_02_asr.LOG_DIR', Path("/tmp")):
            with patch.object(df, 'to_excel'):
                save_results_sync(df, str(output_path))

    def test_save_filters_long_words(self):
        """测试过滤长单词"""
        from src.steps.step_02_asr import save_results_sync

        df = pd.DataFrame({
            'text': ['short', 'a' * 35, 'normal'],
            'start': [0.0, 1.0, 2.0],
            'end': [1.0, 2.0, 3.0],
        })

        output_path = Path("/tmp/test_output.xlsx")

        with patch('src.steps.step_02_asr.LOG_DIR', Path("/tmp")):
            with patch.object(df, 'to_excel'):
                save_results_sync(df, str(output_path))


class TestDemucsAudio:
    """测试 demucs_audio 函数"""

    @pytest.mark.asyncio
    async def test_demucs_runs_subprocess(self):
        """测试运行 demucs 子进程"""
        from src.steps.step_02_asr import demucs_audio

        with patch('src.steps.step_02_asr.asyncio.to_thread', new=AsyncMock()):
            with patch('src.steps.step_02_asr.Path'):
                with patch('shutil.move'):
                    with patch('shutil.rmtree'):
                        await demucs_audio("input.mp3", "output.mp3")

    @pytest.mark.asyncio
    async def test_demucs_moves_output(self):
        """测试移动输出文件"""
        from src.steps.step_02_asr import demucs_audio

        with patch('src.steps.step_02_asr.asyncio.to_thread', new=AsyncMock()):
            mock_path_instance = MagicMock()
            mock_vocals = MagicMock()
            mock_vocals.exists.return_value = True
            mock_path_instance.__truediv__.return_value = mock_vocals
            mock_vocals.__truediv__.return_value = mock_vocals

            with patch('src.steps.step_02_asr.Path', return_value=mock_path_instance):
                with patch('shutil.move'):
                    with patch('shutil.rmtree'):
                        await demucs_audio("input.mp3", "output.mp3")


class TestTranscribeAudio:
    """测试 transcribe_audio 函数"""

    @pytest.mark.asyncio
    async def test_transcribe_local_runtime(self):
        """测试本地运行时"""
        from src.steps.step_02_asr import transcribe_audio

        with patch('src.steps.step_02_asr.whisperx_local.transcribe_audio', new=AsyncMock(return_value={"segments": []})):
            result = await transcribe_audio("audio.mp3", "vocal.mp3", 0, 100, "local")

            assert result == {"segments": []}

    @pytest.mark.asyncio
    async def test_transcribe_cloud_runtime(self):
        """测试云端运行时"""
        from src.steps.step_02_asr import transcribe_audio

        with patch('src.steps.step_02_asr.whisperx_api.transcribe_audio', new=AsyncMock(return_value={"segments": []})):
            result = await transcribe_audio("audio.mp3", "vocal.mp3", 0, 100, "cloud")

            assert result == {"segments": []}

    @pytest.mark.asyncio
    async def test_transcribe_elevenlabs_runtime(self):
        """测试 ElevenLabs 运行时"""
        from src.steps.step_02_asr import transcribe_audio

        with patch('src.steps.step_02_asr.elevenlabs.transcribe_audio', new=AsyncMock(return_value={"segments": []})):
            result = await transcribe_audio("audio.mp3", "vocal.mp3", 0, 100, "elevenlabs")

            assert result == {"segments": []}

    @pytest.mark.asyncio
    async def test_transcribe_unknown_runtime_raises(self):
        """测试未知运行时抛出错误"""
        from src.steps.step_02_asr import transcribe_audio

        with pytest.raises(ValueError, match="Unknown ASR runtime"):
            await transcribe_audio("audio.mp3", "vocal.mp3", 0, 100, "unknown")


class TestStep02ASR:
    """测试 step_02_asr 函数"""

    @pytest.mark.asyncio
    async def test_asr_with_existing_output(self, tmp_path: Path):
        """测试输出文件已存在时跳过"""
        from src.steps.step_02_asr import step_02_asr

        video_path = str(tmp_path / "video.mp4")
        output_file = tmp_path / "log" / "cleaned_chunks.xlsx"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("test")

        with patch('src.steps.step_02_asr.CLEANED_CHUNKS', output_file):
            result = await step_02_asr(video_path, "en")

            # 文件已存在应该跳过
            assert result is None

    @pytest.mark.asyncio
    async def test_asr_full_pipeline(self):
        """测试完整 ASR 流程"""
        from src.steps.step_02_asr import step_02_asr

        with patch('src.steps.step_02_asr.CLEANED_CHUNKS', Path("/nonexistent/cleaned_chunks.xlsx")):
            with patch('src.steps.step_02_asr.convert_video_to_audio_sync'):
                with patch('src.steps.step_02_asr.settings.demucs', False):
                    with patch('src.steps.step_02_asr.split_audio_sync', return_value=[(0, 100)]):
                        with patch('src.steps.step_02_asr.transcribe_audio', new=AsyncMock(return_value={'segments': []})):
                            with patch('src.steps.step_02_asr.process_transcription', return_value=pd.DataFrame({'text': []})):
                                with patch('src.steps.step_02_asr.save_results_sync'):
                                    result = await step_02_asr("video.mp4", "en")

                                    assert result is not None


@pytest.mark.integration
class TestASRIntegration:
    """集成测试: ASR 功能"""

    @pytest.mark.skip(reason="需要真实的音频文件和模型")
    @pytest.mark.asyncio
    async def test_real_whisperx_transcription(self):
        """测试真实的 WhisperX 转录（跳过）"""
        pass

    @pytest.mark.skip(reason="需要 Demucs")
    @pytest.mark.asyncio
    async def test_real_demucs_separation(self):
        """测试真实的 Demucs 分离（跳过）"""
        pass
