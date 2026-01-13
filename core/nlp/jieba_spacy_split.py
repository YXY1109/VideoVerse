"""
统一的多语言文本分割模块

支持中文（使用 jieba）和其他语言（使用 Spacy）的文本分割。
遵循 Python 最佳实践：类型提示、策略模式、文档字符串。
"""

import re
import string
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

import jieba
import pandas as pd
from loguru import logger

# 导入常量和工具函数
from core.nlp.nlp_constants import (
    CHINESE_COMMA,
    CHINESE_PUNCTUATION,
    get_language_config,
    is_chinese,
)
from core.nlp.nlp_split import (
    analyze_chinese_connector,
    get_effective_words_jieba,
    is_valid_phrase_spacy,
    load_chinese_stopwords,
    load_spacy_model,
    merge_dataframe_text,
    prepare_dataframe,
)

if TYPE_CHECKING:
    pass


class SplitStrategy(ABC):
    """文本分割策略抽象基类"""

    @abstractmethod
    def split_by_mark(self, df: pd.DataFrame, language: str) -> List[str]:
        """按标点符号分割"""
        pass

    @abstractmethod
    def split_by_comma(self, sentences: List[str]) -> List[str]:
        """按逗号分割"""
        pass

    @abstractmethod
    def split_by_connectors(self, sentences: List[str]) -> List[str]:
        """按连接词分割"""
        pass

    @abstractmethod
    def split_long_sentences(self, sentences: List[str], max_tokens: int) -> List[str]:
        """分割长句子"""
        pass


class ChineseSplitStrategy(SplitStrategy):
    """中文文本分割策略（使用 jieba）"""

    def __init__(self):
        self._stopwords: Optional[set[str]] = None

    @property
    def stopwords(self) -> set[str]:
        """延迟加载停用词"""
        if self._stopwords is None:
            try:
                self._stopwords = load_chinese_stopwords()
            except Exception as e:
                logger.warning(f"Failed to load stopwords: {e}, using empty set")
                self._stopwords = set()
        return self._stopwords

    def split_by_mark(self, df: pd.DataFrame, language: str) -> List[str]:
        """
        按标点符号分割中文文本
        处理连字符连接（...、-）
        """
        df, joiner = prepare_dataframe(df, language)
        input_text = merge_dataframe_text(df, joiner)

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
                result[-1] += sentence
            else:
                result.append(sentence)

        logger.info(f"Split {len(result)} sentences by punctuation marks (jieba)")
        return result

    def split_by_comma(self, sentences: List[str]) -> List[str]:
        """
        按逗号分割中文句子
        检查左右是否构成完整句子（>=3 词）
        """
        all_split_sentences = []

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
                left_words = get_effective_words_jieba(current_part, self.stopwords)
                right_words = get_effective_words_jieba(next_part, self.stopwords)

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

    def split_by_connectors(self, sentences: List[str]) -> List[str]:
        """
        按连接词分割中文句子
        连接词：因为、所以、但是、而且等
        """
        all_split_sentences = []

        for sentence in sentences:
            split_sentences = self._split_by_connectors_single(sentence.strip())
            all_split_sentences.extend(split_sentences)

        logger.info(f"Sentences split by connectors (jieba)")
        return all_split_sentences

    def _split_by_connectors_single(self, text: str, context_words: int = 5) -> List[str]:
        """单个句子的连接词分割"""
        words = list(jieba.cut(text))
        sentences = [text]

        # 迭代处理，避免同时多处分割
        while True:
            split_occurred = False
            new_sentences = []

            for sent in sentences:
                words = list(jieba.cut(sent))

                for i, word in enumerate(words):
                    if analyze_chinese_connector(words, i):
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

    def split_long_sentences(self, sentences: List[str], max_tokens: int = 60) -> List[str]:
        """
        分割超长中文句子
        使用贪心算法在合适位置分割（>60 token）
        """
        all_split_sentences = []

        for sentence in sentences:
            words = list(jieba.cut(sentence.strip()))

            if len(words) > max_tokens:
                logger.debug(f"Splitting long sentences: {sentence[:30]}...")
                split_sentences = self._split_long_sentence_single(sentence.strip(), max_tokens)

                # 如果还有超长句子，强制平均分割
                if any(len(list(jieba.cut(sent))) > max_tokens for sent in split_sentences):
                    split_sentences = [
                        subsent
                        for sent in split_sentences
                        for subsent in self._split_extremely_long_sentence(sent, max_tokens)
                    ]

                all_split_sentences.extend(split_sentences)
            else:
                all_split_sentences.append(sentence.strip())

        # 过滤空句子和仅包含标点的句子
        filtered_sentences = self._filter_invalid_sentences(all_split_sentences)

        logger.info(f"Long sentences split (jieba)")
        return filtered_sentences

    def _split_long_sentence_single(self, text: str, max_tokens: int = 60) -> List[str]:
        """分割单个长句子"""
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

    def _split_extremely_long_sentence(self, text: str, max_tokens: int = 60) -> List[str]:
        """分割极长句子（平均分割）"""
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

    def _filter_invalid_sentences(self, sentences: List[str]) -> List[str]:
        """过滤空句子和仅包含标点的句子"""
        punctuation = string.punctuation + "'" + '"'
        filtered_sentences = []

        for i, sentence in enumerate(sentences):
            stripped_sentence = sentence.strip()
            if not stripped_sentence or all(char in punctuation for char in stripped_sentence):
                logger.warning(f"Empty or punctuation-only line detected at index {i}")
                if filtered_sentences:
                    filtered_sentences[-1] += sentence
                continue
            filtered_sentences.append(sentence)

        return filtered_sentences


