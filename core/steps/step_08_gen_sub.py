"""Step 08: Generate Subtitle.

对齐时间轴，生成 SRT 字幕文件。
从 temp/steps/step_08_gen_sub.py 迁移并转换为 PipelineStep。
"""

import re
from pathlib import Path
from typing import List

import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext

settings = get_settings()

# 字幕输出配置
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

# 尝试导入 autocorrect
try:
    import autocorrect_py as autocorrect
    AUTOCORRECT_AVAILABLE = True
except ImportError:
    AUTOCORRECT_AVAILABLE = False


def convert_to_srt_format(start_time: float, end_time: float) -> str:
    """将时间（秒）转换为 SRT 格式：小时:分钟:秒,毫秒。

    Args:
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）

    Returns:
        SRT 格式的时间戳字符串
    """

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
    """移除标点符号。

    Args:
        text: 输入文本

    Returns:
        移除标点后的文本
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def show_difference(str1: str, str2: str) -> None:
    """显示两个字符串的差异位置。

    Args:
        str1: 第一个字符串
        str2: 第二个字符串
    """
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
    """获取句子的时间戳。

    Args:
        df_words: 词级别的 DataFrame（包含 text, start, end 列）
        df_sentences: 句子级别的 DataFrame（包含 Source 列）

    Returns:
        时间戳列表 [(start, end), ...]
    """
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
        search_limit = min(current_pos + 100, len(full_words_str) - sentence_len + 1)

        while current_pos < search_limit:
            if current_pos > len(full_words_str) - sentence_len:
                break
            if full_words_str[current_pos:current_pos + sentence_len] == clean_sentence:
                start_word_idx = position_to_word_idx.get(current_pos, 0)
                end_word_idx = position_to_word_idx.get(current_pos + sentence_len - 1, start_word_idx)

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
            logger.warning(f"Original sentence: {df_sentences['Source'][idx]}")
            # 使用估算时间戳而不是抛出异常
            if time_stamp_list:
                last_end = time_stamp_list[-1][1]
                time_stamp_list.append((last_end, last_end + 3.0))
            else:
                time_stamp_list.append((0.0, 3.0))

    return time_stamp_list


def clean_translation(x) -> str:
    """美化翻译。

    Args:
        x: 输入文本

    Returns:
        清理后的文本
    """
    if pd.isna(x):
        return ''
    text = str(x).strip('。').strip('，')
    if AUTOCORRECT_AVAILABLE:
        return autocorrect.format(text)
    return text.strip()


def align_timestamp_sync(
    df_text: pd.DataFrame,
    df_translate: pd.DataFrame,
    subtitle_output_configs: list,
    output_dir: Path,
    for_display: bool = True
) -> pd.DataFrame:
    """对齐时间轴并添加新的时间戳列到 df_translate。

    Args:
        df_text: 词级别的文本 DataFrame
        df_translate: 翻译结果 DataFrame
        subtitle_output_configs: 字幕输出配置
        output_dir: 输出目录
        for_display: 是否用于显示（美化标点）

    Returns:
        包含时间戳的 DataFrame
    """
    df_trans_time = df_translate.copy()

    # 处理时间戳
    try:
        time_stamp_list = get_sentence_timestamps(df_text, df_translate)
    except Exception as e:
        logger.warning(f"Failed to get exact timestamps: {e}, using estimated timestamps")
        # 使用估算的时间戳
        time_stamp_list = [(i * 3.0, (i + 1) * 3.0) for i in range(len(df_translate))]

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


class GenSubStep(PipelineStep):
    """生成字幕步骤 - PipelineStep 实现。

    对齐时间轴，生成 SRT 字幕文件。
    """

    @property
    def name(self) -> str:
        return "step_08_gen_sub"

    @property
    def dependencies(self) -> list[str]:
        return ["step_07_split_sub"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证分割结果是否存在。"""
        split_sub_result = context.get("split_sub_result")
        if not split_sub_result:
            logger.error("No split_sub_result in context")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行字幕生成。

        Args:
            context: 流水线上下文

        Returns:
            字幕文件目录路径
        """
        logger.info("Starting subtitle generation")

        # 获取 ASR 结果
        asr_dataframe = context.get("asr_dataframe")
        split_sub_result = context.get("split_sub_result")

        # 读取数据
        df_text = asr_dataframe.copy()
        df_text['text'] = df_text['text'].str.strip('"').str.strip()

        df_translate = pd.read_excel(split_sub_result)
        df_translate['Translation'] = df_translate['Translation'].apply(clean_translation)

        # 生成显示字幕
        align_timestamp_sync(
            df_text, df_translate, SUBTITLE_OUTPUT_CONFIGS, paths.output_dir, True
        )
        logger.info(f"Subtitles generated in {paths.output_dir}")

        # 生成音频字幕
        translation_remerged = context.get("translation_remerged")
        if translation_remerged and Path(translation_remerged).exists():
            df_translate_for_audio = pd.read_excel(translation_remerged)
            df_translate_for_audio['Translation'] = df_translate_for_audio['Translation'].apply(clean_translation)

            align_timestamp_sync(
                df_text, df_translate_for_audio, AUDIO_SUBTITLE_OUTPUT_CONFIGS, paths.audio_dir, True
            )
            logger.info(f"Audio subtitles generated in {paths.audio_dir}")
        else:
            # 使用 split_sub_result 生成音频字幕
            align_timestamp_sync(
                df_text, df_translate, AUDIO_SUBTITLE_OUTPUT_CONFIGS, paths.audio_dir, True
            )
            logger.info(f"Audio subtitles generated in {paths.audio_dir}")

        logger.info("Subtitle generation complete")
        context.set("subtitle_dir", str(paths.output_dir))
        return str(paths.output_dir)


def create_step() -> GenSubStep:
    """工厂函数：创建字幕生成步骤。"""
    return GenSubStep()


__all__ = ["GenSubStep", "create_step"]
