"""分割超长文本模块。

从 temp/tools/spacy_utils/split_long_by_root.py 迁移。
使用动态规划分割超过 60 token 的句子。
"""

import os
import string

from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.utils.common import get_joiner
from tools.spacy_utils.load_nlp_model import SPLIT_BY_CONNECTOR_FILE

settings = get_settings()


def split_long_sentence(doc: object) -> list[str]:
    """使用动态规划分割长句。

    Args:
        doc: Spacy 文档对象

    Returns:
        分割后的句子列表
    """
    tokens = [token.text for token in doc]
    n = len(tokens)

    # 动态规划数组，dp[i] 表示从开始到第 i 个 token 的最优分割方案
    dp = [float('inf')] * (n + 1)
    dp[0] = 0

    # 记录最优分割点
    prev = [0] * (n + 1)

    for i in range(1, n + 1):
        for j in range(max(0, i - 100), i):  # 限制搜索范围避免过长句子
            if i - j >= 30:  # 确保句子长度至少 30
                token = doc[i - 1]
                if j == 0 or (token.is_sent_end or token.pos_ in ['VERB', 'AUX'] or token.dep_ == 'ROOT'):
                    if dp[j] + 1 < dp[i]:
                        dp[i] = dp[j] + 1
                        prev[i] = j

    # 根据最优分割点重建句子
    sentences = []
    i = n
    language = settings.whisper_language
    joiner = get_joiner(language)

    while i > 0:
        j = prev[i]
        sentences.append(joiner.join(tokens[j:i]).strip())
        i = j

    return sentences[::-1]  # 反转列表保持原始顺序


def split_extremely_long_sentence(doc: object) -> list[str]:
    """平均分割极长句子。

    Args:
        doc: Spacy 文档对象

    Returns:
        分割后的句子列表
    """
    tokens = [token.text for token in doc]
    n = len(tokens)

    num_parts = (n + 59) // 60  # 向上取整
    part_length = n // num_parts

    sentences = []
    language = settings.whisper_language
    joiner = get_joiner(language)

    for i in range(num_parts):
        start = i * part_length
        end = start + part_length if i < num_parts - 1 else n
        sentence = joiner.join(tokens[start:end])
        sentences.append(sentence)

    return sentences


def split_long_by_root_main(nlp: object) -> None:
    """分割超长文本的主函数。

    Args:
        nlp: Spacy NLP 模型对象
    """
    with open(SPLIT_BY_CONNECTOR_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        doc = nlp(sentence.strip())
        if len(doc) > 60:
            split_sentences = split_long_sentence(doc)
            if any(len(nlp(sent)) > 60 for sent in split_sentences):
                split_sentences = [
                    subsent
                    for sent in split_sentences
                    for subsent in split_extremely_long_sentence(nlp(sent))
                ]
            all_split_sentences.extend(split_sentences)
            logger.debug(f"Splitting long sentences by root: {sentence[:30]}...")
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

    # 删除原文件
    os.remove(SPLIT_BY_CONNECTOR_FILE)

    logger.info(f"Long sentences split by root saved to {paths.split_by_nlp}")


if __name__ == "__main__":
    from tools.spacy_utils.load_nlp_model import init_nlp

    nlp = init_nlp()
    split_long_by_root_main(nlp)


__all__ = ["split_long_sentence", "split_extremely_long_sentence", "split_long_by_root_main"]
