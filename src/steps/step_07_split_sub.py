"""
步骤 07: 字幕分割优化

根据字幕长度限制进行分割和对齐
"""
import asyncio
import re
from typing import List, Tuple

import pandas as pd

from src.config import get_settings
from src.utils.paths import TRANSLATION_FOR_SUBTITLES, TRANSLATION_REMERGED, TRANSLATION_RESULTS
from src.utils.decorators import async_check_file_exists
from src.utils.llm import ask_llm
from src.tools.prompts import get_align_prompt
from src.steps.step_04_meaning_split import split_sentence, get_joiner

from loguru import logger
settings = get_settings()


def calc_len(text: str) -> float:
    """计算文本长度（根据不同语言字符权重）"""
    text = str(text)

    def char_weight(char):
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x30FF:  # 中文和日文
            return 1.75
        elif 0xAC00 <= code <= 0xD7A3 or 0x1100 <= code <= 0x11FF:  # 韩文
            return 1.5
        elif 0x0E00 <= code <= 0x0E7F:  # 泰文
            return 1
        elif 0xFF01 <= code <= 0xFF5E:  # 全角符号
            return 1.75
        else:  # 其他字符（如英文和半角符号）
            return 1

    return sum(char_weight(char) for char in text)


async def align_subs_async(
    src_sub: str,
    tr_sub: str,
    src_part: str
) -> Tuple[List[str], List[str], str]:
    """异步对齐源语言和目标语言字幕"""
    align_prompt = get_align_prompt(src_sub, tr_sub, src_part)

    def valid_align(response_data):
        if 'align' not in response_data:
            return {"status": "error", "message": "Missing required key: `align`"}
        if len(response_data['align']) < 2:
            return {"status": "error", "message": "Align does not contain more than 1 part as expected!"}
        return {"status": "success", "message": "Align completed"}

    parsed = await ask_llm(align_prompt, resp_type='json', valid_def=valid_align, log_title='align_subs')
    align_data = parsed['align']
    src_parts = src_part.split('\n')
    tr_parts = [item[f'target_part_{i + 1}'].strip() for i, item in enumerate(align_data)]

    language = settings.whisper_language
    joiner = get_joiner(language)
    tr_remerged = joiner.join(tr_parts)

    logger.info(f"Aligned parts:\nSRC_LANG: {' | '.join(src_parts)}\nTARGET_LANG: {' | '.join(tr_parts)}")

    return src_parts, tr_parts, tr_remerged


async def split_align_subs_async(src_lines: List[str], tr_lines: List[str]):
    """异步分割和对齐字幕"""
    max_sub_length = settings.subtitle_max_length
    target_multiplier = settings.subtitle_target_multiplier
    remerged_tr_lines = tr_lines.copy()

    to_split = []
    for i, (src, tr) in enumerate(zip(src_lines, tr_lines)):
        src, tr = str(src), str(tr)
        if len(src) > max_sub_length or calc_len(tr) * target_multiplier > max_sub_length:
            to_split.append(i)
            logger.info(f"Line {i} needs to be split - Source: {src}, Target: {tr}")

    # 并发处理需要分割的行
    async def process_split(i):
        split_src = await split_sentence(src_lines[i], num_parts=2)
        split_src = split_src.strip()
        src_parts, tr_parts, tr_remerged = await align_subs_async(
            src_lines[i], tr_lines[i], split_src
        )
        src_lines[i] = src_parts
        tr_lines[i] = tr_parts
        remerged_tr_lines[i] = tr_remerged

    for i in to_split:
        await process_split(i)

    # 展平 src_lines 和 tr_lines
    src_lines = [
        item for sublist in src_lines
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]
    tr_lines = [
        item for sublist in tr_lines
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]

    return src_lines, tr_lines, remerged_tr_lines


@async_check_file_exists(TRANSLATION_FOR_SUBTITLES)
async def step_07_split_sub(translation_file: str = None) -> str:
    """
    流水线第七步：字幕分割优化

    Args:
        translation_file: 翻译结果文件路径

    Returns:
        分割后的字幕文件路径
    """
    logger.info("Starting subtitle split")

    if translation_file is None:
        translation_file = str(TRANSLATION_RESULTS)

    df = await asyncio.to_thread(pd.read_excel, translation_file)
    src = df['Source'].tolist()
    trans = df['Translation'].tolist()

    max_sub_length = settings.subtitle_max_length
    target_multiplier = settings.subtitle_target_multiplier

    # 多次切割直到所有字幕符合长度要求
    for attempt in range(3):
        logger.info(f"Split attempt {attempt + 1}")
        split_src, split_trans, remerged = await split_align_subs_async(
            src.copy(), trans
        )

        # 检查是否所有字幕都符合长度要求
        if all(len(s) <= max_sub_length for s in split_src) and \
           all(calc_len(t) * target_multiplier <= max_sub_length for t in split_trans):
            break

        # 更新源数据继续下一轮分割
        src, trans = split_src, split_trans

    # 确保二者有相同的长度
    if len(src) > len(remerged):
        remerged += [None] * (len(src) - len(remerged))
    elif len(remerged) > len(src):
        src += [None] * (len(remerged) - len(src))

    # 保存结果
    await asyncio.to_thread(
        lambda: pd.DataFrame({'Source': split_src, 'Translation': split_trans}).to_excel(
            TRANSLATION_FOR_SUBTITLES, index=False
        )
    )
    await asyncio.to_thread(
        lambda: pd.DataFrame({'Source': src, 'Translation': remerged}).to_excel(
            TRANSLATION_REMERGED, index=False
        )
    )

    logger.info(f"Subtitle split complete: {TRANSLATION_FOR_SUBTITLES}")
    return str(TRANSLATION_FOR_SUBTITLES)
