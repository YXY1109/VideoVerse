from typing import Dict

import pandas as pd
from loguru import logger


def process_transcription(result: Dict) -> pd.DataFrame:
    """处理转录结果"""
    all_words = []
    for segment in result['segments']:
        speaker_id = segment.get('speaker_id', None)

        for word in segment['words']:
            word["word"] = fix_mojibake_text(word["word"])

            if len(word["word"]) > 30:
                logger.warning(f"Detected word longer than 30 characters, skipping: {word['word']}")
                continue

            word["word"] = word["word"].replace('»', '').replace('«', '')

            if 'start' not in word and 'end' not in word:
                if all_words:
                    word_dict = {
                        'text': word["word"],
                        'start': all_words[-1]['end'],
                        'end': all_words[-1]['end'],
                        'speaker_id': speaker_id
                    }
                    all_words.append(word_dict)
                else:
                    next_word = next((w for w in segment['words'] if 'start' in w and 'end' in w), None)
                    if next_word:
                        word_dict = {
                            'text': word["word"],
                            'start': next_word["start"],
                            'end': next_word["end"],
                            'speaker_id': speaker_id
                        }
                        all_words.append(word_dict)
                    else:
                        raise Exception(f"No next word with timestamp found: {word}")
            else:
                word_dict = {
                    'text': f'{word["word"]}',
                    'start': word.get('start', all_words[-1]['end'] if all_words else 0),
                    'end': word['end'],
                    'speaker_id': speaker_id
                }
                all_words.append(word_dict)

    return pd.DataFrame(all_words)


def fix_mojibake_text(text: str) -> str:
    """修复 faster-whisper 输出的乱码中文文本"""
    if not text:
        return text

    # 已经包含中文，直接返回
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return text

    # 尝试多种编码修复方式
    encoding_attempts = [
        ('latin-1', 'utf-8'),
        ('iso-8859-1', 'utf-8'),
        ('cp1252', 'utf-8'),
        ('gbk', 'utf-8'),
        ('gb2312', 'utf-8'),
        ('big5', 'utf-8'),
    ]

    for encode_from, decode_to in encoding_attempts:
        try:
            fixed = text.encode(encode_from).decode(decode_to)
            if any('\u4e00' <= c <= '\u9fff' for c in fixed):
                logger.info(f"Fixed encoding using {encode_from} -> {decode_to}")
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
            continue

    return text


def save_results(df: pd.DataFrame, output_path: str) -> None:
    """同步保存结果"""
    initial_rows = len(df)
    df = df[df['text'].str.len() > 0]
    removed_rows = initial_rows - len(df)
    if removed_rows > 0:
        logger.info(f"Removed {removed_rows} row(s) with empty text")

    long_words = df[df['text'].str.len() > 30]
    if not long_words.empty:
        logger.warning(f"Detected {len(long_words)} word(s) longer than 30 characters. Removing them.")
        df = df[df['text'].str.len() <= 30]

    df['text'] = df['text'].apply(lambda x: f'"{x}"')
    df.to_excel(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
