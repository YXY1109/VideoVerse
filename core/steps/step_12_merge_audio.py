"""Step 12: Merge Audio.

合并音频片段。
从 temp/steps/step_12_merge_audio.py 迁移并转换为 PipelineStep（简化版）。
"""

import subprocess
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

settings = get_settings()


class MergeAudioStep(PipelineStep):
    """音频合并步骤 - PipelineStep 实现。

    合并 TTS 生成的音频片段。
    """

    @property
    def name(self) -> str:
        return "step_12_merge_audio"

    @property
    def dependencies(self) -> list[str]:
        return ["step_11_gen_audio"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证音频片段目录是否存在。"""
        audio_segments_dir = context.get("audio_segments_dir")
        if not audio_segments_dir:
            logger.error("No audio_segments_dir in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行音频合并。

        Args:
            context: 流水线上下文

        Returns:
            合并后的音频路径
        """
        logger.info("Starting audio merge")

        # 简化实现：使用 FFmpeg concat 合并音频
        audio_segments_dir = context.get("audio_segments_dir")
        output_path = str(paths.audio_dir / "merged_audio.mp3")

        # 创建 concat 列表文件
        import os
        segments = [f for f in os.listdir(audio_segments_dir) if f.endswith('.mp3')]
        segments.sort()

        concat_file = paths.audio_tmp_dir / "concat.txt"
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{os.path.join(audio_segments_dir, seg)}'\n")

        # 使用 FFmpeg 合并
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            output_path
        ]

        subprocess.run(cmd, check=True)

        logger.info(f"Audio merge complete: {output_path}")
        context.set("merged_audio", output_path)
        return output_path


def create_step() -> MergeAudioStep:
    """工厂函数：创建音频合并步骤。"""
    return MergeAudioStep()


__all__ = ["MergeAudioStep", "create_step"]
