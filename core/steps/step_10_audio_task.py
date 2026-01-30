"""Step 10: Audio Task.

生成 TTS 音频任务。
从 temp/steps/step_10_audio_task.py 迁移并转换为 PipelineStep。
"""

import asyncio
import datetime
import re
from pathlib import Path

import pandas as pd
from loguru import logger

from core.config import get_settings
from core.paths import paths
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.utils.llm import ask_llm

settings = get_settings()

TRANS_SUBS_FOR_AUDIO_FILE = paths.audio_dir / "trans_subs_for_audio.srt"
SRC_SUBS_FOR_AUDIO_FILE = paths.audio_dir / "src_subs_for_audio.srt"


def time_diff_seconds(t1, t2, base_date) -> float:
    """计算两个时间对象之间的秒数差。

    Args:
        t1: 开始时间
        t2: 结束时间
        base_date: 基准日期

    Returns:
        秒数差
    """
    dt1 = datetime.datetime.combine(base_date, t1)
    dt2 = datetime.datetime.combine(base_date, t2)
    return (dt2 - dt1).total_seconds()


def check_len_then_trim(text: str, duration: float) -> str:
    """检查并裁剪过长的字幕。

    Args:
        text: 字幕文本
        duration: 目标时长（秒）

    Returns:
        裁剪后的文本
    """
    # 简化估算：每秒约10个字符
    estimated_duration = len(text) / 10.0

    logger.info(f"Subtitle text: {text}, Estimated reading duration: {estimated_duration:.2f} seconds")

    if estimated_duration > duration:
        logger.warning(
            f"Estimated reading duration {estimated_duration:.2f} seconds exceeds "
            f"given duration {duration:.2f} seconds, shortening..."
        )
        original_text = text

        # 尝试从 tools.prompts 导入，如果失败则使用简化版本
        try:
            from tools.prompts import get_subtitle_trim_prompt
            prompt = get_subtitle_trim_prompt(text, duration)
        except ImportError:
            prompt = f"""The subtitle text is too long for the given duration. Please shorten it.

Original text: {text}
Target duration: {duration:.2f} seconds

Please return a JSON with 'result' key containing the shortened text."""

        def valid_trim(response):
            if 'result' not in response:
                return {'status': 'error', 'message': 'No result in response'}
            return {'status': 'success', 'message': ''}

        try:
            response = ask_llm(prompt, resp_type='json', log_title='sub_trim', valid_def=valid_trim)
            shortened_text = response['result']
        except Exception:
            logger.warning("AI failed to answer, manually removing punctuation")
            shortened_text = re.sub(r'[,.!?;:，。！？；：]', ' ', text).strip()

        logger.info(f"Subtitle before shortening: {original_text}")
        logger.info(f"Subtitle after shortening: {shortened_text}")
        return shortened_text
    else:
        return text


def process_srt() -> pd.DataFrame:
    """处理 SRT 文件，生成音频任务。

    Returns:
        包含音频任务的 DataFrame
    """
    with open(TRANS_SUBS_FOR_AUDIO_FILE, 'r', encoding='utf-8') as file:
        content = file.read()

    with open(SRC_SUBS_FOR_AUDIO_FILE, 'r', encoding='utf-8') as src_file:
        src_content = src_file.read()

    subtitles = []
    src_subtitles = {}

    # 解析源字幕
    for block in src_content.strip().split('\n\n'):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 3:
            continue

        number = int(lines[0])
        src_text = ' '.join(lines[2:])
        src_subtitles[number] = src_text

    # 解析目标字幕
    for block in content.strip().split('\n\n'):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if len(lines) < 3:
            continue

        try:
            number = int(lines[0])
            start_time, end_time = lines[1].split(' --> ')
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S,%f').time()
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S,%f').time()
            duration = time_diff_seconds(start_time, end_time, datetime.date.today())
            text = ' '.join(lines[2:])

            # 移除括号内的内容（包括英文和中文括号）
            text = re.sub(r'\([^)]*\)', '', text).strip()
            text = re.sub(r'（[^）]*）', '', text).strip()
            # 移除 '-' 字符
            text = text.replace('-', '')

            # 添加来自 src_subs_for_audio.srt 的原文
            origin = src_subtitles.get(number, '')

        except ValueError as e:
            logger.warning(f"Unable to parse subtitle block '{block}', error: {str(e)}, skipping...")
            continue

        subtitles.append({
            'number': number,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'text': text,
            'origin': origin
        })

    df = pd.DataFrame(subtitles)

    # 合并过短的字幕
    i = 0
    min_sub_dur = settings.min_subtitle_duration
    while i < len(df):
        today = datetime.date.today()
        if df.loc[i, 'duration'] < min_sub_dur:
            if (i < len(df) - 1 and
                time_diff_seconds(df.loc[i, 'start_time'], df.loc[i + 1, 'start_time'], today) < min_sub_dur):
                logger.info(f"Merging subtitles {i + 1} and {i + 2}")
                df.loc[i, 'text'] += ' ' + df.loc[i + 1, 'text']
                df.loc[i, 'origin'] += ' ' + df.loc[i + 1, 'origin']
                df.loc[i, 'end_time'] = df.loc[i + 1, 'end_time']
                df.loc[i, 'duration'] = time_diff_seconds(df.loc[i, 'start_time'], df.loc[i, 'end_time'], today)
                df = df.drop(i + 1).reset_index(drop=True)
            else:
                if i < len(df) - 1:
                    logger.info(f"Extending subtitle {i + 1} duration to {min_sub_dur} seconds")
                    df.loc[i, 'end_time'] = (
                        datetime.datetime.combine(today, df.loc[i, 'start_time']) +
                        datetime.timedelta(seconds=min_sub_dur)
                    ).time()
                    df.loc[i, 'duration'] = min_sub_dur
                else:
                    logger.warning(f"The last subtitle {i + 1} duration is less than {min_sub_dur} seconds")
                i += 1
        else:
            i += 1

    df['start_time'] = df['start_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])
    df['end_time'] = df['end_time'].apply(lambda x: x.strftime('%H:%M:%S.%f')[:-3])

    return df


class AudioTaskStep(PipelineStep):
    """音频任务生成步骤 - PipelineStep 实现。

    生成 TTS 音频任务列表。
    """

    @property
    def name(self) -> str:
        return "step_10_audio_task"

    @property
    def dependencies(self) -> list[str]:
        return ["step_08_gen_sub"]

    async def validate(self, context: PipelineContext) -> bool:
        """验证字幕文件是否存在。"""
        if not TRANS_SUBS_FOR_AUDIO_FILE.exists():
            logger.error(f"Subtitle file not found: {TRANS_SUBS_FOR_AUDIO_FILE}")
            return False
        return True

    async def execute(self, context: PipelineContext) -> str:
        """执行音频任务生成。

        Args:
            context: 流水线上下文

        Returns:
            音频任务文件路径
        """
        logger.info("Starting audio task generation")

        # 处理 SRT 文件
        df = process_srt()
        logger.info(f"Generated {len(df)} audio tasks")

        # 保存结果
        df.to_excel(paths.audio_tasks, index=False)

        logger.info(f"Audio task generation complete: {paths.audio_tasks}")
        context.set("audio_tasks", str(paths.audio_tasks))
        return str(paths.audio_tasks)


def create_step() -> AudioTaskStep:
    """工厂函数：创建音频任务步骤。"""
    return AudioTaskStep()


__all__ = ["AudioTaskStep", "create_step"]
