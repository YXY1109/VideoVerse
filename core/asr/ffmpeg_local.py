import os
import subprocess

from loguru import logger


def ffmpeg_video_to_audio(video_file: str) -> str:
    """视频提取音频文件"""
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    # 在视频所在目录下创建同名目录
    output_dir = os.path.join(os.path.dirname(video_file), video_name)
    os.makedirs(output_dir, exist_ok=True)
    # 将 mp3 保存在该目录下
    audio_path = os.path.join(output_dir, video_name + ".mp3")
    # 如果音频文件已存在，直接返回
    if os.path.exists(audio_path):
        logger.warning(f"Audio file already exists: {audio_path}")
        return audio_path
    logger.info(f"Converting video to audio: {video_file} -> {audio_path}")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_file,
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "32k",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-metadata",
            "encoding=UTF-8",
            str(audio_path),
        ],
        check=True,
        stderr=subprocess.PIPE,
    )
    logger.success(f"Audio conversion completed: {audio_path}")
    return audio_path
