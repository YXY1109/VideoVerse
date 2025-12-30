"""
VideoVerse 处理步骤模块

导出所有 13 个异步处理步骤
"""

# 步骤 01: 视频下载
from src.steps.step_01_download import step_01_download

# 步骤 02: 语音识别 (ASR)
from src.steps.step_02_asr import step_02_asr

# 步骤 03: NLP 分割
from src.steps.step_03_nlp_split import step_03_nlp_split

# 步骤 04: 语义分割
from src.steps.step_04_meaning_split import step_04_meaning_split

# 步骤 05: 摘要和术语提取
from src.steps.step_05_summarize import step_05_summarize

# 步骤 06: 翻译
from src.steps.step_06_translate import step_06_translate

# 步骤 07: 字幕分割
from src.steps.step_07_split_sub import step_07_split_sub

# 步骤 08: 生成字幕文件
from src.steps.step_08_gen_sub import step_08_gen_sub

# 步骤 09: 烧录字幕
from src.steps.step_09_burn_sub import step_09_burn_sub

# 步骤 10: 生成音频任务
from src.steps.step_10_audio_task import step_10_audio_task

# 步骤 11: 生成 TTS 音频
from src.steps.step_11_gen_audio import step_11_gen_audio

# 步骤 12: 合并音频
from src.steps.step_12_merge_audio import step_12_merge_audio

# 步骤 13: 配音合成
from src.steps.step_13_dubbing import step_13_dubbing

__all__ = [
    "step_01_download",
    "step_02_asr",
    "step_03_nlp_split",
    "step_04_meaning_split",
    "step_05_summarize",
    "step_06_translate",
    "step_07_split_sub",
    "step_08_gen_sub",
    "step_09_burn_sub",
    "step_10_audio_task",
    "step_11_gen_audio",
    "step_12_merge_audio",
    "step_13_dubbing",
]
