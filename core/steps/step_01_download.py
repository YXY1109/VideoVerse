"""Step 01: Video Download.

Downloads videos from YouTube or other online sources using yt-dlp.
从 temp/steps/step_01_download.py 迁移并转换为 PipelineStep。
"""

import asyncio
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

settings = get_settings()


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符。

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip('. ')
    return filename if filename else 'video'


def update_ytdlp() -> None:
    """更新 yt-dlp 到最新版本。"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        if 'yt_dlp' in sys.modules:
            del sys.modules['yt_dlp']
        logger.info("yt-dlp updated successfully")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to update yt-dlp: {e}")


def download_video_ytdlp_sync(url: str, save_path: str, resolution: str = '1080') -> str:
    """同步下载视频（yt-dlp 本身不支持异步）。

    Args:
        url: 视频 URL
        save_path: 保存目录
        resolution: 分辨率

    Returns:
        下载的视频文件路径
    """
    os.makedirs(save_path, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if resolution == 'best' else f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'noplaylist': True,
        'writethumbnail': True,
        'postprocessors': [{'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'}],
    }

    # 读取 cookies 文件路径
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH", "")
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = str(cookies_path)

    # 更新 yt-dlp
    update_ytdlp()
    from yt_dlp import YoutubeDL

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # 清理和重命名文件
    downloaded_files = []
    for file in os.listdir(save_path):
        if os.path.isfile(os.path.join(save_path, file)):
            filename, ext = os.path.splitext(file)
            new_filename = sanitize_filename(filename)
            if new_filename != filename:
                os.rename(os.path.join(save_path, file), os.path.join(save_path, new_filename + ext))
                downloaded_files.append(os.path.join(save_path, new_filename + ext))
            else:
                downloaded_files.append(os.path.join(save_path, file))

    return _find_video_files(save_path)


def _find_video_files(save_path: str) -> str:
    """查找下载的视频文件。

    Args:
        save_path: 搜索目录

    Returns:
        视频文件路径
    """
    video_formats = settings.allowed_video_formats
    video_files = [
        file for file in glob.glob(f"{save_path}/*")
        if os.path.splitext(file)[1][1:].lower() in video_formats
    ]
    # Windows 路径转换
    if sys.platform.startswith('win'):
        video_files = [file.replace("\\", "/") for file in video_files]
    video_files = [file for file in video_files if not file.startswith("output/output")]
    if len(video_files) != 1:
        raise ValueError(f"Number of videos found {len(video_files)} is not unique. Please check.")
    return video_files[0]


async def download_video(url: str, save_path: str, resolution: str = "1080") -> str:
    """异步下载视频。

    Args:
        url: 视频 URL
        save_path: 保存目录
        resolution: 分辨率

    Returns:
        下载的视频文件路径
    """
    logger.info(f"Downloading video from {url} (resolution: {resolution})")

    # yt-dlp 不支持异步，使用 asyncio.to_thread 在线程池中运行
    video_path = await asyncio.to_thread(
        download_video_ytdlp_sync,
        url,
        save_path,
        resolution
    )

    logger.info(f"Video downloaded: {video_path}")
    return video_path


class DownloadStep(PipelineStep):
    """视频下载步骤 - PipelineStep 实现。

    支持从 YouTube 或其他在线源下载视频，或直接使用本地视频文件。
    """

    def __init__(self, resolution: str = "1080"):
        self._resolution = resolution

    @property
    def name(self) -> str:
        return "step_01_download"

    @property
    def dependencies(self) -> list[str]:
        return []  # 无依赖

    async def validate(self, context: PipelineContext) -> bool:
        """验证视频源是否有效。

        Args:
            context: 流水线上下文

        Returns:
            是否有效
        """
        video_source = context.video_source
        if not video_source:
            logger.error("No video_source provided")
            return False

        # 检查是本地文件还是 URL
        if os.path.exists(video_source) and not video_source.startswith(('http://', 'https://')):
            return True

        if video_source.startswith(('http://', 'https://')):
            return True

        logger.error(f"Invalid video source: {video_source}")
        return False

    async def execute(self, context: PipelineContext) -> str:
        """执行视频下载。

        Args:
            context: 流水线上下文

        Returns:
            视频文件路径
        """
        video_source = context.video_source

        # 如果是本地文件，直接返回
        if os.path.exists(video_source) and not video_source.startswith(('http://', 'https://')):
            logger.info(f"Using local video file: {video_source}")
            context.set("video_path", video_source)
            return video_source

        # 如果是 URL，下载视频
        resolution = self._resolution or settings.youtube_resolution
        video_path = await download_video(video_source, str(paths.output_dir), resolution)

        context.set("video_path", video_path)
        return video_path


def create_step(resolution: str = "1080") -> DownloadStep:
    """工厂函数：创建下载步骤。

    Args:
        resolution: 视频分辨率

    Returns:
        DownloadStep 实例
    """
    return DownloadStep(resolution)


# 向后兼容的异步函数
async def step_01_download(url: str, resolution: str = "1080") -> str:
    """流水线第一步：下载视频（向后兼容）。

    Args:
        url: 视频 URL 或本地文件路径
        resolution: 分辨率

    Returns:
        视频文件路径
    """
    # 如果是本地文件，直接返回
    if os.path.exists(url) and not url.startswith(('http://', 'https://')):
        logger.info(f"Using local video file: {url}")
        return url

    # 如果是 URL，下载视频
    return await download_video(url, str(paths.output_dir), resolution)


__all__ = ["DownloadStep", "create_step", "step_01_download"]
