"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path:
    """Find .env file by searching upward from current directory."""
    current = Path.cwd()
    while current != current.parent:
        env_file = current / ".env"
        if env_file.exists():
            return env_file
        current = current.parent
    return Path(".env")


# Load .env file explicitly (pydantic-settings loads it automatically, but this ensures visibility)
env_file = _find_env_file()
load_dotenv(env_file, override=False)


class Settings(BaseSettings):
    """Application settings using pydantic-settings."""

    # OpenAI / LLM Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, alias="OPENAI_MAX_TOKENS")

    # TTS Configuration
    tts_method: Literal["edge", "azure", "openai", "fish", "gpt_sovits"] = Field(default="edge", alias="TTS_METHOD")
    edge_tts_voice: str = Field(default="zh-CN-XiaoxiaoNeural", alias="EDGE_TTS_VOICE")

    # ASR Configuration
    whisper_runtime: Literal["local", "api", "elevenlabs"] = Field(default="local", alias="WHISPER_RUNTIME")
    whisper_model: str = Field(default="large-v3", alias="WHISPER_MODEL")

    model_config = SettingsConfigDict(
        env_file=str(env_file),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance for backward compatibility
settings = get_settings()
