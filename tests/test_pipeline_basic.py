"""测试前 3 个步骤的流水线。

用于验证核心功能是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from core.config import get_settings
from core.pipeline import PipelineEngine, StepRegistry
from core.paths import paths
from core.steps import create_download_step, create_asr_step


async def run_first_3_steps():
    """运行前 3 个步骤：下载、ASR、NLP 分割。"""
    logger.info("=" * 60)
    logger.info("VideoVerse Pipeline Test - First 3 Steps")
    logger.info("=" * 60)

    # 获取配置
    settings = get_settings()
    logger.info(f"Configuration:")
    logger.info(f"  openai_model: {settings.openai_model}")
    logger.info(f"  tts_method: {settings.tts_method}")
    logger.info(f"  whisper_runtime: {settings.whisper_runtime}")
    logger.info(f"  whisper_model: {settings.whisper_model}")
    logger.info(f"  output_dir: {settings.output_dir}")

    # 创建注册表并注册步骤
    registry = StepRegistry()
    registry.register("step_01_download", create_download_step())
    registry.register("step_02_asr", create_asr_step())

    # 创建流水线引擎
    engine = PipelineEngine(registry)

    # 确保输出目录存在
    paths.ensure_directories()

    # 配置视频源 - 使用 demo 视频
    video_source = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"
    source_language = "zh"
    target_language = "en"

    logger.info(f"")
    logger.info(f"Pipeline Configuration:")
    logger.info(f"  Video source: {video_source}")
    logger.info(f"  Languages: {source_language} -> {target_language}")
    logger.info(f"")

    # 运行流水线（前 2 个步骤，因为 NLP 分割需要 spacy）
    steps_to_run = [
        "step_01_download",
        "step_02_asr",
    ]

    try:
        logger.info(f"Running pipeline steps: {steps_to_run}")
        context = await engine.run(
            steps=steps_to_run,
            video_source=video_source,
            source_language=source_language,
            target_language=target_language,
        )

        logger.success("Pipeline completed successfully!")
        logger.info(f"")
        logger.info(f"Results:")
        for key in ["video_path", "asr_result", "cleaned_chunks"]:
            value = context.get(key)
            if value:
                logger.info(f"  - {key}: {value}")

        return context

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(run_first_3_steps())
    sys.exit(0 if result else 1)
