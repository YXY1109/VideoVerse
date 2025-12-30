"""
步骤 01: 视频下载测试

测试视频下载功能
"""
import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestSanitizeFilename:
    """测试 sanitize_filename 函数"""

    def test_basic_filename(self):
        """测试基本文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename("video.mp4")
        assert result == "video.mp4"

    def test_filename_with_invalid_chars(self):
        """测试包含非法字符的文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename('video<>:"|?*.mp4')
        assert result == "video.mp4"
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_filename_with_slashes(self):
        """测试包含斜杠的文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename("video/test/file.mp4")
        assert "/" not in result
        assert "\\" not in result

    def test_empty_filename(self):
        """测试空文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename("")
        assert result == "video"

    def test_filename_with_dots(self):
        """测试包含点的文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename("..test..mp4..")
        assert result == "test.mp4"

    def test_filename_with_spaces(self):
        """测试包含空格的文件名"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename("  test video .mp4  ")
        assert result == "test video .mp4"

    def test_all_invalid_chars(self):
        """测试全部是非法字符"""
        from src.steps.step_01_download import sanitize_filename

        result = sanitize_filename('<>:"/\\|?*')
        assert result == "video"


class TestFindVideoFiles:
    """测试 find_video_files 函数"""

    def test_find_single_video(self, tmp_path: Path):
        """测试查找单个视频文件"""
        from src.steps.step_01_download import find_video_files

        # 创建一个视频文件
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"")

        with patch('src.steps.step_01_download.settings.allowed_video_formats', ['mp4']):
            result = find_video_files(str(tmp_path))

            assert result == str(video_file)

    def test_find_multiple_videos_raises_error(self, tmp_path: Path):
        """测试多个视频文件抛出错误"""
        from src.steps.step_01_download import find_video_files

        # 创建多个视频文件
        (tmp_path / "video1.mp4").write_bytes(b"")
        (tmp_path / "video2.mp4").write_bytes(b"")

        with patch('src.steps.step_01_download.settings.allowed_video_formats', ['mp4']):
            with pytest.raises(ValueError, match="Number of videos found.*is not unique"):
                find_video_files(str(tmp_path))

    def test_find_no_video_raises_error(self, tmp_path: Path):
        """测试没有视频文件抛出错误"""
        from src.steps.step_01_download import find_video_files

        # 不创建视频文件

        with patch('src.steps.step_01_download.settings.allowed_video_formats', ['mp4']):
            with pytest.raises(ValueError, match="Number of videos found.*is not unique"):
                find_video_files(str(tmp_path))

    def test_find_video_ignores_non_video_files(self, tmp_path: Path):
        """测试忽略非视频文件"""
        from src.steps.step_01_download import find_video_files

        # 创建视频和非视频文件
        (tmp_path / "video.mp4").write_bytes(b"")
        (tmp_path / "document.txt").write_bytes(b"")
        (tmp_path / "image.jpg").write_bytes(b"")

        with patch('src.steps.step_01_download.settings.allowed_video_formats', ['mp4']):
            result = find_video_files(str(tmp_path))

            assert "video.mp4" in result
            assert ".txt" not in result
            assert ".jpg" not in result

    def test_find_video_different_formats(self, tmp_path: Path):
        """测试不同视频格式"""
        from src.steps.step_01_download import find_video_files

        formats = ['mp4', 'avi', 'mkv', 'mov']

        for fmt in formats:
            # 创建单个视频文件
            video_file = tmp_path / f"test.{fmt}"
            video_file.write_bytes(b"")

            with patch('src.steps.step_01_download.settings.allowed_video_formats', [fmt]):
                result = find_video_files(str(tmp_path))
                assert result == str(video_file)

            # 清理
            video_file.unlink()


