"""Step 13: Dubbing.

最终配音合成。
从 temp/steps/step_13_dubbing.py 迁移并转换为 PipelineStep（简化版）。
"""

import subprocess
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

settings = get_settings()


class DubbingStep(PipelineStep):
    """配音合成步骤 - PipelineStep 实现。

    将合并后的音频与视频合成最终配音视频。
    """

    @property
    def name(self) -> str:
        return "step_13_dubbing"

    @property
    def dependencies(self) -> list[str]:
        return ["step_09_burn_sub", "step_12_merge_audio"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证视频和音频是否存在。"""
        video_path = context.get("video_path")
        merged_audio = context.get("merged_audio")
        if not video_path or not merged_audio:
            logger.error("Missing video_path or merged_audio")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行配音合成。

        Args:
            context: 流水线上下文

        Returns:
            配音视频路径
        """
        logger.info("Starting dubbing composition")

        video_path = context.get("video_path")
        merged_audio = context.get("merged_audio")
        output_path = str(paths.output_video_dubbed)

        # 使用 FFmpeg 替换音频
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', merged_audio,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            output_path
        ]

        subprocess.run(cmd, check=True)

        logger.info(f"Dubbing composition complete: {output_path}")
        context.set("dubbed_video", output_path)
        return output_path


def create_step() -> DubbingStep:
    """工厂函数：创建配音合成步骤。"""
    return DubbingStep()


__all__ = ["DubbingStep", "create_step"]
