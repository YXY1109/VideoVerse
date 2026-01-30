"""Step 11: Generate Audio.

使用 TTS 生成音频。
从 temp/steps/step_11_gen_audio.py 迁移并转换为 PipelineStep。
"""

import os
from pathlib import Path

import pandas as pd
from loguru import logger

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.tts import (
    TTSBackend,
    create_azure_backend,
    create_edge_backend,
    create_fish_backend,
    create_gpt_sovits_backend,
    create_openai_backend,
)

settings = get_settings()


def time_to_samples(time_str: str, sr: int) -> int:
    """统一时间转换函数。

    Args:
        time_str: 时间字符串 (HH:MM:SS,mmm)
        sr: 采样率

    Returns:
        采样点数
    """
    h, m, s = time_str.split(':')
    s, ms = s.split(',') if ',' in s else (s, '0')
    seconds = int(h) * 3600 + int(m) * 60 + float(s) + float(ms) / 1000
    return int(seconds * sr)


def extract_audio(audio_data, sr: int, start_time: str, end_time: str, out_file: Path) -> None:
    """提取音频片段。

    Args:
        audio_data: 音频数据数组
        sr: 采样率
        start_time: 开始时间字符串
        end_time: 结束时间字符串
        out_file: 输出文件路径
    """
    start = time_to_samples(start_time, sr)
    end = time_to_samples(end_time, sr)
    sf.write(out_file, audio_data[start:end], sr)


def generate_refer_audio(df: pd.DataFrame, vocal_audio_file: Path, refers_dir: Path) -> None:
    """生成参考音频片段。

    Args:
        df: 音频任务 DataFrame
        vocal_audio_file: 人声音频文件
        refers_dir: 参考音频输出目录
    """
    if not SOUNDFILE_AVAILABLE:
        logger.warning("soundfile not available, skipping reference audio generation")
        return

    # 确保输出目录存在
    refers_dir.mkdir(parents=True, exist_ok=True)

    # 读取音频数据
    data, sr = sf.read(vocal_audio_file)

    # 提取所有音频片段
    for _, row in df.iterrows():
        out_file = refers_dir / f"{row['number']}.wav"
        extract_audio(data, sr, row['start_time'], row['end_time'], out_file)

    logger.info(f"Generated {len(df)} reference audio segments in {refers_dir}")


def get_tts_backend(method: str, voice: str | None = None) -> TTSBackend:
    """获取 TTS 后端。

    Args:
        method: TTS 方法
        voice: 音色（可选）

    Returns:
        TTS 后端实例
    """
    method = method.lower()

    if method == 'azure':
        return create_azure_backend(voice or settings.azure_tts_voice)
    elif method == 'openai':
        return create_openai_backend(voice or settings.openai_tts_voice)
    elif method == 'edge':
        return create_edge_backend(voice or settings.edge_tts_voice)
    elif method == 'fish':
        return create_fish_backend()
    elif method == 'gpt_sovits':
        return create_gpt_sovits_backend()
    else:
        raise ValueError(f"Unsupported TTS method: {method}")


class GenAudioStep(PipelineStep):
    """TTS 音频生成步骤 - PipelineStep 实现。

    使用 TTS 后端生成音频。
    """

    @property
    def name(self) -> str:
        return "step_11_gen_audio"

    @property
    def dependencies(self) -> list[str]:
        return ["step_10_audio_task"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证音频任务是否存在。"""
        audio_tasks = context.get("audio_tasks")
        if not audio_tasks:
            logger.error("No audio_tasks in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行 TTS 音频生成。

        Args:
            context: 流水线上下文

        Returns:
            音频片段目录路径
        """
        logger.info("Starting TTS audio generation")

        audio_tasks = context.get("audio_tasks")
        df = pd.read_excel(audio_tasks)

        # 确保输出目录存在
        paths.audio_segs_dir.mkdir(parents=True, exist_ok=True)
        paths.audio_refers_dir.mkdir(parents=True, exist_ok=True)

        # 检查是否需要先生成参考音频
        if not list(paths.audio_refers_dir.glob('*.wav')):
            logger.info("Generating reference audio segments...")

            # 先确保人声音频存在
            vocal_audio = paths.vocal_audio
            if vocal_audio.exists():
                generate_refer_audio(df, vocal_audio, paths.audio_refers_dir)
            else:
                logger.warning(f"Vocal audio file not found: {vocal_audio}")

        # 创建 TTS 后端
        tts_backend = get_tts_backend(settings.tts_method)

        # 检查是否已存在所有音频片段
        existing_segs = len(list(paths.audio_segs_dir.glob('seg_*.wav')))
        if existing_segs >= len(df):
            logger.info(f"Audio segments already exist ({existing_segs} files), skipping generation")
            context.set("audio_segments_dir", str(paths.audio_segs_dir))
            return str(paths.audio_segs_dir)

        # 生成 TTS 音频
        logger.info(f"Generating {len(df)} audio segments using {settings.tts_method} TTS")
        for _, row in df.iterrows():
            text = row['text']
            number = row['number']
            output_file = paths.audio_segs_dir / f"seg_{number}.wav"

            # 检查是否已存在
            if output_file.exists():
                continue

            # 获取参考音频（如果存在）
            refer_audio = paths.audio_refers_dir / f"{number}.wav"
            refer_path = str(refer_audio) if refer_audio.exists() else None

            # 使用 TTS 后端生成音频
            await tts_backend.synthesize(text, str(output_file), refer_audio=refer_path)
            logger.info(f"Generated audio segment {number}: {output_file}")

        logger.info(f"TTS audio generation complete: {paths.audio_segs_dir}")
        context.set("audio_segments_dir", str(paths.audio_segs_dir))
        return str(paths.audio_segs_dir)


def create_step() -> GenAudioStep:
    """工厂函数：创建 TTS 音频生成步骤。"""
    return GenAudioStep()


__all__ = ["GenAudioStep", "create_step"]
