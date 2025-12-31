"""
步骤 04: AI 语义分割

使用 LLM 对长句进行语义分割
"""
import asyncio
import math
import warnings
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

# 抑制 jieba 导入时的 pkg_resources 弃用警告
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

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
    """找到分割位置"""
    split_positions = []
    parts = modified.split('[br]')
    start = 0
    language = settings.whisper_language
    joiner = get_joiner(language)

    for i in range(len(parts) - 1):
        max_similarity = 0
        best_split = None

        for j in range(start, len(original)):
            original_left = original[start:j]
            modified_left = joiner.join(parts[i].split())

            left_similarity = SequenceMatcher(None, original_left, modified_left).ratio()

            if left_similarity > max_similarity:
                max_similarity = left_similarity
                best_split = j

        if max_similarity < 0.9:
            logger.warning(f"Warning: low similarity found at the best split point: {max_similarity}")
        if best_split is not None:
            split_positions.append(best_split)
            start = best_split
        else:
            logger.warning(f"Warning: Unable to find a suitable split point for the {i + 1}th part.")

    return split_positions


async def split_sentence(sentence: str, num_parts: int, word_limit: int = 20, index: int = -1, retry_attempt: int = 0) -> str:
    """Split a long sentence using GPT and return the result as a string."""
    split_prompt = get_split_prompt(sentence, num_parts, word_limit)

    def valid_split(response_data):
        choice = response_data.get("choice", "1")
        if f'split{choice}' not in response_data:
            return {"status": "error", "message": "Missing required key: `split`"}
        if "[br]" not in response_data[f"split{choice}"]:
            return {"status": "error", "message": "Split failed, no [br] found"}
        return {"status": "success", "message": "Split completed"}

    response_data = await ask_llm(split_prompt + " " * retry_attempt, resp_type='json', valid_def=valid_split,
                                  log_title='split_by_meaning')
    choice = response_data.get("choice", "1")
    best_split = response_data.get(f"split{choice}", "")
    split_points = find_split_positions(sentence, best_split)

    # split the sentence based on the split points
    for i, split_point in enumerate(split_points):
        if i == 0:
            best_split = sentence[:split_point] + '\n' + sentence[split_point:]
        else:
            parts = best_split.split('\n')
            last_part = parts[-1]
            parts[-1] = last_part[:split_point - split_points[i - 1]] + '\n' + last_part[
                split_point - split_points[i - 1]:]
            best_split = '\n'.join(parts)

    if index != -1:
        logger.info(f'Sentence {index} has been successfully split')

    return best_split


async def parallel_split_sentences(sentences: list, max_length: int, max_workers: int, nlp, retry_attempt: int = 0, use_jieba: bool = False) -> list:
    """Split sentences in parallel using a thread pool."""
    new_sentences = [None] * len(sentences)
    futures = []

    # 创建任务
    for index, sentence in enumerate(sentences):
        # Use tokenizer to split the sentence (jieba for Chinese, Spacy for others)
        tokens = tokenize_sentence(sentence, nlp, use_jieba=use_jieba)
        num_parts = math.ceil(len(tokens) / max_length)
        if len(tokens) > max_length:
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
