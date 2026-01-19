"""
NLP 工具函数模块

提供 Spacy 模型加载、语言检测、分词等通用功能。
遵循 Python 最佳实践：类型提示、文档字符串、缓存。
"""

from functools import lru_cache
from pathlib import Path

import jieba
import pandas as pd
import spacy
from loguru import logger
from spacy.cli import download

from core.nlp.nlp_constants import (
    CHINESE_CONNECTORS,
    SPACY_MODEL_MAP,
    get_spacy_model,
)
from core.utils.common import get_joiner


@lru_cache(maxsize=10)
def load_spacy_model(language: str) -> spacy.Language:
    """
    加载 Spacy NLP 模型（带缓存）

    Args:
        language: 语言代码 (如 'en', 'zh', 'ja')

    Returns:
        spacy.Language: Spacy NLP 模型对象

    Examples:
        >>> nlp = load_spacy_model('en')
        >>> doc = nlp("This is a test.")
    """
    model_name = get_spacy_model(language)
    if language not in SPACY_MODEL_MAP:
        logger.warning(f"Spacy model does not support '{language}', using {model_name} as fallback")

    try:
        nlp = spacy.load(model_name)
        logger.success(f"NLP Spacy model loaded: {model_name}")
    except OSError:
        logger.warning(f"Downloading {model_name} model...")
        download(model_name)
        nlp = spacy.load(model_name)
        logger.success(f"NLP Spacy model downloaded and loaded: {model_name}")

    return nlp


def load_chinese_stopwords(stopwords_path: str | Path | None = None) -> set[str]:
    """
    加载中文停用词表

    Args:
        stopwords_path: 停用词文件路径，默认为 files/chinese_stopwords.txt

    Returns:
        set[str]: 停用词集合

    Raises:
        FileNotFoundError: 停用词文件不存在时
        IOError: 读取文件失败时
    """
    if stopwords_path is None:
        # 默认路径
        project_root = Path(__file__).parent.parent.parent
        stopwords_path = project_root / "files" / "chinese_stopwords.txt"

    stopwords_path = Path(stopwords_path)

    if not stopwords_path.exists():
        raise FileNotFoundError(f"Chinese stopwords file not found: {stopwords_path}")

    try:
        with open(stopwords_path, encoding="utf-8") as f:
            stopwords = {line.strip() for line in f if line.strip()}
        logger.info(f"Loaded {len(stopwords)} Chinese stopwords from {stopwords_path}")
        return stopwords
    except Exception as e:
        raise OSError(f"Failed to load Chinese stopwords from {stopwords_path}: {e}") from e


def get_effective_words_jieba(text: str, stopwords: set[str] | None = None, remove_punct: bool = True) -> list[str]:
    """
    使用 jieba 分词并获取有效词（去除停用词和标点）

    Args:
        text: 输入文本
        stopwords: 停用词集合，如不提供则自动加载
        remove_punct: 是否移除标点符号

    Returns:
        list[str]: 有效词列表
    """
    import string

    if stopwords is None:
        stopwords = load_chinese_stopwords()

    words = jieba.cut(text)
    effective_words = [
        w for w in words if w.strip() and w not in stopwords and (not remove_punct or w not in string.punctuation)
    ]
    return effective_words


def count_effective_words_jieba(text: str, stopwords: set[str] | None = None) -> int:
    """
    计算中文文本的有效词数

    Args:
        text: 输入文本
        stopwords: 停用词集合

    Returns:
        int: 有效词数量
    """
    return len(get_effective_words_jieba(text, stopwords))


def analyze_chinese_connector(words: list[str], connector_idx: int, min_context_words: int = 5) -> bool:
    """
    分析中文连接词是否应该触发分割

    Args:
        words: 分词后的词语列表
        connector_idx: 连接词索引位置
        min_context_words: 连接词前后需要的最少词数

    Returns:
        bool: 是否应该在此处分割
    """
    if connector_idx < 1 or connector_idx >= len(words) - 1:
        return False

    connector = words[connector_idx]
    if connector not in CHINESE_CONNECTORS:
        return False

    # 检查前后词数
    left_words = words[max(0, connector_idx - min_context_words) : connector_idx]
    right_words = words[connector_idx + 1 : min(len(words), connector_idx + min_context_words + 1)]

    import string

    left_words = [w for w in left_words if w.strip() and w not in string.punctuation]
    right_words = [w for w in right_words if w.strip() and w not in string.punctuation]

    return len(left_words) >= min_context_words and len(right_words) >= min_context_words


def is_valid_phrase_spacy(phrase: spacy.tokens.Span) -> bool:
    """
    检查 Spacy 短语是否有效（包含主语和动词）

    Args:
        phrase: Spacy Span 对象

    Returns:
        bool: 是否为有效短语
    """
    has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] or token.pos_ == "PRON" for token in phrase)
    has_verb = any(token.pos_ in ("VERB", "AUX") for token in phrase)
    return has_subject and has_verb


def get_phrase_token_count(phrase: spacy.tokens.Span, include_punct: bool = False) -> int:
    """
    计算 Spacy 短语中的 token 数量

    Args:
        phrase: Spacy Span 对象
        include_punct: 是否包含标点符号

    Returns:
        int: token 数量
    """
    if include_punct:
        return len(phrase)
    return sum(1 for token in phrase if not token.is_punct)


def split_text_by_punctuation(text: str, punctuation: tuple[str, ...], joiner: str = " ") -> list[str]:
    """
    按标点符号分割文本

    Args:
        text: 输入文本
        punctuation: 标点符号元组
        joiner: 合并文本时的连接符

    Returns:
        list[str]: 分割后的句子列表
    """
    import re

    # 构建正则表达式
    pattern = f"[{''.join(re.escape(p) for p in punctuation)}]"

    # 分割
    raw_sentences = re.split(pattern, text)

    # 过滤空句子并去除首尾空白
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    return sentences


def prepare_dataframe(df: pd.DataFrame, language: str) -> tuple[pd.DataFrame, str]:
    """
    准备用于 NLP 处理的 DataFrame

    Args:
        df: 输入 DataFrame
        language: 语言代码

    Returns:
        tuple: (处理后的 DataFrame, 连接符)
    """
    joiner = get_joiner(language)
    logger.info(f"Using {language} language joiner: '{joiner}'")

    # 清理文本
    df = df.copy()
    df.text = df.text.apply(lambda x: x.strip('"').strip(""))

    return df, joiner


def merge_dataframe_text(df: pd.DataFrame, joiner: str) -> str:
    """
    合并 DataFrame 中的文本列

    Args:
        df: 输入 DataFrame
        joiner: 文本连接符

    Returns:
        str: 合并后的文本
    """
    return joiner.join(df.text.to_list())


if __name__ == "__main__":
    # 测试代码
    from core.utils.common import get_joiner

    # 测试加载停用词
    try:
        stopwords = load_chinese_stopwords()
        print(f"Loaded {len(stopwords)} stopwords")
    except Exception as e:
        print(f"Failed to load stopwords: {e}")

    # 测试分词
    test_text = "这是一个测试句子，用于验证分词功能是否正常工作。"
    words = get_effective_words_jieba(test_text)
    print(f"Effective words: {words}")
    print(f"Count: {len(words)}")
