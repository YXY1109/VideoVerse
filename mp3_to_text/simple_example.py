"""
简单示例：将中文音频（两倍速）转换为字幕
"""

import datetime

from audio_to_srt import transcribe_to_srt

# 模型在这里：C:\Users\YXY1109\.cache\huggingface\hub

video_name = 6

# 配置参数
AUDIO_FILE = f"files/{video_name}.m4a"  # 你的音频文件路径
now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_SRT = f"srt/{video_name}_{now}.srt"  # 输出字幕文件路径
print(f"正在处理文件: {OUTPUT_SRT}")

# tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3,
# large, distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3, distil-large-v3.5, large-v3-turbo, turbo

model_size = "large-v3"
# model_size = "tiny"

# 执行转换
transcribe_to_srt(
    audio_path=AUDIO_FILE,
    output_srt=OUTPUT_SRT,
    model_size=model_size,  # 使用大模型获得最佳效果
    language="zh",  # 中文
    is_double_speed=True,  # 两倍速录音
    device="cuda",  # 使用 GPU
    compute_type="float16",  # GPU 使用 float16 加速
)
