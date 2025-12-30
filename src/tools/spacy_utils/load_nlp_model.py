import spacy
from spacy.cli import download

from src.utils.common import rprint, settings
from src.utils.decorators import async_except_handler

SPACY_MODEL_MAP = settings.spacy_model_map


def get_spacy_model(language: str):
    model = SPACY_MODEL_MAP.get(language.lower(), "en_core_web_md")
    if language not in SPACY_MODEL_MAP:
        rprint(f"[yellow]Spacy model does not support '{language}', using en_core_web_md model as fallback...[/yellow]")
    return model


def init_nlp():
    """
    初始化 Spacy NLP 模型

    注意：此函数是同步的，需要在异步上下文中使用 asyncio.to_thread 调用
    """
    language = "en" if settings.whisper_language == "en" else settings.whisper_language
    model = get_spacy_model(language)
    rprint(f"[blue]⏳ Loading NLP Spacy model: <{model}> ...[/blue]")
    try:
        nlp = spacy.load(model)
    except:
        rprint(f"[yellow]Downloading {model} model...[/yellow]")
        rprint("[yellow]If download failed, please check your network and try again.[/yellow]")
        download(model)
        nlp = spacy.load(model)
    rprint("[green]✅ NLP Spacy model loaded successfully![/green]")
    return nlp


# --------------------
# define the intermediate files
# --------------------
SPLIT_BY_COMMA_FILE = "output/log/split_by_comma.txt"
SPLIT_BY_CONNECTOR_FILE = "output/log/split_by_connector.txt"
SPLIT_BY_MARK_FILE = "output/log/split_by_mark.txt"
