"""
步骤 05: 内容摘要

提取视频内容的摘要和术语表
"""
import asyncio
import json
from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.utils.paths import TERMINOLOGY, SPLIT_BY_MEANING
from src.utils.llm import ask_llm
from src.utils.decorators import async_check_file_exists
from src.tools.prompts import get_summary_prompt

from loguru import logger
settings = get_settings()

CUSTOM_TERMS_PATH = 'custom_terms.xlsx'


def combine_chunks_sync() -> str:
    """Combine the text chunks identified by whisper into a single long text"""
    with open(SPLIT_BY_MEANING, 'r', encoding='utf-8') as file:
        sentences = file.readlines()
    cleaned_sentences = [line.strip() for line in sentences]
    combined_text = ' '.join(cleaned_sentences)
    summary_length = getattr(settings, 'summary_length', 3000)
    return combined_text[:summary_length]


def search_things_to_note_in_prompt(sentence: str) -> str:
    """Search for terms to note in the given sentence"""
    if not TERMINOLOGY.exists():
        return None

    with open(TERMINOLOGY, 'r', encoding='utf-8') as file:
        things_to_note = json.load(file)
    things_to_note_list = [term['src'] for term in things_to_note.get('terms', [])
                           if term['src'].lower() in sentence.lower()]
    if things_to_note_list:
        prompt = '\n'.join(
            f'{i + 1}. "{term["src"]}": "{term["tgt"]}",'
            f' meaning: {term["note"]}'
            for i, term in enumerate(things_to_note.get('terms', []))
            if term['src'] in things_to_note_list
        )
        return prompt
    else:
        return None


@async_check_file_exists(TERMINOLOGY)
async def step_05_summarize(split_file: str, target_language: str = "zh") -> str:
    """
    流水线第五步：内容摘要和术语提取

    Args:
        split_file: 分割结果文件路径
        target_language: 目标语言代码

    Returns:
        术语表文件路径
    """
    logger.info("Starting summarization")

    # Combine text chunks
    src_content = await asyncio.to_thread(combine_chunks_sync)

    # Load custom terms
    custom_terms_json = {"terms": []}
    if Path(CUSTOM_TERMS_PATH).exists():
        try:
            custom_terms = pd.read_excel(CUSTOM_TERMS_PATH)
            if len(custom_terms) > 0:
                custom_terms_json = {
                    "terms": [
                        {
                            "src": str(row.iloc[0]),
                            "tgt": str(row.iloc[1]),
                            "note": str(row.iloc[2])
                        }
                        for _, row in custom_terms.iterrows()
                    ]
                }
                logger.info(f"Custom Terms Loaded: {len(custom_terms)} terms")
        except Exception as e:
            logger.warning(f"Failed to load custom terms: {e}")

    # Generate summary prompt
    summary_prompt = get_summary_prompt(src_content, custom_terms_json)
    logger.info("Summarizing and extracting terminology ...")

    def valid_summary(response_data):
        required_keys = {'src', 'tgt', 'note'}
        if 'terms' not in response_data:
            return {"status": "error", "message": "Invalid response format"}
        for term in response_data['terms']:
            if not all(key in term for key in required_keys):
                return {"status": "error", "message": "Invalid response format"}
        return {"status": "success", "message": "Summary completed"}

    summary = await ask_llm(summary_prompt, resp_type='json', valid_def=valid_summary, log_title='summary')

    # Merge with custom terms
    if 'terms' not in summary:
        summary['terms'] = []
    summary['terms'].extend(custom_terms_json['terms'])

    # Save terminology
    TERMINOLOGY.parent.mkdir(parents=True, exist_ok=True)
    with open(TERMINOLOGY, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    logger.info(f"Summary log saved to: {TERMINOLOGY}")
    return str(TERMINOLOGY)
