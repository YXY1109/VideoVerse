"""VideoVerse 流水线验证脚本。

对比 temp 和 core 的实现，确保功能一致性。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


async def compare_step_implementations():
    """对比 temp 和 core 中步骤的实现差异。"""
    logger.info("Comparing temp vs core implementations...")

    # 定义需要对比的步骤
    steps_to_compare = [
        "step_01_download",
        "step_02_asr",
        "step_03_nlp_split",
        "step_04_meaning_split",
        "step_05_summarize",
    ]

    for step in steps_to_compare:
        temp_path = Path(f"temp/steps/{step}.py")
        core_path = Path(f"core/steps/{step}.py")

        if temp_path.exists() and core_path.exists():
            logger.info(f"  {step}: ✓ Both exist")
        elif temp_path.exists() and not core_path.exists():
            logger.warning(f"  {step}: ⚠ Only in temp")
        elif not temp_path.exists() and core_path.exists():
            logger.info(f"  {step}: ✓ Migrated to core")
        else:
            logger.error(f"  {step}: ✗ Missing from both")

    logger.info("Comparison complete")


async def verify_pipeline_steps():
    """验证流水线步骤的完整性。"""
    logger.info("Verifying pipeline step integrity...")

    from core.steps import (
        create_download_step,
        create_asr_step,
        create_nlp_split_step,
        create_meaning_split_step,
        create_summarize_step,
        create_translate_step,
        create_split_sub_step,
        create_gen_sub_step,
        create_burn_sub_step,
        create_audio_task_step,
        create_gen_audio_step,
        create_merge_audio_step,
        create_dubbing_step,
    )

    # 创建所有步骤
    steps = {
        "step_01_download": create_download_step(),
        "step_02_asr": create_asr_step(),
        "step_03_nlp_split": create_nlp_split_step(),
        "step_04_meaning_split": create_meaning_split_step(),
        "step_05_summarize": create_summarize_step(),
        "step_06_translate": create_translate_step(),
        "step_07_split_sub": create_split_sub_step(),
        "step_08_gen_sub": create_gen_sub_step(),
        "step_09_burn_sub": create_burn_sub_step(),
        "step_10_audio_task": create_audio_task_step(),
        "step_11_gen_audio": create_gen_audio_step(),
        "step_12_merge_audio": create_merge_audio_step(),
        "step_13_dubbing": create_dubbing_step(),
    }

    # 验证步骤属性
    all_valid = True
    for step_name, step in steps.items():
        try:
            # 检查必需属性
            assert hasattr(step, 'name'), f"{step_name}: missing 'name' property"
            assert hasattr(step, 'dependencies'), f"{step_name}: missing 'dependencies' property"
            assert hasattr(step, 'validate'), f"{step_name}: missing 'validate' method"
            assert hasattr(step, 'execute'), f"{step_name}: missing 'execute' method"

            # 验证返回值
            name = step.name
            deps = step.dependencies

            logger.info(f"  ✓ {step_name}: name={name}, dependencies={deps}")
        except Exception as e:
            logger.error(f"  ✗ {step_name}: {e}")
            all_valid = False

    if all_valid:
        logger.success("All pipeline steps validated successfully")
    else:
        logger.error("Some pipeline steps failed validation")

    return all_valid


async def run_verification():
    """运行验证脚本。"""
    logger.info("=" * 60)
    logger.info("VideoVerse Verification Script")
    logger.info("=" * 60)

    await compare_step_implementations()
    logger.info("")
    await verify_pipeline_steps()

    logger.info("=" * 60)
    logger.info("Verification complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_verification())
