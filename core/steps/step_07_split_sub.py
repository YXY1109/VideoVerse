"""Step 07: Split Subtitle.

根据字幕长度限制进行分割和对齐。
从 temp/steps/step_07_split_sub.py 迁移并转换为 PipelineStep。
"""

import re
from typing import List, Tuple

import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.utils.llm import ask_llm

settings = get_settings()


def calc_len(text: str) -> float:
    """计算文本长度（根据不同语言字符权重）。"""
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


def get_joiner(language: str) -> str:
    """获取指定语言的连接符。"""
    joiners = {
        "zh": "",
        "ja": "",
        "ko": "",
        "th": "",
    }
    return joiners.get(language, " ")


def split_sentence(text: str, num_parts: int = 2) -> str:
    """使用 LLM 分割句子。

    Args:
        text: 要分割的文本
        num_parts: 分割数量

    Returns:
        分割后的文本
    """
    from tools.prompts import get_split_prompt

    prompt = get_split_prompt(
        text,
        num_parts=num_parts,
        word_limit=20,
        language=settings.whisper_language
    )

    def valid_split(response_data):
        if "split_text" not in response_data:
            return {"status": "error", "message": "Missing split_text in response"}
        return {"status": "success"}

    result = ask_llm(prompt, resp_type="json", valid_def=valid_split, log_title="split_sentence")
    return result.get("split_text", text)


def align_subs(
    src_sub: str,
    tr_sub: str,
    src_part: str
) -> Tuple[List[str], List[str], str]:
    """对齐源语言和目标语言字幕。

    Args:
        src_sub: 源语言字幕
        tr_sub: 目标语言字幕
        src_part: 分割后的源语言部分

    Returns:
        (源语言部分列表, 目标语言部分列表, 重新合并的目标语言)
    """
    # 尝试从 tools.prompts 导入，如果失败则使用简化版本
    try:
        from tools.prompts import get_align_prompt
        align_prompt = get_align_prompt(src_sub, tr_sub, src_part)
    except ImportError:
        # 简化版本的 prompt
        align_prompt = f"""Align the translated subtitle with the split source subtitle parts.

Source subtitle: {src_sub}
Translated subtitle: {tr_sub}
Split source parts: {src_part}

Please align the translation with the split parts. Return a JSON with 'align' key containing a list of objects, each with 'target_part_1', 'target_part_2', etc. keys."""

    def valid_align(response_data):
        if 'align' not in response_data:
            return {"status": "error", "message": "Missing required key: `align`"}
        if len(response_data['align']) < 2:
            return {"status": "error", "message": "Align does not contain more than 1 part as expected!"}
        return {"status": "success", "message": "Align completed"}

    parsed = ask_llm(align_prompt, resp_type='json', valid_def=valid_align, log_title='align_subs')
    align_data = parsed['align']
    src_parts = src_part.split('\n')
    tr_parts = [item[f'target_part_{i + 1}'].strip() for i, item in enumerate(align_data)]

    language = settings.whisper_language
    joiner = get_joiner(language)
    tr_remerged = joiner.join(tr_parts)

    logger.info(f"Aligned parts:\nSRC_LANG: {' | '.join(src_parts)}\nTARGET_LANG: {' | '.join(tr_parts)}")

    return src_parts, tr_parts, tr_remerged


def split_align_subs(src_lines: List[str], tr_lines: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """分割和对齐字幕。

    Args:
        src_lines: 源语言行列表
        tr_lines: 目标语言行列表

    Returns:
        (分割后的源语言行, 分割后的目标语言行, 重新合并的目标语言行)
    """
    max_sub_length = settings.subtitle_max_length
    target_multiplier = settings.subtitle_target_multiplier
    remerged_tr_lines = tr_lines.copy()

    to_split = []
    for i, (src, tr) in enumerate(zip(src_lines, tr_lines)):
        src, tr = str(src), str(tr)
        if len(src) > max_sub_length or calc_len(tr) * target_multiplier > max_sub_length:
            to_split.append(i)
            logger.info(f"Line {i} needs to be split - Source: {src}, Target: {tr}")

    # 处理需要分割的行
    for i in to_split:
        split_src = split_sentence(src_lines[i], num_parts=2)
        split_src = split_src.strip()
        src_parts, tr_parts, tr_remerged = align_subs(
            src_lines[i], tr_lines[i], split_src
        )
        src_lines[i] = src_parts
        tr_lines[i] = tr_parts
        remerged_tr_lines[i] = tr_remerged

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


class SplitSubStep(PipelineStep):
    """字幕分割优化步骤 - PipelineStep 实现。

    根据字幕长度限制进行分割和对齐。
    """

    @property
    def name(self) -> str:
        return "step_07_split_sub"

    @property
    def dependencies(self) -> list[str]:
        return ["step_06_translate"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证翻译结果是否存在。"""
        translation_result = context.get("translation_result")
        if not translation_result:
            logger.error("No translation_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行字幕分割优化。

        Args:
            context: 流水线上下文

        Returns:
            分割结果文件路径
        """
        logger.info("Starting subtitle split optimization")

        # 读取翻译结果
        translation_result = context.get("translation_result")
        df = pd.read_excel(translation_result)
        src = df['Source'].tolist()
        trans = df['Translation'].tolist()

        max_sub_length = settings.subtitle_max_length
        target_multiplier = settings.subtitle_target_multiplier

        # 多次切割直到所有字幕符合长度要求
        for attempt in range(3):
            logger.info(f"Split attempt {attempt + 1}")
            split_src, split_trans, remerged = split_align_subs(
                src.copy(), trans.copy()
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
        pd.DataFrame({'Source': split_src, 'Translation': split_trans}).to_excel(
            paths.translation_for_subtitles, index=False
        )

        # 保存 remerged 版本
        translation_remerged = paths.translation_for_subtitles.parent / "translation_results_remerged.xlsx"
        pd.DataFrame({'Source': src, 'Translation': remerged}).to_excel(
            translation_remerged, index=False
        )

        logger.info(f"Subtitle split optimization complete: {paths.translation_for_subtitles}")
        context.set("split_sub_result", str(paths.translation_for_subtitles))
        context.set("translation_remerged", str(translation_remerged))
        return str(paths.translation_for_subtitles)


def create_step() -> SplitSubStep:
    """工厂函数：创建字幕分割步骤。"""
    return SplitSubStep()


__all__ = ["SplitSubStep", "create_step"]
