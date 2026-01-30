"""Spacy NLP 模型加载模块。

从 temp/tools/spacy_utils/load_nlp_model.py 迁移。
提供 NLP 模型加载和语言检测功能。
"""

from pathlib import Path

import spacy
from loguru import logger
from spacy.cli import download

from core.config import get_settings
from core.paths import paths

settings = get_settings()


def get_spacy_model(language: str) -> str:
    """获取指定语言的 Spacy 模型名称。

    Args:
        language: 语言代码（如 "en", "zh", "ja"）

    Returns:
        Spacy 模型名称
    """
    model = settings.spacy_model_map.get(language.lower(), "en_core_web_md")
    if language not in settings.spacy_model_map:
        logger.warning(f"Spacy model does not support '{language}', using en_core_web_md as fallback")
    return model


def init_nlp(language: str | None = None) -> spacy.Language:
    """初始化 Spacy NLP 模型。

    Args:
        language: 语言代码（可选，默认使用配置中的语言）

    Returns:
        Spacy NLP 模型对象

    注意：
        此函数是同步的，可能需要较长时间下载模型。
    """
    if language is None:
        language = settings.whisper_language

    model = get_spacy_model(language)
    logger.info(f"Loading NLP Spacy model: {model}")

    try:
        nlp = spacy.load(model)
    except Exception:
        logger.warning(f"Downloading {model} model...")
        logger.warning("If download failed, please check your network and try again.")
        download(model)
        nlp = spacy.load(model)

    logger.info("NLP Spacy model loaded successfully!")
    return nlp


# 定义中间文件路径
SPLIT_BY_COMMA_FILE = paths.log_dir / "split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = paths.log_dir / "split_by_connector.txt"
SPLIT_BY_MARK_FILE = paths.log_dir / "split_by_mark.txt"


__all__ = [
    "get_spacy_model",
    "init_nlp",
    "SPLIT_BY_COMMA_FILE",
    "SPLIT_BY_CONNECTOR_FILE",
    "SPLIT_BY_MARK_FILE",
]
