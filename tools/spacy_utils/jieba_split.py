"""Jieba 中文分割模块。

从 temp/tools/spacy_utils/jieba_split.py 迁移。
使用 jieba 替代 Spacy 进行中文文本分割。
"""

import os
import re
import string
from typing import List

import jieba
import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.utils.common import get_joiner
from tools.spacy_utils.load_nlp_model import SPLIT_BY_CONNECTOR_FILE

settings = get_settings()

# 中文停用词和连接词
CHINESE_STOPWORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
    '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
    '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '与',
    '或', '及', '而', '等', '却', '又', '么', '之'
])

CHINESE_CONNECTORS = [
    '因为', '所以', '但是', '而且', '虽然', '如果', '即使', '尽管',
    '另外', '此外', '因此', '不过', '然而', '可是', '接着', '然后'
]

# 标点符号定义
CHINESE_PUNCTUATION = ['。', '！', '？', '，', '；', '：', '、', '…']
CHINESE_COMMA = '，'

# 文件路径
SPLIT_BY_MARK_FILE = paths.log_dir / "split_by_mark.txt"
SPLIT_BY_COMMA_FILE = paths.log_dir / "split_by_comma.txt"


def load_chinese_stopwords() -> set:
    """从配置文件加载中文停用词表。

    Returns:
        停用词集合
    """
    try:
        stopwords_path = settings.chinese_stopwords_file
        if os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                custom_stopwords = set(line.strip() for line in f if line.strip())
            return CHINESE_STOPWORDS | custom_stopwords
    except Exception:
        pass
    return CHINESE_STOPWORDS


