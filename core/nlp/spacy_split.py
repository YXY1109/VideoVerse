import spacy
from loguru import logger
from spacy.cli import download

spacy_model_map: dict = {
    "en": "en_core_web_md",
    "ru": "ru_core_news_md",
    "fr": "fr_core_news_md",
    "ja": "ja_core_news_md",
    "es": "es_core_news_md",
    "de": "de_core_news_md",
    "it": "it_core_news_md",
}


def load_spacy_model(language: str):
    model = spacy_model_map.get(language.lower(), "en_core_web_md")
    if language not in spacy_model_map:
        logger.warning(f"Spacy model does not support '{language}', using en_core_web_md model as fallback...")
    try:
        nlp = spacy.load(model)
    except Exception as e:
        logger.warning(f"Downloading {model} model...")
        download(model)
        logger.success(f"NLP Spacy model downloaded: {model}")
        nlp = spacy.load(model)
    logger.success("NLP Spacy model loaded successfully!")
    return nlp


if __name__ == '__main__':
    load_spacy_model("ru")
