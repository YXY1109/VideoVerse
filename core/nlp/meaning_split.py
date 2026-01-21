"""AI 语义分割模块 - 将长句子按语义边界分割成适合字幕的片段。

该模块使用 LLM 将过长的句子按语义边界分割，确保每个片段适合字幕显示。
"""

from __future__ import annotations

import concurrent.futures
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import jieba
from loguru import logger

from core.nlp.nlp_split import load_spacy_model
from core.utils.llm import ask_llm
from core.utils.prompts import get_split_prompt

if TYPE_CHECKING:
    from spacy import Language


# ==================== 常量定义 ====================
class Config:
    """语义分割配置常量"""
    # 分割参数
    MAX_SEGMENT_LENGTH = 20          # 每个片段最大字符/词数
    MIN_SEGMENT_LENGTH = 3           # 每个片段最小字符/词数
    MAX_WORKERS = 5                  # 最大并行工作线程数
    MAX_RETRIES = 3                  # 最大重试次数

    # 验证参数
    COVERAGE_MIN_RATIO = 0.6         # 分割结果最小覆盖率
    COVERAGE_MAX_RATIO = 1.4         # 分割结果最大覆盖率
    NON_STRICT_TOLERANCE = 0.3       # 非严格模式允许超出的比例


# ==================== 类型定义 ====================
@dataclass(frozen=True)
class SplitRequest:
    """分割请求参数"""
    sentence: str
    num_parts: int
    word_limit: int = Config.MAX_SEGMENT_LENGTH
    language: str = "zh"
    index: int = -1


@dataclass(frozen=True)
class ValidationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""


# ==================== 主入口函数 ====================
def process_meaning_split(sentences: list[str], source_language: str = "en") -> list[str]:
    """流水线第四步：AI 语义分割

    Args:
        sentences: NLP 分割后的句子列表
        source_language: 源语言代码 (如 "zh", "en")

    Returns:
        分割后的句子列表
    """
    logger.info(f"Starting meaning split with AI, language: {source_language}")

    # 加载分词模型
    nlp = None if source_language == "zh" else load_spacy_model(source_language)
    if source_language == "zh":
        logger.info("Using jieba for Chinese tokenization")

    # 并行处理
    result = _parallel_split(sentences, source_language, nlp)

    logger.info(f"Meaning split completed, total {len(result)} segments")
    return result


# ==================== 核心分割逻辑 ====================
def _parallel_split(
    sentences: list[str],
    language: str,
    nlp: Language | None,
) -> list[str]:
    """并行分割句子列表"""
    results: list[list[str] | None] = [None] * len(sentences)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(Config.MAX_WORKERS, len(sentences))
    ) as executor:
        futures = {}

        for idx, sentence in enumerate(sentences):
            if not sentence or not sentence.strip():
                results[idx] = []
                continue

            # 计算是否需要分割
            num_parts = _calculate_split_parts(sentence, language, Config.MAX_SEGMENT_LENGTH)

            if num_parts > 1:
                request = SplitRequest(sentence, num_parts, Config.MAX_SEGMENT_LENGTH, language, idx)
                futures[executor.submit(_split_with_retry, request)] = idx
            else:
                results[idx] = [sentence]

        # 收集结果
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            try:
                split_result = future.result()
                results[idx] = split_result if split_result else [sentences[idx]]
            except Exception as e:
                logger.error(f"Error splitting sentence at index {idx}: {e}")
                results[idx] = [sentences[idx]]

    # 扁平化结果
    return [seg for parts in results if parts for seg in parts]


def _split_with_retry(request: SplitRequest) -> list[str] | None:
    """带重试机制的分割

    采用渐进式策略：
    - 前 2 次：严格模式
    - 第 3 次：非严格模式（允许轻微超出限制）
    """
    if not request.sentence or not request.sentence.strip():
        return None

    for attempt in range(Config.MAX_RETRIES):
        strict = attempt < 2
        prompt = _build_split_prompt(request, attempt)

        try:
            response = ask_llm(prompt, log_title="split_by_meaning")
            choice = response.get("choice", "1")
            content = response.get(f"split{choice}", "")

            if not content:
                continue

            segments = _extract_and_validate_segments(
                content, request.sentence, request.language,
                request.word_limit, request.num_parts, strict
            )

            if segments:
                if request.index != -1:
                    logger.info(f"Sentence {request.index} split into {len(segments)} parts (attempt {attempt + 1})")
                    _log_split_result(request.sentence, segments)
                return segments

        except Exception as e:
            logger.error(f"Attempt {attempt + 1}: {e}")
            if attempt == Config.MAX_RETRIES - 1:
                return None

    logger.warning(f"Failed to split after {Config.MAX_RETRIES} attempts: {request.sentence[:50]}...")
    return None


