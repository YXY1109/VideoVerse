from core.spacy_utils import (
    split_by_mark, split_by_comma_main, split_sentences_main,
    split_long_by_root_main, init_nlp,
    split_by_mark_jieba, split_by_comma_jieba_main,
    split_sentences_jieba_main, split_long_by_root_jieba_main,
    JIEBA_AVAILABLE
)
from core.utils import check_file_exists, load_key, rprint
from core.utils.models import _3_1_SPLIT_BY_NLP


@check_file_exists(_3_1_SPLIT_BY_NLP)
def split_by_spacy():
    """使用 Spacy 进行 NLP 分割"""
    nlp = init_nlp()
    split_by_mark(nlp)
    split_by_comma_main(nlp)
    split_sentences_main(nlp)
    split_long_by_root_main(nlp)
    return


@check_file_exists(_3_1_SPLIT_BY_NLP)
def split_by_jieba():
    """使用 jieba 进行中文 NLP 分割"""
    rprint("[blue]🔍 Using jieba for Chinese text splitting[/blue]")
    split_by_mark_jieba()
    split_by_comma_jieba_main()
    split_sentences_jieba_main()
    split_long_by_root_jieba_main()
    return


@check_file_exists(_3_1_SPLIT_BY_NLP)
def split_by_nlp():
    """
    根据语言自动选择 Spacy 或 jieba 进行 NLP 分割
    - 中文使用 jieba（如果可用）
    - 其他语言使用 Spacy
    """
    whisper_language = load_key("whisper.language")
    detected_language = load_key("whisper.detected_language")
    language = detected_language if whisper_language == 'auto' else whisper_language

    # 中文优先使用 jieba（如果可用）
    if language == 'zh' and JIEBA_AVAILABLE:
        split_by_jieba()
    else:
        split_by_spacy()
    return


if __name__ == '__main__':
    split_by_nlp()
