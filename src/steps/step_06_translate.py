"""
步骤 06: 翻译

使用 LLM 进行多步翻译（直译 → 反思 → 意译）
"""
import asyncio
from pathlib import Path

from src.config import get_settings
from src.utils.paths import TRANSLATION_RESULTS, TERMINOLOGY
from src.utils.llm import ask_llm_batch
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


async def translate_chunk_async(
    chunk: str,
    target_language: str,
    terminology: str,
    index: int
) -> tuple[int, str]:
    """异步翻译单个文本块"""
    # TODO: 从 core/translate_lines.py 迁移三步翻译逻辑
    # 1. 直译
    # 2. 反思
    # 3. 意译

    # 简化版实现
    prompt = f"Translate to {target_language}: {chunk}"
    result = await ask_llm(prompt, log_title=f"translate_{index}")

    return index, result


@async_check_file_exists(TRANSLATION_RESULTS)
async def step_06_translate(
    split_file: str,
    terminology_file: str,
    target_language: str = "zh"
) -> str:
    """
    流水线第六步：翻译

    Args:
        split_file: 分割结果文件路径
        terminology_file: 术语表文件路径
        target_language: 目标语言代码

    Returns:
        翻译结果文件路径
    """
    logger.info(f"Starting translation to {target_language}")

    # 读取术语表
    with open(terminology_file, 'r', encoding='utf-8') as f:
        import json
        terminology = json.load(f)
    theme_prompt = terminology.get('theme', '')

    # 读取需要翻译的文本
    # TODO: 实现完整的文本读取逻辑
    chunks = []  # 从文件读取的文本块

    if chunks:
        # 使用 asyncio.gather 并发翻译
        tasks = [
            translate_chunk_async(chunk, target_language, theme_prompt, i)
            for i, chunk in enumerate(chunks)
        ]
        results = await asyncio.gather(*tasks)

        # 按顺序排序结果
        results.sort(key=lambda x: x[0])

    # 保存翻译结果
    # TODO: 实现结果保存逻辑

    logger.info(f"Translation complete: {TRANSLATION_RESULTS}")
    return str(TRANSLATION_RESULTS)
