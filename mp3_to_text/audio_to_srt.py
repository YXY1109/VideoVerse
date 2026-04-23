"""
使用 faster-whisper 将中文音频转换为 SRT 字幕文件
支持处理两倍速录制的音频
"""

import argparse
import subprocess
import tempfile
import time
from pathlib import Path

from faster_whisper import WhisperModel


class Timer:
    """简单的时间统计工具"""

    def __init__(self):
        self.start_time = time.time()
        self.last_time = self.start_time

    def tick(self, name: str) -> float:
        """记录节点并返回从上一节点到现在的耗时"""
        now = time.time()
        elapsed = now - self.last_time
        total = now - self.start_time
        print(f"⏱ {name}: {elapsed:.2f}秒 (总耗时: {total:.2f}秒)")
        self.last_time = now
        return elapsed

    def total(self) -> float:
        """返回总耗时"""
        return time.time() - self.start_time


def format_timestamp(seconds: float) -> str:
    """将秒数转换为 SRT 时间戳格式 (00:00:00,000)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def slow_down_audio(input_path: str, output_path: str, speed_factor: float = 0.5) -> None:
    """
    使用 ffmpeg 降低音频速度（处理两倍速音频）

    Args:
        input_path: 输入音频路径
        output_path: 输出音频路径
        speed_factor: 速度因子（0.5 表示将两倍速音频降为正常速度）
    """
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-filter:a", f"atempo={speed_factor}", "-y", output_path],
            check=True,
            capture_output=True,
        )
        print(f"✓ 音频降速完成: {input_path} -> {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"✗ ffmpeg 处理失败: {e}")
        print("提示: 请确保已安装 ffmpeg 并添加到 PATH")
        raise
    except FileNotFoundError:
        print("✗ 未找到 ffmpeg，请先安装: https://ffmpeg.org/download.html")
        raise


def transcribe_to_srt(
    audio_path: str,
    output_srt: str,
    model_size: str = "large-v3",
    language: str = "zh",
    is_double_speed: bool = True,
    device: str = "cuda",
    compute_type: str = "float16",
) -> None:
    """
    将音频转录为 SRT 字幕文件

    Args:
        audio_path: 输入音频文件路径
        output_srt: 输出 SRT 字幕文件路径
        model_size: Whisper 模型大小 (tiny, base, small, medium, large-v2, large-v3)
        language: 音频语言代码 (zh=中文)
        is_double_speed: 是否为两倍速录音
        device: 运行设备 (cuda 或 cpu)
        compute_type: 计算类型 (float16, int8, int8_float16)
    """
    timer = Timer()
    audio_path = Path(audio_path)
    output_srt = Path(output_srt)

    # 确保输出目录存在
    output_srt.parent.mkdir(parents=True, exist_ok=True)

    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    print(f"{'='*50}")
    print(f"📁 输入文件: {audio_path.name}")
    print(f"📏 文件大小: {audio_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"🎯 模型: {model_size}")
    print(f"🔧 设备: {device} ({compute_type})")
    print(f"🌐 语言: {language}")
    print(f"⚡ 两倍速: {'是' if is_double_speed else '否'}")
    print(f"{'='*50}\n")

    print(f"正在加载模型: {model_size}")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    timer.tick("模型加载")

    # 处理两倍速音频
    temp_audio = None
    working_audio = audio_path

    if is_double_speed:
        print("检测到两倍速音频，正在降速处理...")
        with tempfile.NamedTemporaryFile(suffix=audio_path.suffix, delete=False) as f:
            temp_audio = Path(f.name)
        slow_down_audio(str(audio_path), str(temp_audio), speed_factor=0.5)
        timer.tick("音频降速")
        working_audio = temp_audio

    print(f"正在转录音频: {working_audio}")
    print(f"语言: {language}")

    # 转录参数
    transcribe_start = time.time()
    segments, info = model.transcribe(
        str(working_audio),
        language=language,
        beam_size=5,
        vad_filter=True,  # 启用 VAD (语音活动检测)
        vad_parameters={
            "min_silence_duration_ms": 100,  # 最小静音持续时间
            "speech_pad_ms": 30,  # 语音前后填充
        },
        word_timestamps=True,  # 获取词级时间戳
    )

    print(f"检测到语言: {info.language} (置信度: {info.language_probability:.2f})")

    # 写入 SRT 文件
    write_start = time.time()
    with open(output_srt, "w", encoding="utf-8") as f:
        segment_list = list(segments)
        total_segments = len(segment_list)

        for idx, segment in enumerate(segment_list, 1):
            start_time = segment.start
            end_time = segment.end
            text = segment.text.strip()

            # 如果是两倍速音频，需要调整时间戳
            if is_double_speed:
                start_time = start_time * 2
                end_time = end_time * 2

            f.write(f"{idx}\n")
            f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
            f.write(f"{text}\n\n")

            print(f"\r进度: {idx}/{total_segments} ({idx * 100 // total_segments}%)", end="")

    transcribe_time = time.time() - transcribe_start
    write_time = time.time() - write_start
    timer.tick(f"转录完成 (识别{transcribe_time:.2f}s + 写入{write_time:.2f}s)")

    # 清理临时文件
    if temp_audio and temp_audio.exists():
        temp_audio.unlink()

    # 输出统计信息
    total_time = timer.total()
    print(f"\n{'='*50}")
    print(f"✓ 字幕文件已保存: {output_srt}")
    print(f"📊 统计: {total_segments} 条字幕")
    print(f"⏱ 总耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="使用 faster-whisper 将中文音频转换为 SRT 字幕")
    parser.add_argument("audio", help="输入音频文件路径")
    parser.add_argument("-o", "--output", default="output.srt", help="输出 SRT 文件路径 (默认: output.srt)")
    parser.add_argument(
        "-m",
        "--model",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Whisper 模型大小 (默认: large-v3)",
    )
    parser.add_argument("-l", "--language", default="zh", help="音频语言 (默认: zh=中文)")
    parser.add_argument("--no-double-speed", action="store_true", help="音频不是两倍速录制（默认假设是两倍速）")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="运行设备 (默认: cuda)")

    args = parser.parse_args()

    transcribe_to_srt(
        audio_path=args.audio,
        output_srt=args.output,
        model_size=args.model,
        language=args.language,
        is_double_speed=not args.no_double_speed,
        device=args.device,
    )


if __name__ == "__main__":
    main()
