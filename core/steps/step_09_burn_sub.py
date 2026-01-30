"""Step 09: Burn Subtitle.

将字幕烧录到视频中。
从 temp/steps/step_09_burn_sub.py 迁移并转换为 PipelineStep（简化版）。
"""

import subprocess
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

settings = get_settings()


class BurnSubStep(PipelineStep):
    """字幕烧录步骤 - PipelineStep 实现。

    将字幕烧录到视频中。
    """

    @property
    def name(self) -> str:
        return "step_09_burn_sub"

    @property
    def dependencies(self) -> list[str]:
        return ["step_08_gen_sub"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证视频和字幕是否存在。"""
        video_path = context.get("video_path")
        subtitle_file = context.get("subtitle_file")
        if not video_path or not subtitle_file:
            logger.error("Missing video_path or subtitle_file")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行字幕烧录。

        Args:
            context: 流水线上下文

        Returns:
            带字幕的视频路径
        """
        logger.info("Starting subtitle burning")

        video_path = context.get("video_path")
        subtitle_file = context.get("subtitle_file")
        output_path = str(paths.output_video_with_sub)

        # 使用 FFmpeg 烧录字幕
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f"subtitles={subtitle_file}",
            '-c:a', 'copy',
            output_path
        ]

        subprocess.run(cmd, check=True)

        logger.info(f"Subtitle burning complete: {output_path}")
        context.set("video_with_sub", output_path)
        return output_path


def create_step() -> BurnSubStep:
    """工厂函数：创建字幕烧录步骤。"""
    return BurnSubStep()


__all__ = ["BurnSubStep", "create_step"]
