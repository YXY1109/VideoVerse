"""
步骤 04: AI 语义分割

使用 LLM 对长句进行语义分割
"""
import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from pathlib import Path

from src.config import get_settings
from src.utils.paths import SPLIT_BY_MEANING
from src.utils.decorators import async_check_file_exists
from src.tools.prompts import get_split_prompt
from src.tools.spacy_utils.load_nlp_model import init_nlp
from src.utils.llm import ask_llm

from loguru import logger
settings = get_settings()

# 尝试导入 jieba（中文分词）
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


def get_joiner(language: str) -> str:
    """获取语言连接符"""
    return '' if language == 'zh' else ' '


def tokenize_sentence(sentence: str, nlp, use_jieba: bool = False):
    """Tokenize a sentence using Spacy or jieba (for Chinese)"""
    if use_jieba and JIEBA_AVAILABLE:
        return list(jieba.cut(sentence))
    else:
        doc = nlp(sentence)
        return [token.text for token in doc]


def find_split_positions(original: str, modified: str) -> list:
    """找到分割位置

    将 LLM 返回的带 [br] 标记的分割结果映射回原始句子的字符位置
    """
    split_positions = []
    parts = modified.split('[br]')
    start = 0
    language = settings.whisper_language
    joiner = get_joiner(language)

    # 清理 parts：去除空白和无效部分
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        logger.warning("No valid [br] split markers found in LLM response")
        return []

    for i in range(len(parts) - 1):
        current_part = parts[i]

        # 对于中文，确保当前部分至少包含 3 个字符
        if language == 'zh' and len(current_part) < 3:
            logger.warning(f"Part {i + 1} too short ({len(current_part)} chars): '{current_part}', skipping")
            # 将当前部分与下一部分合并，继续查找
            continue

        max_similarity = 0
        best_split = None

        # 在原始句子中查找与当前部分最佳匹配的位置
        for j in range(start + min(3, len(original) - start), len(original)):
            original_left = original[start:j]

            # 对于中文，直接比较字符串
            # 对于英文，需要处理空格
            if language == 'zh':
                modified_left = current_part
            else:
                modified_left = joiner.join(current_part.split())

            left_similarity = SequenceMatcher(None, original_left, modified_left).ratio()

            if left_similarity > max_similarity:
                max_similarity = left_similarity
                best_split = j

            # 如果相似度很高，提前结束查找
            if left_similarity >= 0.95:
                break

        # 验证分割点质量
        if max_similarity < 0.7:
            logger.warning(f"Part {i + 1} similarity too low ({max_similarity:.2f}): '{current_part}'")
            continue

        if best_split is not None:
            # 确保分割点不会产生空片段或单字片段
            part_length = best_split - start
            if language == 'zh' and part_length < 3:
                logger.warning(f"Split point creates too short part ({part_length} chars), skipping")
                continue
            split_positions.append(best_split)
            start = best_split
        else:
            logger.warning(f"Unable to find split point for part {i + 1}: '{current_part}'")

    return split_positions


async def split_sentence(sentence: str, num_parts: int, word_limit: int = 20, index: int = -1, retry_attempt: int = 0) -> str:
    """Split a long sentence using GPT and return the result as a string."""
    split_prompt = get_split_prompt(sentence, num_parts, word_limit)
    language = settings.whisper_language

    def valid_split(response_data):
        choice = response_data.get("choice", "1")
        if f'split{choice}' not in response_data:
            return {"status": "error", "message": "Missing required key: `split`"}

        split_result = response_data.get(f"split{choice}", "")
        if "[br]" not in split_result:
            return {"status": "error", "message": "Split failed, no [br] found"}

        # 验证分割后的每个部分长度
        parts = [p.strip() for p in split_result.split('[br]') if p.strip()]

        if language == 'zh':
            # 中文：每个部分至少 10 个字符
            min_length = 10
            unit = "字符"
        else:
            # 其他语言：每个部分至少 3 个词
            min_length = 3
            unit = "词"

        for i, part in enumerate(parts):
            part_length = len(part) if language == 'zh' else len(part.split())
            if part_length < min_length:
                return {"status": "error",
                        "message": f"Part {i + 1} too short ({part_length} {unit}, minimum {min_length}): '{part}'"}

        return {"status": "success", "message": "Split completed"}

    response_data = await ask_llm(split_prompt + " " * retry_attempt, resp_type='json', valid_def=valid_split,
                                  log_title='split_by_meaning')
    choice = response_data.get("choice", "1")
    best_split = response_data.get(f"split{choice}", "")
    split_points = find_split_positions(sentence, best_split)

    # 如果没有找到有效的分割点，返回原句子
    if not split_points:
        logger.warning(f"No valid split points found for sentence {index}, returning original")
        return sentence

    # split the sentence based on the split points
    parts = []
    start = 0
    for split_point in split_points:
        parts.append(sentence[start:split_point])
        start = split_point
    parts.append(sentence[start:])  # 添加最后一部分
    best_split = '\n'.join(parts)

    if index != -1:
        logger.info(f'Sentence {index} has been successfully split into {len(split_points) + 1} parts')

    return best_split


async def parallel_split_sentences(sentences: list, max_length: int, max_workers: int, nlp, retry_attempt: int = 0, use_jieba: bool = False) -> list:
    """Split sentences in parallel using a thread pool."""
    new_sentences = [None] * len(sentences)
    futures = []
    language = settings.whisper_language

    # 创建任务
    for index, sentence in enumerate(sentences):
        # 根据语言选择不同的计数方式
        if language == 'zh':
            # 中文：使用字符数
            sentence_length = len(sentence)
        else:
            # 其他语言：使用 token 数量
            tokens = tokenize_sentence(sentence, nlp, use_jieba=use_jieba)
            sentence_length = len(tokens)

        num_parts = math.ceil(sentence_length / max_length)
        if sentence_length > max_length:
            future = asyncio.create_task(split_sentence(sentence, num_parts, max_length, index=index,
                                                       retry_attempt=retry_attempt))
            futures.append((future, index, num_parts, sentence))
        else:
            new_sentences[index] = [sentence]

    # 等待所有任务完成
    for future, index, num_parts, sentence in futures:
        split_result = await future
        if split_result:
            split_lines = split_result.strip().split('\n')
            new_sentences[index] = [line.strip() for line in split_lines]
        else:
            new_sentences[index] = [sentence]

    return [sentence for sublist in new_sentences for sentence in sublist]


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

    # 读取输入句子
    with open(nlp_split_file, 'r', encoding='utf-8') as f:
        sentences = [line.strip() for line in f.readlines()]

    # 检测语言，中文使用 jieba 进行 tokenization
    language = source_language
    use_jieba = (language == 'zh' and JIEBA_AVAILABLE)

    if use_jieba:
        logger.info('Using jieba for Chinese tokenization in meaning split')
    else:
        nlp = await asyncio.to_thread(init_nlp)

    # process sentences multiple times to ensure all are split
    for retry_attempt in range(3):
        sentences = await parallel_split_sentences(
            sentences,
            max_length=getattr(settings, 'max_split_length', 42),
            max_workers=settings.max_workers,
            nlp=nlp if not use_jieba else None,
            retry_attempt=retry_attempt,
            use_jieba=use_jieba
        )

    # save results
    SPLIT_BY_MEANING.parent.mkdir(parents=True, exist_ok=True)
    with open(SPLIT_BY_MEANING, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sentences))

    logger.info(f"All sentences have been successfully split: {SPLIT_BY_MEANING}")
    return str(SPLIT_BY_MEANING)
