from loguru import logger

from core.asr.demucs_local import demucs_audio
from core.asr.ffmpeg_local import convert_video_to_audio

DEFAULT_VIDEO_SOURCE = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"
DEFAULT_SOURCE_LANGUAGE = "zh"
DEFAULT_TARGET_LANGUAGE = "en"
#  是否使用Demucs进行人声分离
demucs = True

# 一：下载视频
video_path = DEFAULT_VIDEO_SOURCE

# 二：语音识别 (ASR)

# 2.1： 获取音频文件
mp3_path = convert_video_to_audio(video_path)

# 2.2： 使用Demucs进行人声分离
if demucs:
    vocal_audio = demucs_audio(mp3_path)
else:
    vocal_audio = mp3_path
logger.info(f"Demucs complete: {vocal_audio}")
