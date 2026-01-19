"""
NLP 常量定义模块

包含多语言的连接词、标点符号等常量。
遵循 Python 最佳实践：使用枚举、类型提示、文档字符串。
"""

from dataclasses import dataclass
from enum import Enum


class Language(str, Enum):
    """支持的语言枚举"""

    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    FRENCH = "fr"
    RUSSIAN = "ru"
    SPANISH = "es"
    GERMAN = "de"
    ITALIAN = "it"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LanguageConfig:
    """
    语言配置类

    Attributes:
        connectors: 连接词列表
        punctuation: 标点符号列表
        comma: 逗号字符
        mark_dep: Spacy mark 依赖标签
        det_pron_deps: Spacy det/pron 依赖标签列表
        verb_pos: 动词词性标签
        noun_pos: 名词词性标签列表
    """

    connectors: tuple[str, ...]
    punctuation: tuple[str, ...]
    comma: str
    # Spacy 依赖标签
    mark_dep: str = "mark"
    det_pron_deps: tuple[str, ...] = ("det", "pron")
    verb_pos: str = "VERB"
    noun_pos: tuple[str, ...] = ("NOUN", "PROPN")

    def __post_init__(self):
        # 确保列表是不可变的（使用 tuple）
        if isinstance(self.connectors, list):
            object.__setattr__(self, "connectors", tuple(self.connectors))
        if isinstance(self.punctuation, list):
            object.__setattr__(self, "punctuation", tuple(self.punctuation))
        if isinstance(self.det_pron_deps, tuple):
            object.__setattr__(self, "det_pron_deps", tuple(self.det_pron_deps))
        if isinstance(self.noun_pos, tuple):
            object.__setattr__(self, "noun_pos", tuple(self.noun_pos))


# 语言配置映射表
LANGUAGE_CONFIGS: dict[Language, LanguageConfig] = {
    Language.CHINESE: LanguageConfig(
        connectors=(
            "因为",
            "所以",
            "但是",
            "而且",
            "虽然",
            "如果",
            "即使",
            "尽管",
            "另外",
            "此外",
            "因此",
            "不过",
            "然而",
            "可是",
            "接着",
            "然后",
        ),
        punctuation=("。", "！", "？", "，", "；", "：", "、", "…"),
        comma="，",
    ),
    Language.ENGLISH: LanguageConfig(
        connectors=("that", "which", "where", "when", "because", "but", "and", "or"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
    ),
    Language.JAPANESE: LanguageConfig(
        connectors=("けれども", "しかし", "だから", "それで", "ので", "のに", "ため"),
        punctuation=("。", "！", "？", "、", "；", "：", "…"),
        comma="、",
        det_pron_deps=("case",),
    ),
    Language.FRENCH: LanguageConfig(
        connectors=("que", "qui", "où", "quand", "parce que", "mais", "et", "ou"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
    ),
    Language.RUSSIAN: LanguageConfig(
        connectors=("что", "который", "где", "когда", "потому что", "но", "и", "или"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
        det_pron_deps=("det",),
    ),
    Language.SPANISH: LanguageConfig(
        connectors=("que", "cual", "donde", "cuando", "porque", "pero", "y", "o"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
    ),
    Language.GERMAN: LanguageConfig(
        connectors=("dass", "welche", "wo", "wann", "weil", "aber", "und", "oder"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
    ),
    Language.ITALIAN: LanguageConfig(
        connectors=("che", "quale", "dove", "quando", "perché", "ma", "e", "o"),
        punctuation=(".", "!", "?", ",", ";", ":", "…"),
        comma=",",
    ),
}

# Spacy 模型映射表
SPACY_MODEL_MAP: dict[str, str] = {
    "en": "en_core_web_md",
    "ru": "ru_core_news_md",
    "fr": "fr_core_news_md",
    "ja": "ja_core_news_md",
    "es": "es_core_news_md",
    "de": "de_core_news_md",
    "it": "it_core_news_md",
    # 中文使用 jieba，不需要 Spacy 模型
}


def get_language_config(language: str) -> LanguageConfig:
    """
    获取指定语言的配置

    Args:
        language: 语言代码 (如 'zh', 'en', 'ja')

    Returns:
        LanguageConfig: 该语言的配置对象

    Raises:
        KeyError: 当语言不支持时
    """
    try:
        lang = Language(language)
    except ValueError:
        # 默认使用英文配置
        lang = Language.ENGLISH
    return LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS[Language.ENGLISH])


def is_chinese(language: str) -> bool:
    """判断是否为中文"""
    return language.lower() in ("zh", "chinese", "cn")


def get_spacy_model(language: str) -> str:
    """
    获取指定语言的 Spacy 模型名称

    Args:
        language: 语言代码

    Returns:
        Spacy 模型名称，不支持的语言默认返回 en_core_web_md
    """
    return SPACY_MODEL_MAP.get(language.lower(), "en_core_web_md")


# 中文专用常量
CHINESE_CONNECTORS = LANGUAGE_CONFIGS[Language.CHINESE].connectors
CHINESE_PUNCTUATION = LANGUAGE_CONFIGS[Language.CHINESE].punctuation
CHINESE_COMMA = LANGUAGE_CONFIGS[Language.CHINESE].comma
