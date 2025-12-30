"""
VideoVerse 异步流水线

实现 13 步视频处理流水线
"""
import asyncio
import logging
from typing import Optional
import importlib

from .config import get_settings
from .utils.paths import (
    ensure_directories,
    OUTPUT_VIDEO_DUBBED,
    OUTPUT_VIDEO_WITH_SUB,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _load_step_module(name: str):
    """动态加载步骤模块"""
    return importlib.import_module(f".{name}", package="videoverse.core.steps")


# 加载所有步骤模块
_download_module = _load_step_module("01_download")
_asr_module = _load_step_module("02_asr")
_nlp_split_module = _load_step_module("03_nlp_split")
_meaning_split_module = _load_step_module("04_meaning_split")
_summarize_module = _load_step_module("05_summarize")
_translate_module = _load_step_module("06_translate")
_split_sub_module = _load_step_module("07_split_sub")
_gen_sub_module = _load_step_module("08_gen_sub")
_burn_sub_module = _load_step_module("09_burn_sub")
_audio_task_module = _load_step_module("10_audio_task")
_gen_audio_module = _load_step_module("11_gen_audio")
_merge_audio_module = _load_step_module("12_merge_audio")
_dubbing_module = _load_step_module("13_dubbing")


async def run_pipeline(
    video_source: str,
    source_language: str = "zh",
    target_language: str = "en",
    dubbing: bool = False,
) -> str:
    """
    运行完整的异步流水线

    Args:
        video_source: YouTube URL 或本地视频路径
        source_language: 源语言代码
        target_language: 目标语言代码
        dubbing: 是否生成配音

    Returns:
        输出视频路径
    """
    ensure_directories()

    logger.info("=" * 60)
    logger.info("Starting VideoVerse Pipeline")
    logger.info(f"Source: {video_source}")
    logger.info(f"Languages: {source_language} -> {target_language}")
    logger.info(f"Dubbing: {dubbing}")
    logger.info("=" * 60)

    # 步骤 1: 下载视频
    logger.info("[1/13] Downloading video...")
    video_path = await _download_module.step_01_download(video_source)
    logger.info(f"[1/13] ✓ Video downloaded: {video_path}")

    # 步骤 2: 语音识别 (ASR)
    logger.info("[2/13] Running ASR...")
    asr_result = await _asr_module.step_02_asr(video_path, source_language)
    logger.info(f"[2/13] ✓ ASR complete: {asr_result}")

    # 步骤 3: NLP 分割
    logger.info("[3/13] NLP splitting...")
    nlp_split = await _nlp_split_module.step_03_nlp_split(asr_result, source_language)
    logger.info(f"[3/13] ✓ NLP split complete: {nlp_split}")

    # 步骤 4: 语义分割
    logger.info("[4/13] Meaning splitting with AI...")
    meaning_split = await _meaning_split_module.step_04_meaning_split(nlp_split, source_language)
    logger.info(f"[4/13] ✓ Meaning split complete: {meaning_split}")

    # 步骤 5: 摘要
    logger.info("[5/13] Generating summary and terminology...")
    terminology = await _summarize_module.step_05_summarize(meaning_split, target_language)
    logger.info(f"[5/13] ✓ Summary complete: {terminology}")

    # 步骤 6: 翻译
    logger.info("[6/13] Translating...")
    translation = await _translate_module.step_06_translate(meaning_split, terminology, target_language)
    logger.info(f"[6/13] ✓ Translation complete: {translation}")

    # 步骤 7: 字幕分割
    logger.info("[7/13] Splitting subtitles...")
    split_sub = await _split_sub_module.step_07_split_sub(translation)
    logger.info(f"[7/13] ✓ Subtitle split complete: {split_sub}")

    # 步骤 8: 生成字幕
    logger.info("[8/13] Generating subtitle file...")
    subtitle_file = await _gen_sub_module.step_08_gen_sub(split_sub)
    logger.info(f"[8/13] ✓ Subtitle generation complete")

    # 步骤 9: 烧录字幕
    if settings.burn_subtitles:
        logger.info("[9/13] Burning subtitles to video...")
        video_with_sub = await _burn_sub_module.step_09_burn_sub(video_path, subtitle_file)
        logger.info(f"[9/13] ✓ Subtitles burned: {video_with_sub}")
    else:
        video_with_sub = video_path
        logger.info("[9/13] Skipped subtitle burning")

    # 如果不需要配音，直接返回带字幕的视频
    if not dubbing:
        logger.info("=" * 60)
        logger.info("Pipeline complete (subtitles only)")
        logger.info(f"Output: {video_with_sub}")
        logger.info("=" * 60)
        return video_with_sub

    # 步骤 10: 音频任务
    logger.info("[10/13] Generating audio tasks...")
    audio_tasks = await _audio_task_module.step_10_audio_task(subtitle_file)
    logger.info(f"[10/13] ✓ Audio tasks complete: {audio_tasks}")

    # 步骤 11: 生成音频
    logger.info("[11/13] Generating TTS audio...")
    audio_segments = await _gen_audio_module.step_11_gen_audio(audio_tasks)
    logger.info(f"[11/13] ✓ TTS audio generation complete: {audio_segments}")

    # 步骤 12: 合并音频
    logger.info("[12/13] Merging audio...")
    merged_audio = await _merge_audio_module.step_12_merge_audio(audio_segments)
    logger.info(f"[12/13] ✓ Audio merge complete: {merged_audio}")

    # 步骤 13: 配音合成
    logger.info("[13/13] Composing dubbed video...")
    dubbed_video = await _dubbing_module.step_13_dubbing(video_path, merged_audio)
    logger.info(f"[13/13] ✓ Dubbing complete: {dubbed_video}")

    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"Output: {dubbed_video}")
    logger.info("=" * 60)

    return dubbed_video


if __name__ == '__main__':
    asyncio.run(run_pipeline(
        video_source=r"D:\PycharmProjects\VideoVerse\files\demo.mp4",
        source_language="zh",
        target_language="en",
        dubbing=False,
    ))