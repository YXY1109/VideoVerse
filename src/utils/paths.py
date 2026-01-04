"""
VideoVerse 路径定义

定义所有中间产出文件和输出文件的路径
"""
from pathlib import Path

# ==================== 目录定义 ====================
# 获取项目根目录 (src/utils/paths.py -> src/utils -> src -> root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
LOG_DIR = OUTPUT_DIR / "log"
GPT_LOG_DIR = OUTPUT_DIR / "gpt_log"
AUDIO_REFERS_DIR = AUDIO_DIR / "refers"
AUDIO_SEGS_DIR = AUDIO_DIR / "segs"
AUDIO_TMP_DIR = AUDIO_DIR / "tmp"

# ==================== 中间产出文件 ====================
# 第 2 步：ASR 输出
CLEANED_CHUNKS = LOG_DIR / "cleaned_chunks.xlsx"

# 第 3 步：句子分割
SPLIT_BY_NLP = LOG_DIR / "split_by_nlp.txt"
SPLIT_BY_MEANING = LOG_DIR / "split_by_meaning.txt"

# 第 4 步：摘要和翻译
TERMINOLOGY = LOG_DIR / "terminology.json"
TRANSLATION_RESULTS = LOG_DIR / "translation_results.xlsx"
TRANSLATION_FOR_SUBTITLES = LOG_DIR / "translation_results_for_subtitles.xlsx"
TRANSLATION_REMERGED = LOG_DIR / "translation_results_remerged.xlsx"

# 第 8 步：音频任务
AUDIO_TASKS = AUDIO_DIR / "tts_tasks.xlsx"

# ==================== 音频文件 ====================
RAW_AUDIO_FILE = AUDIO_DIR / "raw.mp3"
VOCAL_AUDIO_FILE = AUDIO_DIR / "vocal.mp3"
BACKGROUND_AUDIO_FILE = AUDIO_DIR / "background.mp3"

# ==================== 视频文件 ====================
# 输入视频
INPUT_VIDEO_FILE = OUTPUT_DIR / "input_video.mp4"

# 输出视频
OUTPUT_VIDEO_WITH_SUB = OUTPUT_DIR / "output_with_subtitles.mp4"
OUTPUT_VIDEO_DUBBED = OUTPUT_DIR / "output_dubbed.mp4"


# ==================== 辅助函数 ====================
def ensure_directories() -> None:
    """确保所有必要的目录存在"""
    for dir_path in [
        OUTPUT_DIR, AUDIO_DIR, LOG_DIR, GPT_LOG_DIR,
        AUDIO_REFERS_DIR, AUDIO_SEGS_DIR, AUDIO_TMP_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)


# 导出所有路径常量
__all__ = [
    # 目录
    "PROJECT_ROOT",
    "OUTPUT_DIR",
    "AUDIO_DIR",
    "LOG_DIR",
    "GPT_LOG_DIR",
    "AUDIO_REFERS_DIR",
    "AUDIO_SEGS_DIR",
    "AUDIO_TMP_DIR",
    # 中间产出
    "CLEANED_CHUNKS",
    "SPLIT_BY_NLP",
    "SPLIT_BY_MEANING",
    "TERMINOLOGY",
    "TRANSLATION_RESULTS",
    "TRANSLATION_FOR_SUBTITLES",
    "TRANSLATION_REMERGED",
    "AUDIO_TASKS",
    # 音频文件
    "RAW_AUDIO_FILE",
    "VOCAL_AUDIO_FILE",
    "BACKGROUND_AUDIO_FILE",
    # 视频文件
    "INPUT_VIDEO_FILE",
    "OUTPUT_VIDEO_WITH_SUB",
    "OUTPUT_VIDEO_DUBBED",
    # 辅助函数
    "ensure_directories",
]
