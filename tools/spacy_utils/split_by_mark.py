"""按标点符号分割文本模块。

从 temp/tools/spacy_utils/split_by_mark.py 迁移。
处理连字符连接（...、-）的情况。
"""

import os

import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.utils.common import get_joiner
from tools.spacy_utils.load_nlp_model import SPLIT_BY_MARK_FILE

settings = get_settings()


def split_by_mark(nlp: object) -> None:
    """按标点符号分割文本。

    Args:
        nlp: Spacy NLP 模型对象

    功能：
        - 读取转录结果
        - 按标点符号分割句子
        - 处理连字符连接的情况（...、-）
        - 保存分割结果
    """
    language = settings.whisper_language
    joiner = get_joiner(language)
    logger.info(f"Using {language} language joiner: '{joiner}'")

    # 读取转录结果
    chunks = pd.read_excel(str(paths.cleaned_chunks))
    chunks.text = chunks.text.apply(lambda x: x.strip('"').strip(""))

    # 合并文本
    input_text = joiner.join(chunks.text.to_list())

    # 使用 Spacy 进行句子分割
    doc = nlp(input_text)
    assert doc.has_annotation("SENT_START"), "NLP model does not support sentence detection"

    # 处理连字符连接
    sentences_by_mark = []
    current_sentence = []

    # 遍历所有句子
    for sent in doc.sents:
        text = sent.text.strip()

        # 检查当前句子是否与前一句通过连字符连接
        if current_sentence and (
                text.startswith('-') or
                text.startswith('...') or
                current_sentence[-1].endswith('-') or
                current_sentence[-1].endswith('...')
        ):
            current_sentence.append(text)
        else:
            if current_sentence:
                sentences_by_mark.append(' '.join(current_sentence))
                current_sentence = []
            current_sentence.append(text)

    # 添加最后一句
    if current_sentence:
        sentences_by_mark.append(' '.join(current_sentence))

    # 写入文件
    with open(SPLIT_BY_MARK_FILE, "w", encoding="utf-8") as output_file:
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.', '，', '。', '？', '！']:
                # 如果当前行只包含标点符号，将其合并到前一行
                output_file.seek(output_file.tell() - 1, os.SEEK_SET)
                output_file.write(sentence)
            else:
                output_file.write(sentence + "\n")

    logger.info(f"Sentences split by punctuation marks saved to `{SPLIT_BY_MARK_FILE}`")


if __name__ == "__main__":
    from tools.spacy_utils.load_nlp_model import init_nlp

    nlp = init_nlp()
    split_by_mark(nlp)


__all__ = ["split_by_mark"]
