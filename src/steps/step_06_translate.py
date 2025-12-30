"""
步骤 06: 翻译

使用 LLM 进行多步翻译（直译 → 反思 → 意译）
"""
import asyncio
import json
from difflib import SequenceMatcher

import pandas as pd

from src.config import get_settings
from src.utils.paths import TRANSLATION_RESULTS, TERMINOLOGY, SPLIT_BY_MEANING
from src.utils.decorators import async_check_file_exists
from src.tools.translate_lines import translate_lines_async
from src.steps.step_05_summarize import search_things_to_note_in_prompt

from loguru import logger
settings = get_settings()


def similar(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()


def split_chunks_by_chars(chunk_size: int, max_i: int, split_file: str) -> list:
    """根据字符数分割文本块"""
    with open(split_file, "r", encoding="utf-8") as file:
        sentences = file.read().strip().split('\n')

    chunks = []
    chunk = ''
    sentence_count = 0
    for sentence in sentences:
        if len(chunk) + len(sentence + '\n') > chunk_size or sentence_count == max_i:
            if chunk.strip():
                chunks.append(chunk.strip())
            chunk = sentence + '\n'
            sentence_count = 1
        else:
            chunk += sentence + '\n'
            sentence_count += 1
    if chunk.strip():
        chunks.append(chunk.strip())
    return chunks


def get_previous_content(chunks: list, chunk_index: int) -> str:
    """获取前文内容"""
    if chunk_index == 0:
        return None
    return chunks[chunk_index - 1].split('\n')[-3:]


def get_after_content(chunks: list, chunk_index: int) -> str:
    """获取后文内容"""
    if chunk_index == len(chunks) - 1:
        return None
    return chunks[chunk_index + 1].split('\n')[:2]


async def translate_chunk_async(
    chunk: str,
    chunks: list,
    theme_prompt: str,
    index: int,
) -> tuple:
    """异步翻译单个文本块"""
    things_to_note_prompt = search_things_to_note_in_prompt(chunk)
    previous_content_prompt = get_previous_content(chunks, index)
    after_content_prompt = get_after_content(chunks, index)
    translation, english_result = await translate_lines_async(
        chunk, previous_content_prompt, after_content_prompt,
        things_to_note_prompt, theme_prompt, index
    )
    return index, english_result, translation


@async_check_file_exists(TRANSLATION_RESULTS)
async def step_06_translate(
    split_file: str = None,
    terminology_file: str = None,
    target_language: str = None
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
    logger.info("Starting translation")

    # 使用默认值
    if split_file is None:
        split_file = str(SPLIT_BY_MEANING)
    if terminology_file is None:
        terminology_file = str(TERMINOLOGY)
    if target_language is None:
        target_language = settings.target_language

    # 分割文本块
    chunks = split_chunks_by_chars(chunk_size=600, max_i=10, split_file=split_file)

    # 读取术语表
    with open(terminology_file, 'r', encoding='utf-8') as f:
        terminology_data = json.load(f)
    theme_prompt = terminology_data.get('theme', '')

    # 并发翻译所有文本块
    logger.info(f"Translating {len(chunks)} chunks...")
    tasks = [
        translate_chunk_async(chunk, chunks, theme_prompt, i)
        for i, chunk in enumerate(chunks)
    ]
    results = await asyncio.gather(*tasks)

    # 按原始顺序排序结果
    results.sort(key=lambda x: x[0])

    # 构建翻译结果
    src_text, trans_text = [], []
    for i, chunk in enumerate(chunks):
        chunk_lines = chunk.split('\n')
        src_text.extend(chunk_lines)

        # 计算相似度并找到最佳匹配
        chunk_text = ''.join(chunk_lines).lower()
        matching_results = [
            (r, similar(''.join(r[1].split('\n')).lower(), chunk_text))
            for r in results
        ]
        best_match = max(matching_results, key=lambda x: x[1])

        # 检查相似度
        if best_match[1] < 0.9:
            logger.warning(f"Warning: No matching translation found for chunk {i}")
            raise ValueError(f"Translation matching failed (chunk {i})")
        elif best_match[1] < 1.0:
            logger.warning(f"Warning: Similar match found (chunk {i}, similarity: {best_match[1]:.3f})")

        trans_text.extend(best_match[0][2].split('\n'))

    # 保存翻译结果
    df_final = pd.DataFrame({'Source': src_text, 'Translation': trans_text})
    await asyncio.to_thread(df_final.to_excel, TRANSLATION_RESULTS, index=False)

    logger.info(f"Translation complete: {TRANSLATION_RESULTS}")
    return str(TRANSLATION_RESULTS)