def split_by_mark_jieba() -> None:
    """按标点符号分割中文文本。"""
    language = settings.whisper_language
    joiner = get_joiner(language)
    logger.info(f"Using {language} language joiner: '{joiner}'")

    chunks = pd.read_excel(str(paths.cleaned_chunks))
    chunks.text = chunks.text.apply(lambda x: x.strip('"').strip(""))

    # 合并文本
    input_text = joiner.join(chunks.text.to_list())

    # 使用正则表达式按中文标点分割
    sentence_pattern = f"[{''.join(re.escape(p) for p in CHINESE_PUNCTUATION[:3])}]"
    raw_sentences = re.split(sentence_pattern, input_text)

    # 处理连字符连接
    sentences_by_mark = []
    current_sentence = []

    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue

        # 检查是否需要合并
        if current_sentence and (
                sent.startswith('-') or
                sent.startswith('...') or
                sent.startswith('…') or
                current_sentence[-1].endswith('-') or
                current_sentence[-1].endswith('...') or
                current_sentence[-1].endswith('…')
        ):
            current_sentence.append(sent)
        else:
            if current_sentence:
                sentences_by_mark.append(''.join(current_sentence))
                current_sentence = []
            current_sentence.append(sent)

    if current_sentence:
        sentences_by_mark.append(''.join(current_sentence))

    # 写入文件
    with open(SPLIT_BY_MARK_FILE, "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
                output_file.seek(output_file.tell() - 1, os.SEEK_SET)
                output_file.write(sentence)
            else:
                output_file.write(sentence + "\n")

    logger.info(f"Sentences split by punctuation marks (jieba) saved to `{SPLIT_BY_MARK_FILE}`")


def split_by_comma_jieba_main() -> None:
    """按逗号分割中文句子。"""
    with open(SPLIT_BY_MARK_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    stopwords = load_chinese_stopwords()

    for sentence in sentences:
        parts = sentence.strip().split(CHINESE_COMMA)

        i = 0
        while i < len(parts):
            if i == len(parts) - 1:
                if parts[i].strip():
                    all_split_sentences.append(parts[i].strip())
                break

            current_part = parts[i].strip()
            next_part = parts[i + 1].strip()

            # 计算左右的有效词数
            left_words = [w for w in jieba.cut(current_part) if
                          w.strip() and w not in string.punctuation and w not in stopwords]
            right_words = [w for w in jieba.cut(next_part) if
                           w.strip() and w not in string.punctuation and w not in stopwords]

            if len(left_words) >= 3 and len(right_words) >= 3:
                logger.debug(f"Split at comma: {current_part[-4:]}，| {next_part[:4]}")
                all_split_sentences.append(current_part)
            else:
                merged = current_part + CHINESE_COMMA + next_part
                parts[i + 1] = merged

            i += 1

    with open(SPLIT_BY_COMMA_FILE, "w", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")

    os.remove(SPLIT_BY_MARK_FILE)
    logger.info(f"Sentences split by commas (jieba) saved to `{SPLIT_BY_COMMA_FILE}`")


def analyze_chinese_connectors(words: List[str], connector_idx: int) -> bool:
    """分析连接词是否应该触发分割。"""
    if connector_idx < 1 or connector_idx >= len(words) - 1:
        return False

    connector = words[connector_idx]
    if connector not in CHINESE_CONNECTORS:
        return False

    # 检查前后词数
    left_words = words[max(0, connector_idx - 5):connector_idx]
    right_words = words[connector_idx + 1:min(len(words), connector_idx + 6)]

    left_words = [w for w in left_words if w.strip() and w not in string.punctuation]
    right_words = [w for w in right_words if w.strip() and w not in string.punctuation]

    return len(left_words) >= 5 and len(right_words) >= 5


def split_by_connectors_jieba(text: str, context_words: int = 5) -> List[str]:
    """按连接词分割中文句子。"""
    words = list(jieba.cut(text))
    sentences = [text]

    while True:
        split_occurred = False
        new_sentences = []

        for sent in sentences:
            words = list(jieba.cut(sent))

            for i, word in enumerate(words):
                if analyze_chinese_connectors(words, i):
                    left_text = ''.join(words[:i]).strip()
                    right_text = ''.join(words[i:]).strip()

                    left_show = left_text[-context_words:] if len(left_text) > context_words else left_text
                    right_show = right_text[:context_words] if len(right_text) > context_words else right_text
                    logger.debug(f"Split before '{word}': {left_show}| {word}{right_show}")
                    new_sentences.append(left_text)
                    new_sentences.append(right_text)
                    split_occurred = True
                    break

            if not split_occurred:
                new_sentences.append(sent)

        if not split_occurred:
            break

        sentences = new_sentences

    return sentences


def split_sentences_jieba_main() -> None:
    """按连接词分割中文句子主函数。"""
    with open(SPLIT_BY_COMMA_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        split_sentences = split_by_connectors_jieba(sentence.strip())
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_CONNECTOR_FILE, "w+", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")
        output_file.seek(output_file.tell() - 1, os.SEEK_SET)
        output_file.truncate()

    os.remove(SPLIT_BY_COMMA_FILE)
    logger.info(f"Sentences split by connectors (jieba) saved to `{SPLIT_BY_CONNECTOR_FILE}`")


def split_long_sentence_jieba(text: str, max_tokens: int = 60) -> List[str]:
    """分割超长中文句子。"""
    words = list(jieba.cut(text))
    n = len(words)

    if n <= max_tokens:
        return [text]

    sentences = []
    current_start = 0
    min_sentence_length = 30

    while current_start < n:
        best_end = min(current_start + max_tokens, n)

        # 尝试在标点符号处分割
        for i in range(min(current_start + min_sentence_length, n), best_end):
            if words[i] in CHINESE_PUNCTUATION:
                best_end = i + 1
                break

        sentences.append(''.join(words[current_start:best_end]).strip())
        current_start = best_end

    return sentences


def split_long_by_root_jieba_main() -> None:
    """分割超长中文句子主函数。"""
    with open(SPLIT_BY_CONNECTOR_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        words = list(jieba.cut(sentence.strip()))

        if len(words) > 60:
            logger.debug(f"Splitting long sentences: {sentence[:30]}...")
            split_sentences = split_long_sentence_jieba(sentence.strip())

            if any(len(list(jieba.cut(sent))) > 60 for sent in split_sentences):
                split_sentences = [
                    subsent
                    for sent in split_sentences
                    for subsent in split_long_sentence_jieba(sent)
                ]

            all_split_sentences.extend(split_sentences)
        else:
            all_split_sentences.append(sentence.strip())

    punctuation = string.punctuation + "'" + '"'
    with open(str(paths.split_by_nlp), "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(all_split_sentences):
            stripped_sentence = sentence.strip()
            if not stripped_sentence or all(char in punctuation for char in stripped_sentence):
                logger.warning(f"Empty or punctuation-only line detected at index {i}")
                if i > 0:
                    all_split_sentences[i - 1] += sentence
                continue
            output_file.write(sentence + "\n")

    os.remove(SPLIT_BY_CONNECTOR_FILE)
    logger.info(f"Long sentences split by root (jieba) saved to `{paths.split_by_nlp}`")


__all__ = [
    "split_by_mark_jieba",
    "split_by_comma_jieba_main",
    "split_sentences_jieba_main",
    "split_long_by_root_jieba_main"
]
