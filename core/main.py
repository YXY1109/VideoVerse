from loguru import logger

from core.asr.common import process_transcription, save_results
from core.asr.demucs_local import demucs_audio
from core.asr.ffmpeg_local import ffmpeg_video_to_audio
from core.asr.pydub_local import normalize_audio_volume, split_audio
from core.asr.whisperx_local import transcribe_audio

DEFAULT_VIDEO_SOURCE = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"
DEFAULT_SOURCE_LANGUAGE = "zh"
DEFAULT_TARGET_LANGUAGE = "en"
#  是否使用Demucs进行人声分离
demucs = True

# 一：下载视频
video_path = DEFAULT_VIDEO_SOURCE

# 二：语音识别 (ASR)

# 2.1： 获取音频文件
mp3_path = ffmpeg_video_to_audio(video_path)

# 2.2： 使用Demucs进行人声分离
if demucs:
    vocal_audio = demucs_audio(mp3_path)
else:
    vocal_audio = mp3_path

# 2.3 标准化音频音量
vocal_normalized_audio = normalize_audio_volume(vocal_audio)

# 2.4 分割音频
segments = split_audio(vocal_normalized_audio)

# 2.5 转录
all_results = []
for start, end in segments:
    result = transcribe_audio(vocal_normalized_audio, vocal_audio, start, end)
    all_results.append(result)

# 2.6 合并结果
combined_result = {'segments': []}
for result in all_results:
    combined_result['segments'].extend(result['segments'])

# 2.7 处理和保存结果
df = process_transcription(combined_result)

asr_output_path = r"D:\PycharmProjects\VideoVerse\files\demo\cleaned_chunks.xlsx"
save_results(df, asr_output_path)

logger.success(f"asr处理完成：{asr_output_path}")
