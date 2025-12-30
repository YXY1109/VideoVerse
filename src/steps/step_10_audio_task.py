"""
步骤 10: 音频任务生成

生成 TTS 音频任务列表
"""
import asyncio
import datetime
import re
from pathlib import Path

import pandas as pd

from src.config import get_settings
from src.utils.paths import AUDIO_DIR, AUDIO_TASKS
from src.utils.decorators import async_check_file_exists
from src.utils.llm import ask_llm
from src.tools.prompts import get_subtitle_trim_prompt

from loguru import logger
settings = get_settings()

TRANS_SUBS_FOR_AUDIO_FILE = AUDIO_DIR / "trans_subs_for_audio.srt"
SRC_SUBS_FOR_AUDIO_FILE = AUDIO_DIR / "src_subs_for_audio.srt"


def time_diff_seconds(t1, t2, base_date):
    """计算两个时间对象之间的秒数差"""
    dt1 = datetime.datetime.combine(base_date, t1)
    dt2 = datetime.datetime.combine(base_date, t2)
    return (dt2 - dt1).total_seconds()


async def check_len_then_trim_async(text: str, duration: float) -> str:
    """异步检查并裁剪过长的字幕"""
    try:
        from src.backends.tts.estimate_duration import init_estimator, estimate_duration
        estimator = init_estimator()
        estimated_duration = estimate_duration(text, estimator) / settings.speed_factor_max
    except Exception:
        # 粗略估算：每秒约10个字符
        estimated_duration = len(text) / 10.0

    logger.info(f"Subtitle text: {text}, Estimated reading duration: {estimated_duration:.2f} seconds")

    if estimated_duration > duration:
        logger.warning(
            f"Estimated reading duration {estimated_duration:.2f} seconds exceeds "
            f"given duration {duration:.2f} seconds, shortening..."
        )
        original_text = text
        prompt = get_subtitle_trim_prompt(text, duration)

        def valid_trim(response):
            if 'result' not in response:
                return {'status': 'error', 'message': 'No result in response'}
            return {'status': 'success', 'message': ''}

        try:
            response = await ask_llm(prompt, resp_type='json', log_title='sub_trim', valid_def=valid_trim)
            shortened_text = response['result']
        except Exception:
            logger.warning("AI refused to answer, manually removing punctuation")
            shortened_text = re.sub(r'[,.!?;:，。！？；：]', ' ', text).strip()

        logger.info(f"Subtitle before shortening: {original_text}")
        logger.info(f"Subtitle after shortening: {shortened_text}")
        return shortened_text
    else:
        return text


def check_len_then_trim_sync(text: str, duration: float) -> str:
    """同步版本的字幕长度检查和裁剪"""
    # 在同步上下文中运行异步函数
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 使用新线程运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, check_len_then_trim_async(text, duration))
                return future.result()
        else:
            return asyncio.run(check_len_then_trim_async(text, duration))
    except Exception:
        # 如果估算失败，简单返回原文
        return text


def process_srt_sync() -> pd.DataFrame:
    """同步处理 SRT 文件，生成音频任务"""
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


@async_check_file_exists(AUDIO_TASKS)
async def step_10_audio_task(subtitle_file: str = None) -> str:
    """
    流水线第十步：生成音频任务

    Args:
        subtitle_file: 字幕文件路径（可选，默认使用 trans_subs_for_audio.srt）

    Returns:
        音频任务文件路径
    """
    logger.info("Starting audio task generation")

    # 处理 SRT 文件
    df = await asyncio.to_thread(process_srt_sync)
    logger.info(f"Generated {len(df)} audio tasks")

    # 保存结果
    await asyncio.to_thread(df.to_excel, AUDIO_TASKS, index=False)

    logger.info(f"Audio task generation complete: {AUDIO_TASKS}")
    return str(AUDIO_TASKS)
