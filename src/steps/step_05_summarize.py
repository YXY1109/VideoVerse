"""
步骤 05: 内容摘要

提取视频内容的摘要和术语表
"""
import asyncio
import json
from pathlib import Path

from src.config import get_settings
from src.utils.paths import TERMINOLOGY
from src.utils.llm import ask_llm
from src.utils.decorators import async_check_file_exists
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@async_check_file_exists(TERMINOLOGY)
async def step_05_summarize(split_file: str, target_language: str = "zh") -> str:
    """
    流水线第五步：内容摘要和术语提取

    Args:
        split_file: 分割结果文件路径
        target_language: 目标语言代码

    Returns:
        术语表文件路径
    """
    logger.info("Starting summarization")

    # TODO: 从 core/_4_1_summarize.py 迁移
    # 构建摘要 prompt
    # summary_prompt = f"Summarize the following content and extract terminology..."

    # result = await ask_llm(summary_prompt, resp_type="json")

    # 保存术语表
    terminology = {
        "theme": "Video content summary",
        "terminology": []
    }

    # 确保目录存在
    TERMINOLOGY.parent.mkdir(parents=True, exist_ok=True)
    with open(TERMINOLOGY, 'w', encoding='utf-8') as f:
        json.dump(terminology, f, ensure_ascii=False, indent=2)

    logger.info(f"Summarization complete: {TERMINOLOGY}")
    return str(TERMINOLOGY)
