"""按逗号分割文本模块。

从 temp/tools/spacy_utils/split_by_comma.py 迁移。
检查左右是否构成完整句子（>=3 词）。
"""

import itertools
import os

from loguru import logger

from tools.spacy_utils.load_nlp_model import SPLIT_BY_COMMA_FILE, SPLIT_BY_MARK_FILE


def is_valid_phrase(phrase: list) -> bool:
    """检查短语是否有效（有主语和动词）。

    Args:
        phrase: Spacy token 列表

    Returns:
        是否为有效短语
    """
    has_subject = any(
        token.dep_ in ["nsubj", "nsubjpass"] or token.pos_ == "PRON"
        for token in phrase
    )
    has_verb = any(
        token.pos_ == "VERB" or token.pos_ == 'AUX'
        for token in phrase
    )
    return has_subject and has_verb


def analyze_comma(start: int, doc: object, token: object) -> bool:
    """分析逗号是否适合分割。

    Args:
        start: 开始位置
        doc: Spacy 文档对象
        token: 当前 token

    Returns:
        是否适合在逗号处分割
    """
    left_phrase = doc[max(start, token.i - 9):token.i]
    right_phrase = doc[token.i + 1:min(len(doc), token.i + 10)]

    suitable_for_splitting = is_valid_phrase(right_phrase)

    # 移除标点符号并检查词数
    left_words = [t for t in left_phrase if not t.is_punct]
    right_words = list(
        itertools.takewhile(lambda t: not t.is_punct, right_phrase)
    )

    if len(left_words) <= 3 or len(right_words) <= 3:
        suitable_for_splitting = False

    return suitable_for_splitting


def split_by_comma(text: str, nlp: object) -> list[str]:
    """按逗号分割文本。

    Args:
        text: 输入文本
        nlp: Spacy NLP 模型对象

    Returns:
        分割后的句子列表
    """
    doc = nlp(text)
    sentences = []
    start = 0

    for i, token in enumerate(doc):
        if token.text == "," or token.text == "，":
            suitable_for_splitting = analyze_comma(start, doc, token)

            if suitable_for_splitting:
                sentences.append(doc[start:token.i].text.strip())
                logger.debug(f"Split at comma: {doc[start:token.i][-4:]}| {doc[token.i + 1:][:4]}")
                start = token.i + 1

    sentences.append(doc[start:].text.strip())
    return sentences


def split_by_comma_main(nlp: object) -> None:
    """按逗号分割文本的主函数。

    Args:
        nlp: Spacy NLP 模型对象
    """
    with open(SPLIT_BY_MARK_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        split_sentences = split_by_comma(sentence.strip(), nlp)
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_COMMA_FILE, "w", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")

    # 删除原文件
    os.remove(SPLIT_BY_MARK_FILE)

    logger.info(f"Sentences split by commas saved to `{SPLIT_BY_COMMA_FILE}`")


if __name__ == "__main__":
    from tools.spacy_utils.load_nlp_model import init_nlp

    nlp = init_nlp()
    split_by_comma_main(nlp)


__all__ = ["split_by_comma", "split_by_comma_main"]