class SpacySplitStrategy(SplitStrategy):
    """Spacy 文本分割策略（用于非中文语言）"""

    def __init__(self, language: str):
        """
        初始化 Spacy 分割策略

        Args:
            language: 语言代码
        """
        self.language = language
        self.nlp = load_spacy_model(language)
        self.config = get_language_config(language)

    def split_by_mark(self, df: pd.DataFrame, language: str) -> List[str]:
        """按标点符号分割（使用 Spacy 句子分割器）"""
        df, joiner = prepare_dataframe(df, language)
        input_text = merge_dataframe_text(df, joiner)

        doc = self.nlp(input_text)
        if not doc.has_annotation("SENT_START"):
            logger.warning("Spacy model does not support sentence boundary detection")

        # 处理连字符连接
        sentences_by_mark = []
        current_sentence = []

        for sent in doc.sents:
            text = sent.text.strip()

            # 检查是否需要合并（处理 ... 和 -）
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

        if current_sentence:
            sentences_by_mark.append(' '.join(current_sentence))

        # 合并仅包含标点的行到上一行
        result = []
        for i, sentence in enumerate(sentences_by_mark):
            if i > 0 and sentence.strip() in [',', '.']:
                result[-1] += sentence
            else:
                result.append(sentence)

        logger.info(f"Split {len(result)} sentences by punctuation marks (spacy)")
        return result

    def split_by_comma(self, sentences: List[str]) -> List[str]:
        """按逗号分割"""
        all_split_sentences = []

        for sentence in sentences:
            split_sentences = self._split_by_comma_single(sentence.strip())
            all_split_sentences.extend(split_sentences)

        logger.info(f"Sentences split by commas (spacy)")
        return all_split_sentences

    def _split_by_comma_single(self, text: str) -> List[str]:
        """单个句子的逗号分割"""
        doc = self.nlp(text)
        sentences = []
        start = 0

        for i, token in enumerate(doc):
            if token.text == self.config.comma:
                if self._is_suitable_for_comma_split(doc, start, token):
                    sentences.append(doc[start:token.i].text.strip())
                    logger.debug(f"Split at comma: {doc[start:token.i][-4:]},| {doc[token.i + 1:][:4]}")
                    start = token.i + 1

        sentences.append(doc[start:].text.strip())
        return sentences

    def _is_suitable_for_comma_split(self, doc: "spacy.tokens.Doc", start: int, token: "spacy.tokens.Token") -> bool:
        """判断是否适合在逗号处分割"""
        left_phrase = doc[max(start, token.i - 9):token.i]
        right_phrase = doc[token.i + 1:min(len(doc), token.i + 10)]

        # 检查右侧是否为有效短语
        suitable = is_valid_phrase_spacy(right_phrase)

        # 检查词数
        import itertools
        left_words = [t for t in left_phrase if not t.is_punct]
        right_words = list(itertools.takewhile(lambda t: not t.is_punct, right_phrase))

        if len(left_words) <= 3 or len(right_words) <= 3:
            suitable = False

        return suitable

    def split_by_connectors(self, sentences: List[str]) -> List[str]:
        """按连接词分割"""
        all_split_sentences = []

        for sentence in sentences:
            split_sentences = self._split_by_connectors_single(sentence.strip())
            all_split_sentences.extend(split_sentences)

        logger.info(f"Sentences split by connectors (spacy)")
        return all_split_sentences

    def _split_by_connectors_single(self, text: str, context_words: int = 5) -> List[str]:
        """单个句子的连接词分割"""
        doc = self.nlp(text)
        sentences = [doc.text]

        # 迭代处理，避免同时多处分割
        while True:
            split_occurred = False
            new_sentences = []

            for sent in sentences:
                doc = self.nlp(sent)
                start = 0

                for i, token in enumerate(doc):
                    split_before = self._analyze_connectors(doc, token)

                    # 检查是否为缩写
                    if i + 1 < len(doc) and doc[i + 1].text in ["'s", "'re", "'ve", "'ll", "'d"]:
                        continue

                    left_words = doc[max(0, token.i - context_words):token.i]
                    right_words = doc[token.i + 1:min(len(doc), token.i + context_words + 1)]

                    left_words = [word.text for word in left_words if not word.is_punct]
                    right_words = [word.text for word in right_words if not word.is_punct]

                    if len(left_words) >= context_words and len(right_words) >= context_words and split_before:
                        logger.debug(
                            f"Split before '{token.text}': {' '.join(left_words)}| {token.text} {' '.join(right_words)}")
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

    def _analyze_connectors(self, doc: "spacy.tokens.Doc", token: "spacy.tokens.Token") -> bool:
        """
        分析 token 是否为应该触发分割的连接词

        参考 src/tools/spacy_utils/split_by_connector.py 的 analyze_connectors 函数
        """
        lang = doc.lang_

        # 检查是否为连接词
        if token.text.lower() not in self.config.connectors:
            return False

        # 英语特殊处理：that
        if lang == "en" and token.text.lower() == "that":
            if token.dep_ == self.config.mark_dep and token.head.pos_ == self.config.verb_pos:
                return True
            else:
                return False

        # 检查依赖关系
        if token.dep_ in self.config.det_pron_deps and token.head.pos_ in self.config.noun_pos:
            return False

        return True

    def split_long_sentences(self, sentences: List[str], max_tokens: int = 60) -> List[str]:
        """分割长句子"""
        all_split_sentences = []

        for sentence in sentences:
            doc = self.nlp(sentence.strip())
            if len(doc) > max_tokens:
                logger.debug(f"Splitting long sentences: {sentence[:30]}...")
                split_sentences = self._split_long_sentence_single(doc, max_tokens)

                # 如果还有超长句子，强制平均分割
                if any(len(self.nlp(sent)) > max_tokens for sent in split_sentences):
                    split_sentences = [
                        subsent
                        for sent in split_sentences
                        for subsent in self._split_extremely_long_sentence(self.nlp(sent), max_tokens)
                    ]

                all_split_sentences.extend(split_sentences)
            else:
                all_split_sentences.append(sentence.strip())

        # 过滤空句子和仅包含标点的句子
        filtered_sentences = self._filter_invalid_sentences(all_split_sentences)

        logger.info(f"Long sentences split (spacy)")
        return filtered_sentences

    def _split_long_sentence_single(self, doc: "spacy.tokens.Doc", max_tokens: int = 60) -> List[str]:
        """分割单个长句子（动态规划）"""
        tokens = [token.text for token in doc]
        n = len(tokens)

        # 动态规划数组
        dp = [float('inf')] * (n + 1)
        dp[0] = 0

        # 记录最优分割点
        prev = [0] * (n + 1)

        for i in range(1, n + 1):
            for j in range(max(0, i - 100), i):
                if i - j >= 30:  # 确保句子长度至少 30
                    token = doc[i - 1]
                    if j == 0 or (token.is_sent_end or token.pos_ in ['VERB', 'AUX'] or token.dep_ == 'ROOT'):
                        if dp[j] + 1 < dp[i]:
                            dp[i] = dp[j] + 1
                            prev[i] = j

        # 重建句子
        sentences = []
        i = n
        from core.utils.common import get_joiner
        joiner = get_joiner(self.language)

        while i > 0:
            j = prev[i]
            sentences.append(joiner.join(tokens[j:i]).strip())
            i = j

        return sentences[::-1]  # 反转保持原顺序

    def _split_extremely_long_sentence(self, doc: "spacy.tokens.Doc", max_tokens: int = 60) -> List[str]:
        """分割极长句子（平均分割）"""
        tokens = [token.text for token in doc]
        n = len(tokens)

        num_parts = (n + max_tokens - 1) // max_tokens
        part_length = n // num_parts

        sentences = []
        from core.utils.common import get_joiner
        joiner = get_joiner(self.language)

        for i in range(num_parts):
            start = i * part_length
            end = start + part_length if i < num_parts - 1 else n
            sentences.append(joiner.join(tokens[start:end]))

        return sentences

    def _filter_invalid_sentences(self, sentences: List[str]) -> List[str]:
        """过滤空句子和仅包含标点的句子"""
        punctuation = string.punctuation + "'" + '"'
        filtered_sentences = []

        for i, sentence in enumerate(sentences):
            stripped_sentence = sentence.strip()
            if not stripped_sentence or all(char in punctuation for char in stripped_sentence):
                logger.warning(f"Empty or punctuation-only line detected at index {i}")
                if filtered_sentences:
                    filtered_sentences[-1] += sentence
                continue
            filtered_sentences.append(sentence)

        return filtered_sentences


