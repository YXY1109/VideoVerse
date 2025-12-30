"""
步骤 03: NLP 句子分割

使用 Spacy/jieba 对文本进行语言学分割
"""
import asyncio
from pathlib import Path

from src.config import get_settings
from src.utils.paths import SPLIT_BY_NLP
from src.utils.decorators import async_check_file_exists

from loguru import logger
settings = get_settings()


def split_by_nlp_sync(text: str, language: str) -> str:
    """同步 NLP 分割（使用 asyncio.to_thread 包装）"""
    # TODO: 从 core/_3_1_split_nlp.py 迁移
    # 这里暂时返回原文本
    return text


@async_check_file_exists(SPLIT_BY_NLP)
async def step_03_nlp_split(transcript_file: str, source_language: str = "en") -> str:
    """
    流水线第三步：NLP 句子分割

    Args:
        transcript_file: 转录文件路径
        source_language: 源语言代码

    Returns:
        分割结果文件路径
    """
    logger.info("Starting NLP split")

    # 读取转录文件
    # TODO: 实现完整的 NLP 分割逻辑

    # Spacy 不支持异步，使用 asyncio.to_thread
    # result = await asyncio.to_thread(split_by_nlp_sync, text, source_language)

    logger.info(f"NLP split complete: {SPLIT_BY_NLP}")
    return str(SPLIT_BY_NLP)
