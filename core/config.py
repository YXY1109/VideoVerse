"""
VideoVerse 统一配置管理

整合 temp/config.py 和 core/config.py 的优点，提供完整的配置管理功能。
使用 pydantic-settings 从环境变量加载配置，支持测试环境禁用。
"""

from functools import lru_cache
from os import getenv
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path:
    """通过向上搜索查找 .env 文件。"""
    current = Path.cwd()
    while current != current.parent:
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent
    return Path(".env")


# 加载 .env 文件
env_file = _find_env_file()
if not getenv("DOTENV_DISABLED"):
    load_dotenv(env_file, override=False)


class Settings(BaseSettings):
    """VideoVerse 应用配置。

    使用 pydantic-settings 从环境变量加载配置。
    支持 .env 文件和环境变量两种方式。
    """

    # ========================================================================
    # OpenAI / LLM 配置
    # ========================================================================
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_base: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_API_BASE"
    )
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=16384, alias="OPENAI_MAX_TOKENS")
    openai_llm_support_json: bool = Field(default=True, alias="OPENAI_LLM_SUPPORT_JSON")

    # ========================================================================
    # 路径配置
    # ========================================================================
    output_dir: str = Field(default="output", alias="OUTPUT_DIR")
    model_cache_dir: str = Field(default="models", alias="MODEL_CACHE_DIR")
    temp_dir: str = Field(default="temp", alias="TEMP_DIR")

    # ========================================================================
    # 下载行为配置
    # ========================================================================
    disable_auto_download: bool = Field(default=False, alias="DISABLE_AUTO_DOWNLOAD")
    hf_endpoint: str = Field(default="https://hf-mirror.com", alias="HF_ENDPOINT")

    # ========================================================================
    # 视频配置
    # ========================================================================
    youtube_resolution: str = Field(default="1080", alias="YOUTUBE_RESOLUTION")
    allowed_video_formats: list[str] = Field(
        default=["mp4", "mov", "avi", "mkv", "flv", "wmv", "webm"],
        alias="ALLOWED_VIDEO_FORMATS"
    )
    allowed_audio_formats: list[str] = Field(
        default=["wav", "mp3", "flac", "m4a"],
        alias="ALLOWED_AUDIO_FORMATS"
    )

    # ========================================================================
    # 字幕配置
    # ========================================================================
    burn_subtitles: bool = Field(default=True, alias="BURN_SUBTITLES")
    subtitle_max_length: int = Field(default=75, alias="SUBTITLE_MAX_LENGTH")
    subtitle_target_multiplier: float = Field(default=1.2, alias="SUBTITLE_TARGET_MULTIPLIER")
    min_subtitle_duration: float = Field(default=2.5, alias="MIN_SUBTITLE_DURATION")
    min_trim_duration: float = Field(default=3.5, alias="MIN_TRIM_DURATION")
    tolerance: float = Field(default=1.5, alias="TOLERANCE")

    # ========================================================================
    # TTS 配置
    # ========================================================================
    tts_method: Literal["edge", "azure", "openai", "fish", "gpt_sovits"] = Field(
        default="edge",
        alias="TTS_METHOD"
    )

    # Edge TTS
    edge_tts_voice: str = Field(default="zh-CN-XiaoxiaoNeural", alias="EDGE_TTS_VOICE")

    # Azure TTS
    azure_tts_api_key: str = Field(default="", alias="AZURE_TTS_API_KEY")
    azure_tts_voice: str = Field(default="zh-CN-XiaoxiaoNeural", alias="AZURE_TTS_VOICE")

    # OpenAI TTS
    openai_tts_api_key: str = Field(default="", alias="OPENAI_TTS_API_KEY")
    openai_tts_voice: str = Field(default="alloy", alias="OPENAI_TTS_VOICE")

    # Fish TTS
    fish_tts_api_key: str = Field(default="", alias="FISH_TTS_API_KEY")
    sf_fish_tts_api_key: str = Field(default="", alias="SF_FISH_TTS_API_KEY")

    # GPT-SoVITS
    sf_cosyvoice2_api_key: str = Field(default="", alias="SF_COSYVOICE2_API_KEY")
    f5tts_302_api_key: str = Field(default="", alias="F5TTS_302_API_KEY")

    # 配音速度配置
    speed_factor_min: float = Field(default=0.8, alias="SPEED_FACTOR_MIN")
    speed_factor_accept: float = Field(default=1.0, alias="SPEED_FACTOR_ACCEPT")
    speed_factor_max: float = Field(default=1.2, alias="SPEED_FACTOR_MAX")

    # ========================================================================
    # ASR 配置
    # ========================================================================
    whisper_runtime: Literal["local", "api", "elevenlabs"] = Field(
        default="local",
        alias="WHISPER_RUNTIME"
    )
    whisper_model: str = Field(default="large-v3", alias="WHISPER_MODEL")
    whisper_language: str = Field(default="zh", alias="WHISPER_LANGUAGE")
    whisper_model_dir: str = Field(default="", alias="WHISPER_MODEL_DIR")
    whisper_zh_model: str = Field(default="", alias="WHISPER_ZH_MODEL")
    wav2vec2_model: str = Field(default="", alias="WAV2VEC2_MODEL")

    # WhisperX API
    whisperx_302_api_key: str = Field(default="", alias="WHISPERX_302_API_KEY")

    # ElevenLabs ASR
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")

    # ========================================================================
    # 高级配置
    # ========================================================================
    max_workers: int = Field(default=10, alias="MAX_WORKERS")
    max_split_length: int = Field(default=20, alias="MAX_SPLIT_LENGTH")
    summary_length: int = Field(default=8000, alias="SUMMARY_LENGTH")
    reflect_translate: bool = Field(default=False, alias="REFLECT_TRANSLATE")
    pause_before_translate: bool = Field(default=False, alias="PAUSE_BEFORE_TRANSLATE")
    demucs: bool = Field(default=True, alias="DEMUCS")
    ffmpeg_gpu: bool = Field(default=True, alias="FFMPEG_GPU")

    # ========================================================================
    # 语言配置
    # ========================================================================
    target_language: str = Field(default="en", alias="TARGET_LANGUAGE")

    # Spacy 模型映射
    spacy_model_map: dict = Field(
        default={
            "en": "en_core_web_md",
            "ru": "ru_core_news_md",
            "fr": "fr_core_news_md",
            "ja": "ja_core_news_md",
            "es": "es_core_news_md",
            "de": "de_core_news_md",
            "it": "it_core_news_md",
        }
    )

    # 语言分割配置
    language_split_with_space: list[str] = Field(
        default=["en", "es", "fr", "de", "it", "ru"]
    )
    language_split_without_space: list[str] = Field(
        default=["zh", "ja"]
    )

    # 中文停用词文件
    chinese_stopwords_file: str = Field(
        default="files/chinese_stopwords.txt",
        alias="CHINESE_STOPWORDS_FILE"
    )

    # ========================================================================
    # Pydantic 配置
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=None if getenv("DOTENV_DISABLED") else str(env_file),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 将相对路径转换为绝对路径
        if not Path(self.model_cache_dir).is_absolute():
            self.model_cache_dir = str(Path.cwd() / self.model_cache_dir)
        if not Path(self.output_dir).is_absolute():
            self.output_dir = str(Path.cwd() / self.output_dir)
        if not Path(self.temp_dir).is_absolute():
            self.temp_dir = str(Path.cwd() / self.temp_dir)


@lru_cache
def get_settings() -> Settings:
    """获取缓存的配置实例（单例模式）。"""
    return Settings()


# 导出全局配置实例（向后兼容）
settings = get_settings()