# ==================== 辅助函数 ====================
def _calculate_split_parts(sentence: str, language: str, max_length: int) -> int:
    """计算需要分割成几部分"""
    if language == "zh":
        length = len(sentence)
    else:
        # 英文按空格分词后计算
        length = len(sentence.split())
    return max(1, math.ceil(length / max_length))


def _build_split_prompt(request: SplitRequest, attempt: int) -> str:
    """构建分割提示词，添加重试信息"""
    prompt = get_split_prompt(
        request.sentence, request.num_parts,
        request.word_limit, language=request.language
    )

    if attempt == 0:
        return prompt

    unit = "字" if request.language == "zh" else "词"
    retry_msg = (
        f"\n\n## RETRY {attempt + 1}/{Config.MAX_RETRIES}\n"
        f"Previous attempt failed. Ensure:\n"
        f"1. Each part ≤ {request.word_limit} {unit}\n"
        f"2. Exactly {request.num_parts} parts"
    )

    if attempt == 2:  # 非严格模式提示
        max_allowed = int(request.word_limit * 1.3)
        retry_msg += f"\n3. If necessary, may exceed up to {max_allowed} {unit} for coherence"

    return prompt + retry_msg


def _extract_and_validate_segments(
    content: str,
    original: str,
    language: str,
    limit: int,
    expected_parts: int,
    strict: bool,
) -> list[str] | None:
    """提取并验证分割片段"""
    # 提取片段
    parts = _parse_split_content(content)
    if not parts:
        return None

    # 过滤过短片段
    parts = _filter_short_parts(parts, language)
    if not parts:
        return None

    # 验证片段数量
    if len(parts) != expected_parts:
        logger.warning(f"Part count mismatch: expected {expected_parts}, got {len(parts)}")
        return None

    # 验证长度限制
    validation = _validate_length(parts, language, limit, strict)
    if not validation.is_valid:
        logger.warning(f"Length validation failed: {validation.reason}")
        return None

    # 验证覆盖率
    if not _validate_coverage(original, parts, language):
        logger.warning(f"Coverage validation failed")
        return None

    return parts


def _parse_split_content(content: str) -> list[str] | None:
    """解析分割内容，支持 [br] 标记或换行符"""
    if "[br]" in content:
        parts = content.split("[br]")
    else:
        parts = content.split("\n")
        parts = [p for p in parts if p.strip()]

    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else None


def _filter_short_parts(parts: list[str], language: str) -> list[str]:
    """过滤过短的片段"""
    min_len = Config.MIN_SEGMENT_LENGTH
    if language != "zh":
        # 英文按词数计算最小长度
        return [p for p in parts if len(p.split()) >= min_len]

    filtered = [p for p in parts if len(p) >= min_len]
    if len(filtered) != len(parts):
        logger.info(f"Filtered {len(parts) - len(filtered)} short parts")
    return filtered


def _validate_length(
    parts: list[str],
    language: str,
    limit: int,
    strict: bool,
) -> ValidationResult:
    """验证片段长度"""
    tolerance = Config.NON_STRICT_TOLERANCE
    max_allowed = int(limit * (1 + tolerance))

    for i, part in enumerate(parts):
        length = len(part) if language == "zh" else len(part.split())

        if length > limit:
            if strict:
                return ValidationResult(False, f"Part {i+1}: {length} > {limit}")
            if length > max_allowed:
                return ValidationResult(False, f"Part {i+1}: {length} > {max_allowed}")
            logger.info(f"Part {i+1} slightly exceeds limit: {length} vs {limit}")

    return ValidationResult(True)


def _validate_coverage(original: str, parts: list[str], language: str) -> bool:
    """验证分割覆盖率"""
    if language == "zh":
        original_len = len(original)
        split_len = sum(len(p) for p in parts)
    else:
        original_len = len(original.split())
        split_len = sum(len(p.split()) for p in parts)

    if original_len == 0:
        return False

    ratio = split_len / original_len
    return Config.COVERAGE_MIN_RATIO <= ratio <= Config.COVERAGE_MAX_RATIO


def _log_split_result(original: str, segments: list[str]) -> None:
    """记录分割结果"""
    logger.info(f"[Split] Original: {original}")
    logger.info(f"[Split] Result: {' || '.join(segments)}")


# ==================== 向后兼容 ====================
def tokenize_sentence(sentence: str, nlp: Language | None, use_jieba: bool = False) -> list[str]:
    """对句子进行分词（向后兼容）"""
    if use_jieba:
        return list(jieba.cut(sentence))
    if nlp:
        return [token.text for token in nlp(sentence)]
    return sentence.split()