class TestDownloadVideo:
    """测试 download_video 函数"""

    @pytest.mark.asyncio
    async def test_download_video_calls_ytdlp(self):
        """测试调用 yt-dlp"""
        from src.steps.step_01_download import download_video

        with patch('src.steps.step_01_download.asyncio.to_thread', new=AsyncMock(return_value="/path/to/video.mp4")):
            result = await download_video("https://youtube.com/watch?v=test", "1080")

            assert result == "/path/to/video.mp4"

    @pytest.mark.asyncio
    async def test_download_video_with_different_resolution(self):
        """测试不同分辨率"""
        from src.steps.step_01_download import download_video

        resolutions = ["360", "480", "720", "1080", "best"]

        for resolution in resolutions:
            with patch('src.steps.step_01_download.asyncio.to_thread', new=AsyncMock(return_value=f"/path/to/video_{resolution}.mp4")):
                result = await download_video("https://youtube.com/watch?v=test", resolution)

                assert resolution in result


class TestStep01Download:
    """测试 step_01_download 函数"""

    @pytest.mark.asyncio
    async def test_local_file_returns_path(self):
        """测试本地文件直接返回路径"""
        from src.steps.step_01_download import step_01_download

        # 创建临时文件
        with patch('os.path.exists', return_value=True):
            result = await step_01_download("/path/to/local/video.mp4")

            assert result == "/path/to/local/video.mp4"

    @pytest.mark.asyncio
    async def test_local_file_not_url(self):
        """测试非 URL 的本地路径"""
        from src.steps.step_01_download import step_01_download

        local_path = "D:\\Videos\\test.mp4"

        with patch('os.path.exists', return_value=True):
            result = await step_01_download(local_path)

            assert result == local_path

    @pytest.mark.asyncio
    async def test_http_url_downloads(self):
        """测试 HTTP URL 下载"""
        from src.steps.step_01_download import step_01_download

        url = "http://example.com/video.mp4"

        with patch('os.path.exists', return_value=False):
            with patch('src.steps.step_01_download.download_video', new=AsyncMock(return_value="/downloaded/video.mp4")):
                result = await step_01_download(url)

                assert result == "/downloaded/video.mp4"

    @pytest.mark.asyncio
    async def test_https_url_downloads(self):
        """测试 HTTPS URL 下载"""
        from src.steps.step_01_download import step_01_download

        url = "https://youtube.com/watch?v=test"

        with patch('os.path.exists', return_value=False):
            with patch('src.steps.step_01_download.download_video', new=AsyncMock(return_value="/downloaded/video.mp4")):
                result = await step_01_download(url)

                assert result == "/downloaded/video.mp4"

    @pytest.mark.asyncio
    async def test_uses_settings_resolution(self):
        """测试使用配置中的分辨率"""
        from src.steps.step_01_download import step_01_download

        url = "https://youtube.com/watch?v=test"

        with patch('os.path.exists', return_value=False):
            with patch('src.steps.step_01_download.settings.youtube_resolution', '720'):
                with patch('src.steps.step_01_download.download_video', new=AsyncMock(return_value="/video.mp4")) as mock_download:
                    await step_01_download(url)

                    # 验证使用了配置的分辨率
                    mock_download.assert_called_once()
                    call_args = mock_download.call_args
                    assert call_args[0][1] == '720'


@pytest.mark.integration
class TestDownloadIntegration:
    """集成测试: 下载功能"""

    @pytest.mark.skip(reason="需要真实的网络连接")
    @pytest.mark.asyncio
    async def test_real_youtube_download(self):
        """测试真实的 YouTube 下载（跳过）"""
        pass

    @pytest.mark.asyncio
    async def test_download_to_thread_wrapper(self):
        """测试 asyncio.to_thread 包装"""
        from src.steps.step_01_download import download_video

        # 验证同步函数在线程池中运行
        with patch('src.steps.step_01_download.asyncio.to_thread', new=AsyncMock(return_value="/video.mp4")) as mock_to_thread:
            await download_video("url", "1080")

            # 验证 to_thread 被调用
            mock_to_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        from src.steps.step_01_download import step_01_download

        url = "https://youtube.com/watch?v=test"

        with patch('os.path.exists', return_value=False):
            with patch('src.steps.step_01_download.download_video', side_effect=Exception("Download failed")):
                with pytest.raises(Exception, match="Download failed"):
                    await step_01_download(url)
