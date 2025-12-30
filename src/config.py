"""
VideoVerse 配置管理

使用 pydantic-settings 从环境变量加载配置
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """VideoVerse 配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== API 配置 ====================
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4o", validation_alias="OPENAI_MODEL")
    openai_llm_support_json: bool = Field(default=True, validation_alias="OPENAI_LLM_SUPPORT_JSON")
    openai_max_tokens: int = Field(default=16384, validation_alias="OPENAI_MAX_TOKENS")

    # ==================== ASR 配置 ====================
    whisper_runtime: str = Field(default="local", validation_alias="WHISPER_RUNTIME")
    whisper_model: str = Field(default="large-v3", validation_alias="WHISPER_MODEL")
    whisper_language: str = Field(default="zh", validation_alias="WHISPER_LANGUAGE")
    whisperx_302_api_key: str = Field(default="", validation_alias="WHISPERX_302_API_KEY")
    elevenlabs_api_key: str = Field(default="", validation_alias="ELEVENLABS_API_KEY")

    # ==================== TTS 配置 ====================
    tts_method: str = Field(default="azure", validation_alias="TTS_METHOD")
    azure_tts_api_key: str = Field(default="", validation_alias="AZURE_TTS_API_KEY")
    azure_tts_voice: str = Field(default="zh-CN-XiaoxiaoNeural", validation_alias="AZURE_TTS_VOICE")
    openai_tts_api_key: str = Field(default="", validation_alias="OPENAI_TTS_API_KEY")
    openai_tts_voice: str = Field(default="alloy", validation_alias="OPENAI_TTS_VOICE")
    fish_tts_api_key: str = Field(default="", validation_alias="FISH_TTS_API_KEY")
    sf_fish_tts_api_key: str = Field(default="", validation_alias="SF_FISH_TTS_API_KEY")
    sf_cosyvoice2_api_key: str = Field(default="", validation_alias="SF_COSYVOICE2_API_KEY")
    f5tts_302_api_key: str = Field(default="", validation_alias="F5TTS_302_API_KEY")
    edge_tts_voice: str = Field(default="zh-CN-XiaoxiaoNeural", validation_alias="EDGE_TTS_VOICE")

    # ==================== 视频处理配置 ====================
    target_language: str = Field(default="en", validation_alias="TARGET_LANGUAGE")
    demucs: bool = Field(default=True, validation_alias="DEMUCS")
    burn_subtitles: bool = Field(default=True, validation_alias="BURN_SUBTITLES")
    youtube_resolution: str = Field(default="1080", validation_alias="YOUTUBE_RESOLUTION")
    ffmpeg_gpu: bool = Field(default=True, validation_alias="FFMPEG_GPU")

    # ==================== 字幕配置 ====================
    subtitle_max_length: int = Field(default=75, validation_alias="SUBTITLE_MAX_LENGTH")
    subtitle_target_multiplier: float = Field(default=1.2, validation_alias="SUBTITLE_TARGET_MULTIPLIER")
    min_subtitle_duration: float = Field(default=2.5, validation_alias="MIN_SUBTITLE_DURATION")
    min_trim_duration: float = Field(default=3.5, validation_alias="MIN_TRIM_DURATION")
    tolerance: float = Field(default=1.5, validation_alias="TOLERANCE")

    # ==================== 音频配置 ====================
    speed_factor_min: float = Field(default=1.0, validation_alias="SPEED_FACTOR_MIN")
    speed_factor_accept: float = Field(default=1.2, validation_alias="SPEED_FACTOR_ACCEPT")
    speed_factor_max: float = Field(default=1.4, validation_alias="SPEED_FACTOR_MAX")

    # ==================== 高级配置 ====================
    max_workers: int = Field(default=10, validation_alias="MAX_WORKERS")
    max_split_length: int = Field(default=20, validation_alias="MAX_SPLIT_LENGTH")
    summary_length: int = Field(default=8000, validation_alias="SUMMARY_LENGTH")
    reflect_translate: bool = Field(default=False, validation_alias="REFLECT_TRANSLATE")
    model_cache_dir: str = Field(default="_model_cache", validation_alias="MODEL_CACHE_DIR")
    pause_before_translate: bool = Field(default=False, validation_alias="PAUSE_BEFORE_TRANSLATE")

    # ==================== 常量配置 ====================
    # 这些是内部常量，不从环境变量读取
    allowed_video_formats: List[str] = Field(default=["mp4", "mov", "avi", "mkv", "flv", "wmv", "webm"])
    allowed_audio_formats: List[str] = Field(default=["wav", "mp3", "flac", "m4a"])
    spacy_model_map: dict = Field(default={
        "en": "en_core_web_md",
        "ru": "ru_core_news_md",
        "fr": "fr_core_news_md",
        "ja": "ja_core_news_md",
        "es": "es_core_news_md",
        "de": "de_core_news_md",
        "it": "it_core_news_md",
    })
    language_split_with_space: List[str] = Field(default=["en", "es", "fr", "de", "it", "ru"])
    language_split_without_space: List[str] = Field(default=["zh", "ja"])
    chinese_stopwords_file: str = Field(default="files/chinese_stopwords.txt")


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
