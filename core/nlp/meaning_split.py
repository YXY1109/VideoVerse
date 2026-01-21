import concurrent.futures
import math
from difflib import SequenceMatcher

import jieba
from loguru import logger
from rich.table import Table

from core.nlp.nlp_split import load_spacy_model
from core.utils.common import get_joiner
from core.utils.llm import ask_llm
from core.utils.prompts import get_split_prompt


def process_meaning_split(sentences: list, source_language: str = "en") -> list:
    """
    流水线第四步：AI 语义分割

    Args:
        sentences: NLP 分割结果文件路径
        source_language: 源语言代码

    Returns:
        分割结果文件路径
    """
    logger.info("Starting meaning split with AI")
    # 检测语言，中文使用 jieba 进行 tokenization
    use_jieba = source_language == "zh"

    if use_jieba:
        logger.warning("Using jieba for Chinese tokenization in meaning split")
        nlp = None
    else:
        nlp = load_spacy_model(source_language)

    # process sentences multiple times to ensure all are split
    sentences = parallel_split_sentences(
        sentences, language=source_language, nlp=nlp, use_jieba=use_jieba, max_length=10
    )

    return sentences


def parallel_split_sentences(
    sentences: list, language: str, nlp=None, max_length: int = 42, use_jieba: bool = False
) -> list:
    """Split sentences in parallel using a thread pool."""
    new_sentences = [None] * len(sentences)
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for index, sentence in enumerate(sentences):
            # Use tokenizer to split the sentence (jieba for Chinese, Spacy for others)
            tokens = tokenize_sentence(sentence, nlp, use_jieba=use_jieba)
            # print("Tokenization result:", tokens)
            num_parts = math.ceil(len(tokens) / max_length)
            if len(tokens) > max_length:
                future = executor.submit(split_sentence, sentence, num_parts, max_length, index=index, retry_attempt=3)
                futures.append((future, index, num_parts, sentence))
            else:
                new_sentences[index] = [sentence]

        for future, index, _num_parts, sentence in futures:
            split_result = future.result()
            if split_result:
                split_lines = split_result.strip().split("\n")
                new_sentences[index] = [line.strip() for line in split_lines]
            else:
                new_sentences[index] = [sentence]

    return [sentence for sublist in new_sentences for sentence in sublist]


def tokenize_sentence(sentence: str, nlp, use_jieba: bool = False):
    """Tokenize a sentence using Spacy or jieba (for Chinese)"""
    if use_jieba:
        return list(jieba.cut(sentence))
    else:
        doc = nlp(sentence)
        return [token.text for token in doc]


def split_sentence(sentence, num_parts, word_limit=20, index=-1, retry_attempt=0):
    """Split a long sentence using GPT and return the result as a string."""
    split_prompt = get_split_prompt(sentence, num_parts, word_limit)

    def valid_split(response_data):
        choice = response_data["choice"]
        if f"split{choice}" not in response_data:
            return {"status": "error", "message": "Missing required key: `split`"}
        if "[br]" not in response_data[f"split{choice}"]:
            return {"status": "error", "message": "Split failed, no [br] found"}
        return {"status": "success", "message": "Split completed"}

    response_dict = ask_llm(split_prompt + " " * retry_attempt, log_title="split_by_meaning")
    choice = response_dict["choice"]
    best_split = response_dict[f"split{choice}"]
    split_points = find_split_positions(sentence, best_split)
    # split the sentence based on the split points
    for i, split_point in enumerate(split_points):
        if i == 0:
            best_split = sentence[:split_point] + "\n" + sentence[split_point:]
        else:
            parts = best_split.split("\n")
            last_part = parts[-1]
            parts[-1] = (
                last_part[: split_point - split_points[i - 1]] + "\n" + last_part[split_point - split_points[i - 1] :]
            )
            best_split = "\n".join(parts)
    if index != -1:
        print(f"[green]✅ Sentence {index} has been successfully split[/green]")
    table = Table(title="")
    table.add_column("Type", style="cyan")
    table.add_column("Sentence")
    table.add_row("Original", sentence, style="yellow")
    table.add_row("Split", best_split.replace("\n", " ||"), style="yellow")
    print(table)

    return best_split


def find_split_positions(original: str, modified: str) -> list:
    """找到分割位置

    将 LLM 返回的带 [br] 标记的分割结果映射回原始句子的字符位置
    """
    split_positions = []
    parts = modified.split("[br]")
    start = 0
    language = "zh"
    joiner = get_joiner(language)

    # 清理 parts：去除空白和无效部分
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        logger.warning("No valid [br] split markers found in LLM response")
        return []

    for i in range(len(parts) - 1):
        current_part = parts[i]

        # 对于中文，确保当前部分至少包含 3 个字符
        if language == "zh" and len(current_part) < 3:
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
            if language == "zh":
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
            if language == "zh" and part_length < 3:
                logger.warning(f"Split point creates too short part ({part_length} chars), skipping")
                continue
            split_positions.append(best_split)
            start = best_split
        else:
            logger.warning(f"Unable to find split point for part {i + 1}: '{current_part}'")

    return split_positions
