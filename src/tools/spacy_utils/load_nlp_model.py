import spacy
from spacy.cli import download

from loguru import logger

from src.utils.common import settings
from src.utils.decorators import async_except_handler

SPACY_MODEL_MAP = settings.spacy_model_map


def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_md")
    if language not in SPACY_MODEL_MAP:
        logger.warning(f"Spacy model does not support '{language}', using en_core_web_md model as fallback...")
    return model


def init_nlp():
    """
    初始化 Spacy NLP 模型

    注意：此函数是同步的，需要在异步上下文中使用 asyncio.to_thread 调用
    """
    language = "en" if settings.whisper_language == "en" else settings.whisper_language
    model = get_spacy_model(language)
    logger.info(f"Loading NLP Spacy model: {model}")
    try:
        nlp = spacy.load(model)
    except:
        logger.warning(f"Downloading {model} model...")
        logger.warning("If download failed, please check your network and try again.")
        download(model)
        nlp = spacy.load(model)
    logger.info("NLP Spacy model loaded successfully!")
    return nlp


# --------------------
# define the intermediate files
# --------------------
SPLIT_BY_COMMA_FILE = "output/log/split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = "output/log/split_by_connector.txt"
SPLIT_BY_MARK_FILE = "output/log/split_by_mark.txt"
