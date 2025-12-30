"""
步骤 03: NLP 句子分割

使用 Spacy/jieba 对文本进行语言学分割
"""
import asyncio
import pandas as pd
from pathlib import Path

from src.config import get_settings
from src.utils.paths import SPLIT_BY_NLP, SPLIT_BY_MEANING
from src.utils.decorators import async_check_file_exists
from src.tools.spacy_utils import (
    split_by_mark,
    split_by_comma_main,
    split_sentences_main,
    split_long_by_root_main,
    init_nlp,
    split_by_mark_jieba,
    split_by_comma_jieba_main,
    split_sentences_jieba_main,
    split_long_by_root_jieba_main,
    JIEBA_AVAILABLE
)

from loguru import logger
settings = get_settings()


def split_by_spacy_sync() -> None:
    """使用 Spacy 进行 NLP 分割"""
    nlp = init_nlp()
    split_by_mark(nlp)
    split_by_comma_main(nlp)
    split_sentences_main(nlp)
    split_long_by_root_main(nlp)


def split_by_jieba_sync() -> None:
    """使用 jieba 进行中文 NLP 分割"""
    logger.info("Using jieba for Chinese text splitting")
    split_by_mark_jieba()
    split_by_comma_jieba_main()
    split_sentences_jieba_main()
    split_long_by_root_jieba_main()


def split_by_nlp_sync(transcript_file: str, source_language: str) -> None:
    """同步 NLP 分割"""
    # 根据语言自动选择 Spacy 或 jieba 进行 NLP 分割
    # 中文优先使用 jieba（如果可用）
    if source_language == 'zh' and JIEBA_AVAILABLE:
        split_by_jieba_sync()
    else:
        split_by_spacy_sync()


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

    # 读取转录文件获取句子
    df = pd.read_excel(transcript_file)
    sentences = df['text'].str.strip('"').str.strip().tolist()

    # 写入到 split_by_meaning.txt（中间文件）
    SPLIT_BY_MEANING.parent.mkdir(parents=True, exist_ok=True)
    with open(SPLIT_BY_MEANING, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sentences))

    # 使用 asyncio.to_thread 执行同步的 NLP 分割
    await asyncio.to_thread(split_by_nlp_sync, transcript_file, source_language)

    logger.info(f"NLP split complete: {SPLIT_BY_NLP}")
    return str(SPLIT_BY_NLP)
