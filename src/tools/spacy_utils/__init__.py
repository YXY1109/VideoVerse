from .load_nlp_model import init_nlp
from .split_by_comma import split_by_comma_main
from .split_by_connector import split_sentences_main
from .split_by_mark import split_by_mark
from .split_long_by_root import split_long_by_root_main

# 导入 jieba 中文分割函数，如果 jieba 不可用则标记为不可用
try:
    from .jieba_split import (
        split_by_mark_jieba,
        split_by_comma_jieba_main,
        split_sentences_jieba_main,
        split_long_by_root_jieba_main
    )

    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

__all__ = [
    "split_by_comma_main",
    "split_sentences_main",
    "split_by_mark",
    "split_long_by_root_main",
    "init_nlp",
    # jieba 函数
    "split_by_mark_jieba",
    "split_by_comma_jieba_main",
    "split_sentences_jieba_main",
    "split_long_by_root_jieba_main",
    "JIEBA_AVAILABLE"
]
