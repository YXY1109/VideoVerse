"""
步骤 08: 生成字幕

对齐时间轴，生成 SRT 字幕文件
"""
import asyncio
import os
import re
from pathlib import Path
from typing import List

import pandas as pd

try:
    import autocorrect_py as autocorrect
    AUTOCORRECT_AVAILABLE = True
except ImportError:
    AUTOCORRECT_AVAILABLE = False

from src.config import get_settings
from src.utils.paths import CLEANED_CHUNKS, OUTPUT_DIR, AUDIO_DIR, TRANSLATION_FOR_SUBTITLES

from loguru import logger
settings = get_settings()


SUBTITLE_OUTPUT_CONFIGS = [
    ('src.srt', ['Source']),
    ('trans.srt', ['Translation']),
    ('src_trans.srt', ['Source', 'Translation']),
    ('trans_src.srt', ['Translation', 'Source'])
]

AUDIO_SUBTITLE_OUTPUT_CONFIGS = [
    ('src_subs_for_audio.srt', ['Source']),
    ('trans_subs_for_audio.srt', ['Translation'])
]


def convert_to_srt_format(start_time: float, end_time: float) -> str:
    """将时间（秒）转换为 SRT 格式：小时:分钟:秒,毫秒"""

    def seconds_to_hmsm(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int(seconds * 1000) % 1000
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    start_srt = seconds_to_hmsm(start_time)
    end_srt = seconds_to_hmsm(end_time)
    return f"{start_srt} --> {end_srt}"


def remove_punctuation(text: str) -> str:
    """移除标点符号"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def show_difference(str1: str, str2: str):
    """显示两个字符串的差异位置"""
    min_len = min(len(str1), len(str2))
    diff_positions = []

    for i in range(min_len):
        if str1[i] != str2[i]:
            diff_positions.append(i)

    if len(str1) != len(str2):
        diff_positions.extend(range(min_len, max(len(str1), len(str2))))

    logger.warning(f"Difference positions: {diff_positions}")
    logger.warning(f"Expected sentence: {str1}")
    logger.warning(f"Actual match: {str2}")


def get_sentence_timestamps(df_words: pd.DataFrame, df_sentences: pd.DataFrame) -> List[tuple]:
    """获取句子的时间戳"""
    time_stamp_list = []

    # 构建完整字符串和位置映射
    full_words_str = ''
    position_to_word_idx = {}

    for idx, word in enumerate(df_words['text']):
        clean_word = remove_punctuation(word.lower())
        start_pos = len(full_words_str)
        full_words_str += clean_word
        for pos in range(start_pos, len(full_words_str)):
            position_to_word_idx[pos] = idx

    current_pos = 0
    for idx, sentence in df_sentences['Source'].items():
        clean_sentence = remove_punctuation(sentence.lower()).replace(" ", "")
        sentence_len = len(clean_sentence)

        # 跳过空句子
        if sentence_len == 0:
            logger.warning(f"Skipping empty sentence: {sentence}")
            continue

        match_found = False
        while current_pos <= len(full_words_str) - sentence_len:
            if full_words_str[current_pos:current_pos + sentence_len] == clean_sentence:
                start_word_idx = position_to_word_idx[current_pos]
                end_word_idx = position_to_word_idx[current_pos + sentence_len - 1]

                time_stamp_list.append((
                    float(df_words['start'][start_word_idx]),
                    float(df_words['end'][end_word_idx])
                ))

                current_pos += sentence_len
                match_found = True
                break
            current_pos += 1

        if not match_found:
            logger.warning(f"No exact match found for sentence: {sentence}")
            show_difference(
                clean_sentence,
                full_words_str[current_pos:current_pos + len(clean_sentence)]
            )
            logger.warning(f"Original sentence: {df_sentences['Source'][idx]}")
            raise ValueError("No match found for sentence.")

    return time_stamp_list


def align_timestamp_sync(
    df_text: pd.DataFrame,
    df_translate: pd.DataFrame,
    subtitle_output_configs: list,
    output_dir: Path,
    for_display: bool = True
) -> pd.DataFrame:
    """对齐时间轴并添加新的时间戳列到 df_translate"""
    df_trans_time = df_translate.copy()

    # 为 df_text['text'] 中的每个词分配 ID 并创建新的 DataFrame
    words = df_text['text'].str.split(expand=True).stack().reset_index(level=1, drop=True).reset_index()
    words.columns = ['id', 'word']
    words['id'] = words['id'].astype(int)

    # 处理时间戳
    time_stamp_list = get_sentence_timestamps(df_text, df_translate)
    df_trans_time['timestamp'] = time_stamp_list
    df_trans_time['duration'] = df_trans_time['timestamp'].apply(lambda x: x[1] - x[0])

    # 移除间隙
    for i in range(len(df_trans_time) - 1):
        delta_time = df_trans_time.loc[i + 1, 'timestamp'][0] - df_trans_time.loc[i, 'timestamp'][1]
        if 0 < delta_time < 1:
            df_trans_time.at[i, 'timestamp'] = (
                df_trans_time.loc[i, 'timestamp'][0],
                df_trans_time.loc[i + 1, 'timestamp'][0]
            )

    # 转换开始和结束时间戳为 SRT 格式
    df_trans_time['timestamp'] = df_trans_time['timestamp'].apply(
        lambda x: convert_to_srt_format(x[0], x[1])
    )

    # 美化字幕：如果 for_display 为 True，替换 Translation 中的标点
    if for_display:
        df_trans_time['Translation'] = df_trans_time['Translation'].apply(
            lambda x: re.sub(r'[，。]', ' ', x).strip()
        )

    # 输出字幕
    def generate_subtitle_string(df, columns):
        return ''.join([
            f"{i + 1}\n{row['timestamp']}\n{row[columns[0]].strip()}\n"
            f"{row[columns[1]].strip() if len(columns) > 1 else ''}\n\n"
            for i, row in df.iterrows()
        ]).strip()

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, columns in subtitle_output_configs:
            subtitle_str = generate_subtitle_string(df_trans_time, columns)
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                f.write(subtitle_str)
            logger.info(f"Generated subtitle: {output_dir / filename}")

    return df_trans_time


def clean_translation(x):
    """美化翻译"""
    if pd.isna(x):
        return ''
    if AUTOCORRECT_AVAILABLE:
        cleaned = str(x).strip('。').strip('，')
        return autocorrect.format(cleaned)
    return str(x).strip('。').strip('，').strip()


async def step_08_gen_sub(split_file: str = None) -> str:
    """
    流水线第八步：生成字幕

    Args:
        split_file: 分割后的字幕文件路径

    Returns:
        字幕文件目录路径
    """
    logger.info("Starting subtitle generation")

    if split_file is None:
        split_file = str(CLEANED_CHUNKS)

    # 读取数据
    df_text = await asyncio.to_thread(pd.read_excel, CLEANED_CHUNKS)
    df_text['text'] = df_text['text'].str.strip('"').str.strip()

    df_translate = await asyncio.to_thread(pd.read_excel, split_file)
    df_translate['Translation'] = df_translate['Translation'].apply(clean_translation)

    # 生成显示字幕
    await asyncio.to_thread(
        align_timestamp_sync,
        df_text, df_translate, SUBTITLE_OUTPUT_CONFIGS, OUTPUT_DIR, True
    )
    logger.info(f"Subtitles generated in {OUTPUT_DIR}")

    # 生成音频字幕
    remerged_file = str(TRANSLATION_FOR_SUBTITLES.parent / "translation_results_remerged.xlsx")
    if Path(remerged_file).exists():
        df_translate_for_audio = await asyncio.to_thread(pd.read_excel, remerged_file)
        df_translate_for_audio['Translation'] = df_translate_for_audio['Translation'].apply(clean_translation)

        await asyncio.to_thread(
            align_timestamp_sync,
            df_text, df_translate_for_audio, AUDIO_SUBTITLE_OUTPUT_CONFIGS, AUDIO_DIR, True
        )
        logger.info(f"Audio subtitles generated in {AUDIO_DIR}")
    else:
        # 使用 split_file 生成音频字幕
        await asyncio.to_thread(
            align_timestamp_sync,
            df_text, df_translate, AUDIO_SUBTITLE_OUTPUT_CONFIGS, AUDIO_DIR, True
        )
        logger.info(f"Audio subtitles generated in {AUDIO_DIR}")

    logger.info("Subtitle generation complete")
    return str(OUTPUT_DIR)
