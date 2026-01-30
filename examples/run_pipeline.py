"""VideoVerse 运行示例。

演示如何使用 core 模块运行流水线。
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
from core.steps import (
    create_download_step,
    create_asr_step,
    create_nlp_split_step,
    create_meaning_split_step,
    create_summarize_step,
)


async def run_simple_pipeline():
    """运行简化的流水线示例。

    这个示例演示如何使用 core 模块运行前 5 个步骤。
    """
    logger.info("=" * 60)
    logger.info("VideoVerse Simple Pipeline Example")
    logger.info("=" * 60)

    # 获取配置
    settings = get_settings()
    logger.info(f"Configuration: openai_model={settings.openai_model}, tts_method={settings.tts_method}")

    # 创建注册表并注册步骤
    registry = StepRegistry()

    # 注册前 5 个步骤
    registry.register("step_01_download", create_download_step())
    registry.register("step_02_asr", create_asr_step())
    registry.register("step_03_nlp_split", create_nlp_split_step())
    registry.register("step_04_meaning_split", create_meaning_split_step())
    registry.register("step_05_summarize", create_summarize_step())

    # 创建流水线引擎
    engine = PipelineEngine(registry)

    # 确保输出目录存在
    paths.ensure_directories()

    # 配置视频源
    # 这里使用本地视频文件作为示例
    video_source = r"D:\PycharmProjects\VideoVerse\files\demo.mp4"  # 替换为你的视频路径
    source_language = "zh"
    target_language = "en"

    logger.info(f"Video source: {video_source}")
    logger.info(f"Languages: {source_language} -> {target_language}")

    # 运行流水线（前 5 个步骤）
    steps_to_run = [
        "step_01_download",
        "step_02_asr",
        "step_03_nlp_split",
        "step_04_meaning_split",
        "step_05_summarize",
    ]

    try:
        context = await engine.run(
            steps=steps_to_run,
            video_source=video_source,
            source_language=source_language,
            target_language=target_language,
        )

        logger.success("Pipeline completed successfully!")
        logger.info(f"Output files are in: {paths.output_dir}")

        # 显示上下文中的结果
        logger.info("Results:")
        for key in ["video_path", "nlp_split_result", "meaning_split_result", "terminology"]:
            value = context.get(key)
            if value:
                logger.info(f"  - {key}: {value}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


def run_sync_pipeline():
    """同步运行流水线（兼容旧代码）。"""
    asyncio.run(run_simple_pipeline())


# 测试单个步骤
async def test_single_step():
    """测试单个步骤。"""
    logger.info("=" * 60)
    logger.info("Testing Single Step")
    logger.info("=" * 60)

    from core.steps import create_download_step
    from core.pipeline.context import PipelineContext
    from core.config import get_settings

    # 创建步骤
    step = create_download_step()

    # 创建上下文
    settings = get_settings()
    context = PipelineContext(
        video_source="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        source_language="en",
        target_language="zh",
        config=settings,
        storage={}
    )

    # 验证步骤
    is_valid = await step.validate(context)
    logger.info(f"Step validation: {is_valid}")

    # 显示步骤信息
    logger.info(f"Step name: {step.name}")
    logger.info(f"Dependencies: {step.dependencies}")


if __name__ == "__main__":
    # 选择运行模式
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_single_step())
    else:
        run_sync_pipeline()