def get_split_strategy(language: str) -> SplitStrategy:
    """
    工厂函数：根据语言获取对应的分割策略

    Args:
        language: 语言代码

    Returns:
        SplitStrategy: 对应的分割策略实例
    """
    if is_chinese(language):
        return ChineseSplitStrategy()
    else:
        return SpacySplitStrategy(language)


# ============ 兼容旧接口的函数 ============

def split_by_mark(df: pd.DataFrame, language: str) -> List[str]:
    """
    按标点符号分割（统一接口）

    Args:
        df: 输入 DataFrame
        language: 语言代码

    Returns:
        分割后的句子列表
    """
    strategy = get_split_strategy(language)
    return strategy.split_by_mark(df, language)


def split_by_comma(sentences: List[str], language: str) -> List[str]:
    """
    按逗号分割（统一接口）

    Args:
        sentences: 输入句子列表
        language: 语言代码

    Returns:
        分割后的句子列表
    """
    strategy = get_split_strategy(language)
    return strategy.split_by_comma(sentences)


def split_by_connectors(sentences: List[str], language: str) -> List[str]:
    """
    按连接词分割（统一接口）

    Args:
        sentences: 输入句子列表
        language: 语言代码

    Returns:
        分割后的句子列表
    """
    strategy = get_split_strategy(language)
    return strategy.split_by_connectors(sentences)


