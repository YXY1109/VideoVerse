import os
import re
import string
from typing import List

import jieba
import pandas as pd
from loguru import logger

from core.utils.common import get_joiner

# 连接词
CHINESE_CONNECTORS = [
    '因为', '所以', '但是', '而且', '虽然', '如果', '即使', '尽管',
    '另外', '此外', '因此', '不过', '然而', '可是', '接着', '然后'
]

# 标点符号定义
CHINESE_PUNCTUATION = ['。', '！', '？', '，', '；', '：', '、', '…']
CHINESE_COMMA = '，'


def load_chinese_stopwords():
    """从配置文件加载中文停用词表"""
    try:
        stopwords_path = r"D:\PycharmProjects\VideoVerse\files\chinese_stopwords.txt"
        if os.path.exists(stopwords_path):
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                custom_stopwords = set(line.strip() for line in f if line.strip())
            return custom_stopwords
    except Exception:
        raise Exception("Failed to load Chinese stopwords")


def split_by_mark_jieba(df: pd.DataFrame, language: str):
    """
    按标点符号分割中文文本
    处理连字符连接（...、-）
    """
    joiner = get_joiner(language)
    logger.info(f"Using {language} language joiner: '{joiner}'")

    df.text = df.text.apply(lambda x: x.strip('"').strip(""))

    # 合并文本
    input_text = joiner.join(df.text.to_list())

    # 使用正则表达式按中文标点分割（。！？）
    sentence_pattern = f"[{''.join(re.escape(p) for p in CHINESE_PUNCTUATION[:3])}]"
    raw_sentences = re.split(sentence_pattern, input_text)

    # 处理连字符连接
    sentences_by_mark = []
    current_sentence = []

    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue

        # 检查是否需要合并（处理 ... 和 -）
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

    # 合并仅包含标点的行到上一行
    result = []
    for i, sentence in enumerate(sentences_by_mark):
        if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
            # 追加到上一句末尾
            result[-1] += sentence
        else:
            result.append(sentence)

    logger.info(f"Split {len(result)} sentences by punctuation marks (jieba)")
    return result


def split_by_comma_jieba(sentences):
    """
    按逗号分割中文句子
    检查左右是否构成完整句子（>=3 词）
    """
    all_split_sentences = []
    stopwords = load_chinese_stopwords()

    for sentence in sentences:
        # 按逗号分割
        parts = sentence.strip().split(CHINESE_COMMA)

        i = 0
        while i < len(parts):
            if i == len(parts) - 1:
                # 最后一个部分直接添加
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

            # 只有当左右都有足够词汇时才分割
            if len(left_words) >= 3 and len(right_words) >= 3:
                logger.debug(f"Split at comma: {current_part[-4:]}，| {next_part[:4]}")
                all_split_sentences.append(current_part)
            else:
                # 合并
                merged = current_part + CHINESE_COMMA + next_part
                parts[i + 1] = merged

            i += 1

    logger.info(f"Sentences split by commas (jieba)")
    return all_split_sentences


def analyze_chinese_connectors(words: List[str], connector_idx: int) -> bool:
    """
    分析连接词是否应该触发分割
    检查连接词前后的词数（>=5）
    """
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
    """
    按连接词分割中文句子（对应 Spacy 版本的 split_by_connectors）
    连接词：因为、所以、但是、而且等
    """
    words = list(jieba.cut(text))
    sentences = [text]

    # 迭代处理，避免同时多处分割
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


def split_long_sentence_jieba(text: str, max_tokens: int = 60) -> List[str]:
    """
    分割超长中文句子（对应 Spacy 版本的 split_long_sentence）
    使用贪心算法在合适位置分割（>60 token）
    """
    words = list(jieba.cut(text))
    n = len(words)

    if n <= max_tokens:
        return [text]

    # 贪心分割：在合适位置分割
    sentences = []
    current_start = 0
    min_sentence_length = 30

    while current_start < n:
        # 寻找最佳分割点
        best_end = min(current_start + max_tokens, n)

        # 尝试在标点符号处分割
        for i in range(min(current_start + min_sentence_length, n), best_end):
            if words[i] in CHINESE_PUNCTUATION:
                best_end = i + 1
                break

        sentences.append(''.join(words[current_start:best_end]).strip())
        current_start = best_end

    return sentences

def split_sentences_jieba_main(sentences):
    """
    按连接词分割中文句子主函数（对应 Spacy 版本的 split_sentences_main）
    """
    all_split_sentences = []
    for sentence in sentences:
        split_sentences = split_by_connectors_jieba(sentence.strip())
        all_split_sentences.extend(split_sentences)

    logger.info(f"Sentences split by connectors (jieba)")
    return all_split_sentences


def split_extremely_long_sentence_jieba(text: str, max_tokens: int = 60) -> List[str]:
    """
    分割极长中文句子（对应 Spacy 版本的 split_extremely_long_sentence）
    平均分割超过 60 token 的句子
    """
    words = list(jieba.cut(text))
    n = len(words)

    if n <= max_tokens:
        return [text]

    num_parts = (n + max_tokens - 1) // max_tokens
    part_length = n // num_parts

    sentences = []
    for i in range(num_parts):
        start = i * part_length
        end = start + part_length if i < num_parts - 1 else n
        sentences.append(''.join(words[start:end]))

    return sentences

def split_long_by_root_jieba_main(sentences):
    """
    分割超长中文句子主函数（对应 Spacy 版本的 split_long_by_root_main）
    """

    all_split_sentences = []
    for sentence in sentences:
        words = list(jieba.cut(sentence.strip()))

        if len(words) > 60:
            logger.debug(f"Splitting long sentences: {sentence[:30]}...")
            split_sentences = split_long_sentence_jieba(sentence.strip())

            # 如果还有超长句子，强制平均分割
            if any(len(list(jieba.cut(sent))) > 60 for sent in split_sentences):
                split_sentences = [
                    subsent
                    for sent in split_sentences
                    for subsent in split_extremely_long_sentence_jieba(sent)
                ]

            all_split_sentences.extend(split_sentences)
        else:
            all_split_sentences.append(sentence.strip())

    punctuation = string.punctuation + "'" + '"'
    filtered_sentences = []
    for i, sentence in enumerate(all_split_sentences):
        stripped_sentence = sentence.strip()
        if not stripped_sentence or all(char in punctuation for char in stripped_sentence):
            logger.warning(f"Empty or punctuation-only line detected at index {i}")
            if filtered_sentences:
                filtered_sentences[-1] += sentence
            continue
        filtered_sentences.append(sentence)

    logger.info(f"Long sentences split by root (jieba)")
    return filtered_sentences


if __name__ == '__main__':
    df = pd.read_excel(str(r"D:\PycharmProjects\VideoVerse\files\demo\cleaned_chunks.xlsx"))
    result1 = split_by_mark_jieba(df, 'zh')
    print(f"result1:{result1}")
    result2 = split_by_comma_jieba(result1)
    print(f"result2:{result2}")
    result3 = split_sentences_jieba_main(result2)
    print(f"result3:{result3}")
    result4 = split_long_by_root_jieba_main(result3)
    print(f"result4:{result4}")
