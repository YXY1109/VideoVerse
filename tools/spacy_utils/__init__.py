"""Spacy NLP 工具模块。

提供基于 Spacy 的文本分割功能，支持多种语言。

注意：此模块需要 spacy 依赖。如果未安装 spacy，某些功能将不可用。
"""

from loguru import logger

# 尝试导入核心函数
try:
    from tools.spacy_utils.load_nlp_model import (
        SPLIT_BY_COMMA_FILE,
        SPLIT_BY_CONNECTOR_FILE,
        SPLIT_BY_MARK_FILE,
        get_spacy_model,
        init_nlp,
    )
    from tools.spacy_utils.split_by_comma import split_by_comma, split_by_comma_main
    from tools.spacy_utils.split_by_connector import split_connectors, split_sentences_main
    from tools.spacy_utils.split_by_mark import split_by_mark
    from tools.spacy_utils.split_long_by_root import (
        split_extremely_long_sentence,
        split_long_sentence,
        split_long_by_root_main,
    )
    SPACY_AVAILABLE = True
except ImportError as e:
    SPACY_AVAILABLE = False
    logger.warning(f"Spacy not available: {e}")
    # 创建占位函数
    SPLIT_BY_COMMA_FILE = None
    SPLIT_BY_CONNECTOR_FILE = None
    SPLIT_BY_MARK_FILE = None
    get_spacy_model = None
    init_nlp = None
    split_by_comma = None
    split_by_comma_main = None
    split_by_connectors = None
    split_sentences_main = None
    split_by_mark = None
    split_extremely_long_sentence = None
    split_long_sentence = None
    split_long_by_root_main = None

# 尝试导入 jieba 中文分割函数
try:
    from tools.spacy_utils.jieba_split import (
        split_by_mark_jieba,
        split_by_comma_jieba_main,
        split_sentences_jieba_main,
        split_long_by_root_jieba_main,
    )
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

__all__ = [
    # 基础函数
    "get_spacy_model",
    "init_nlp",
    # 分割函数
    "split_by_mark",
    "split_by_comma",
    "split_by_comma_main",
    "split_sentences_main",
    "split_long_sentence",
    "split_long_by_root_main",
    # 文件路径
    "SPLIT_BY_MARK_FILE",
    "SPLIT_BY_COMMA_FILE",
    "SPLIT_BY_CONNECTOR_FILE",
    # jieba 函数（如果可用）
    "split_by_mark_jieba",
    "split_by_comma_jieba_main",
    "split_sentences_jieba_main",
    "split_long_by_root_jieba_main",
    # 可用性标志
    "SPACY_AVAILABLE",
    "JIEBA_AVAILABLE",
]