def split_long_sentences(sentences: List[str], language: str, max_tokens: int = 60) -> List[str]:
    """
    分割长句子（统一接口）

    Args:
        sentences: 输入句子列表
        language: 语言代码
        max_tokens: 最大 token 数

    Returns:
        分割后的句子列表
    """
    strategy = get_split_strategy(language)
    return strategy.split_long_sentences(sentences, max_tokens)


# ============ 主函数 ============

def process_nlp_split(df: pd.DataFrame, language: str) -> List[str]:
    """
    执行完整的 NLP 分割流程

    Args:
        df: 输入 DataFrame
        language: 语言代码

    Returns:
        最终分割后的句子列表

    Examples:
        >>> import pandas as pd
        >>> df = pd.read_excel("cleaned_chunks.xlsx")
        >>> result = process_nlp_split(df, "zh")
    """
    # Step 1: 按标点分割
    result = split_by_mark(df, language)
    logger.info(f"Step 1 - Split by mark: {len(result)} sentences")

    # Step 2: 按逗号分割
    result = split_by_comma(result, language)
    logger.info(f"Step 2 - Split by comma: {len(result)} sentences")

    # Step 3: 按连接词分割
    result = split_by_connectors(result, language)
    logger.info(f"Step 3 - Split by connectors: {len(result)} sentences")

    # Step 4: 分割长句子
    result = split_long_sentences(result, language, max_tokens=60)
    logger.info(f"Step 4 - Split long sentences: {len(result)} sentences")

    return result


if __name__ == '__main__':
    # 测试中文
    df_zh = pd.read_excel(r"D:\PycharmProjects\VideoVerse\files\demo\cleaned_chunks.xlsx")
    result_zh = process_nlp_split(df_zh, 'zh')
    print(f"中文分割结果: {len(result_zh)} 个句子")
    for i, sent in enumerate(result_zh[:5], 1):
        print(f"{i}. {sent}")
