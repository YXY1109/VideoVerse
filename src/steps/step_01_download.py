"""
步骤 01: 视频下载

使用 yt-dlp 下载 YouTube 或其他在线视频
"""
import asyncio
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

from src.config import get_settings
from src.utils.paths import INPUT_VIDEO_FILE, OUTPUT_DIR

settings = get_settings()


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.strip('. ')
    return filename if filename else 'video'


def update_ytdlp() -> None:
    """更新 yt-dlp 到最新版本"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        if 'yt_dlp' in sys.modules:
            del sys.modules['yt_dlp']
        print("yt-dlp updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to update yt-dlp: {e}")


def download_video_ytdlp_sync(url: str, save_path: str = 'output', resolution: str = '1080') -> str:
    """
    同步下载视频（yt-dlp 本身不支持异步）

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

    return find_video_files(save_path)


def find_video_files(save_path: str = 'output') -> str:
    """查找下载的视频文件"""
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


async def download_video(
    url: str,
    resolution: str = "1080",
) -> str:
    """
    异步下载视频

    Args:
        url: 视频 URL
        resolution: 分辨率 (360/480/720/1080/best)

    Returns:
        下载的视频文件路径
    """
    print(f"Downloading video from {url} (resolution: {resolution})")

    # yt-dlp 不支持异步，使用 asyncio.to_thread 在线程池中运行
    video_path = await asyncio.to_thread(
        download_video_ytdlp_sync,
        url,
        str(OUTPUT_DIR),
        resolution
    )

    print(f"Video downloaded: {video_path}")
    return video_path


async def step_01_download(url: str) -> str:
    """
    流水线第一步：下载视频

    Args:
        url: 视频 URL 或本地文件路径

    Returns:
        视频文件路径
    """
    # 如果是本地文件，直接返回
    if os.path.exists(url) and not url.startswith(('http://', 'https://')):
        print(f"Using local video file: {url}")
        return url

    # 如果是 URL，下载视频
    resolution = settings.youtube_resolution
    return await download_video(url, resolution)


if __name__ == '__main__':
    # 测试
    import asyncio
    url = input('Please enter the URL of the video you want to download: ')
    video_path = asyncio.run(step_01_download(url))
    print(f"Video downloaded to: {video_path}")
