"""按连接词分割文本模块。

从 temp/tools/spacy_utils/split_by_connector.py 迁移。
处理各种语言的连接词（that、because、但是、因为等）。
"""

import os

from loguru import logger

from tools.spacy_utils.load_nlp_model import SPLIT_BY_COMMA_FILE, SPLIT_BY_CONNECTOR_FILE


def analyze_connectors(doc: object, token: object) -> tuple[bool, bool]:
    """分析 token 是否为连接词。

    Args:
        doc: Spacy 文档对象
        token: 当前 token

    Returns:
        (是否在连接词前分割, 是否保留连接词)
    """
    lang = doc.lang_

    # 定义各语言的连接词和语法特征
    if lang == "en":
        connectors = ["that", "which", "where", "when", "because", "but", "and", "or"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "zh":
        connectors = ["因为", "所以", "但是", "而且", "虽然", "如果", "即使", "尽管"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "ja":
        connectors = ["けれども", "しかし", "だから", "それで", "ので", "のに", "ため"]
        mark_dep = "mark"
        det_pron_deps = ["case"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "fr":
        connectors = ["que", "qui", "où", "quand", "parce que", "mais", "et", "ou"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "ru":
        connectors = ["что", "который", "где", "когда", "потому что", "но", "и", "или"]
        mark_dep = "mark"
        det_pron_deps = ["det"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "es":
        connectors = ["que", "cual", "donde", "cuando", "porque", "pero", "y", "o"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "de":
        connectors = ["dass", "welche", "wo", "wann", "weil", "aber", "und", "oder"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    elif lang == "it":
        connectors = ["che", "quale", "dove", "quando", "perché", "ma", "e", "o"]
        mark_dep = "mark"
        det_pron_deps = ["det", "pron"]
        verb_pos = "VERB"
        noun_pos = ["NOUN", "PROPN"]
    else:
        return False, False

    if token.text.lower() not in connectors:
        return False, False

    # 特殊处理英语 "that"
    if lang == "en" and token.text.lower() == "that":
        if token.dep_ == mark_dep and token.head.pos_ == verb_pos:
            return True, False
        else:
            return False, False
    elif token.dep_ in det_pron_deps and token.head.pos_ in noun_pos:
        return False, False
    else:
        return True, False


def split_by_connectors(text: str, context_words: int = 5, nlp: object = None) -> list[str]:
    """按连接词分割文本。

    Args:
        text: 输入文本
        context_words: 上下文词数
        nlp: Spacy NLP 模型对象

    Returns:
        分割后的句子列表
    """
    doc = nlp(text)
    sentences = [doc.text]

    while True:
        split_occurred = False
        new_sentences = []

        for sent in sentences:
            doc = nlp(sent)
            start = 0

            for i, token in enumerate(doc):
                split_before, _ = analyze_connectors(doc, token)

                # 跳过缩写
                if i + 1 < len(doc) and doc[i + 1].text in ["'s", "'re", "'ve", "'ll", "'d"]:
                    continue

                left_words = doc[max(0, token.i - context_words):token.i]
                right_words = doc[token.i + 1:min(len(doc), token.i + context_words + 1)]

                left_words = [word.text for word in left_words if not word.is_punct]
                right_words = [word.text for word in right_words if not word.is_punct]

                if len(left_words) >= context_words and len(right_words) >= context_words and split_before:
                    logger.debug(f"Split before '{token.text}': {' '.join(left_words)}| {token.text} {' '.join(right_words)}")
                    new_sentences.append(doc[start:token.i].text.strip())
                    start = token.i
                    split_occurred = True
                    break

            if start < len(doc):
                new_sentences.append(doc[start:].text.strip())

        if not split_occurred:
            break

        sentences = new_sentences

    return sentences


def split_sentences_main(nlp: object) -> None:
    """按连接词分割文本的主函数。

    Args:
        nlp: Spacy NLP 模型对象
    """
    with open(SPLIT_BY_COMMA_FILE, "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        split_sentences = split_by_connectors(sentence.strip(), nlp=nlp)
        all_split_sentences.extend(split_sentences)

    with open(SPLIT_BY_CONNECTOR_FILE, "w+", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")
        output_file.seek(output_file.tell() - 1, os.SEEK_SET)
        output_file.truncate()

    # 删除原文件
    os.remove(SPLIT_BY_COMMA_FILE)

    logger.info(f"Sentences split by connectors saved to `{SPLIT_BY_CONNECTOR_FILE}`")


if __name__ == "__main__":
    from tools.spacy_utils.load_nlp_model import init_nlp

    nlp = init_nlp()
    split_sentences_main(nlp)


__all__ = ["split_by_connectors", "split_sentences_main"]
