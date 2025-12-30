"""
步骤 04: AI 语义分割

使用 LLM 对长句进行语义分割
"""
import asyncio
from pathlib import Path

from src.config import get_settings
from src.utils.paths import SPLIT_BY_MEANING
from src.utils.llm import ask_llm_batch
from src.utils.decorators import async_check_file_exists
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


@async_check_file_exists(SPLIT_BY_MEANING)
async def step_04_meaning_split(nlp_split_file: str, source_language: str = "en") -> str:
    """
    流水线第四步：AI 语义分割

    Args:
        nlp_split_file: NLP 分割结果文件路径
        source_language: 源语言代码

    Returns:
        分割结果文件路径
    """
    logger.info("Starting meaning split with AI")

    # 读取 NLP 分割结果
    # TODO: 实现完整的语义分割逻辑

    # 找出需要分割的长句
    long_sentences = []  # TODO: 从文件中获取

    if long_sentences:
        # 使用 ask_llm_batch 并发处理
        prompts = [f"Split this sentence into meaningful parts: {s}" for s in long_sentences]
        results = await ask_llm_batch(prompts, resp_type="json", max_concurrent=settings.max_workers)

    logger.info(f"Meaning split complete: {SPLIT_BY_MEANING}")
    return str(SPLIT_BY_MEANING)
