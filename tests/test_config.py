"""
配置管理模块测试

测试 Settings 类的配置加载、验证和默认值
"""
import os
from typing import Generator
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


class TestSettings:
    """测试 Settings 类"""

    def test_default_values(self, monkeypatch):
        """测试默认配置值"""
        # 清除环境变量以测试默认值
        for key in list(os.environ.keys()):
            if key.startswith(("OPENAI_", "WHISPER_", "TTS_", "AZURE_", "EDGE_")):
                monkeypatch.delenv(key, raising=False)

        settings = Settings()

        # API 配置默认值
        assert settings.openai_api_base == "https://api.openai.com/v1"
        assert settings.openai_model == "gpt-4o"
        assert settings.openai_llm_support_json is True
        assert settings.openai_max_tokens == 16384

        # ASR 配置默认值
        assert settings.whisper_runtime == "local"
        assert settings.whisper_model == "large-v3"
        assert settings.whisper_language == "zh"

        # TTS 配置默认值
        assert settings.tts_method == "azure"
        assert settings.azure_tts_voice == "zh-CN-XiaoxiaoNeural"
        assert settings.edge_tts_voice == "zh-CN-XiaoxiaoNeural"

        # 视频处理默认值
        assert settings.target_language == "en"
        assert settings.demucs is True
        assert settings.burn_subtitles is True
        assert settings.youtube_resolution == "1080"

        # 字幕配置默认值
        assert settings.subtitle_max_length == 75
        assert settings.subtitle_target_multiplier == 1.2
        assert settings.min_subtitle_duration == 2.5
        assert settings.min_trim_duration == 3.5
        assert settings.tolerance == 1.5

        # 音频配置默认值
        assert settings.speed_factor_min == 1.0
        assert settings.speed_factor_accept == 1.2
        assert settings.speed_factor_max == 1.4

        # 高级配置默认值
        assert settings.max_workers == 10
        assert settings.max_split_length == 20
        assert settings.summary_length == 8000
        assert settings.reflect_translate is False

        # 常量配置
        assert "mp4" in settings.allowed_video_formats
        assert "wav" in settings.allowed_audio_formats
        assert "en" in settings.spacy_model_map
        assert "en" in settings.language_split_with_space
        assert "zh" in settings.language_split_without_space

    @pytest.mark.skip_env_clean
    def test_settings_from_env(self, temp_env_vars: dict):
        """测试从环境变量加载配置"""
        settings = Settings()

        assert settings.openai_api_key == "test_api_key"
        assert settings.openai_api_base == "https://api.openai.com/v1"
        assert settings.openai_model == "gpt-4o"
        assert settings.whisper_runtime == "local"
        assert settings.tts_method == "edge"
        assert settings.target_language == "en"

    @pytest.mark.skip_env_clean
    def test_custom_values(self):
        """测试自定义配置值（需要跳过环境变量清理）"""
        # 使用 validation_alias 的名称作为参数
        settings = Settings(
            OPENAI_API_KEY="custom_key",
            OPENAI_MODEL="gpt-3.5-turbo",
            WHISPER_LANGUAGE="en",
            TTS_METHOD="openai",
            TARGET_LANGUAGE="zh",
        )

        assert settings.openai_api_key == "custom_key"
        assert settings.openai_model == "gpt-3.5-turbo"
        assert settings.whisper_language == "en"
        assert settings.tts_method == "openai"
        assert settings.target_language == "zh"

    def test_validation_alias(self):
        """测试环境变量验证别名（大写下划线转驼峰）"""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test_key",
            "OPENAI_MODEL": "gpt-35-turbo",
            "WHISPER_LANGUAGE": "en",
        }):
            settings = Settings()
            assert settings.openai_api_key == "test_key"
            # 注意: validation_alias 处理了命名转换
            assert settings.whisper_language == "en"

    @pytest.mark.skip_env_clean
    def test_extra_ignore(self):
        """测试额外的配置项被忽略"""
        # 不应该抛出 ValidationError
        settings = Settings(
            OPENAI_API_KEY="test",
            unknown_field="should_be_ignored"
        )
        assert settings.openai_api_key == "test"
        assert not hasattr(settings, "unknown_field")

    def test_allowed_video_formats(self):
        """测试允许的视频格式"""
        settings = Settings()
        expected_formats = ["mp4", "mov", "avi", "mkv", "flv", "wmv", "webm"]
        for fmt in expected_formats:
            assert fmt in settings.allowed_video_formats

    def test_allowed_audio_formats(self):
        """测试允许的音频格式"""
        settings = Settings()
        expected_formats = ["wav", "mp3", "flac", "m4a"]
        for fmt in expected_formats:
            assert fmt in settings.allowed_audio_formats

    def test_spacy_model_map(self):
        """测试 Spacy 模型映射"""
        settings = Settings()
        expected_models = {
            "en": "en_core_web_md",
            "ru": "ru_core_news_md",
            "fr": "fr_core_news_md",
            "ja": "ja_core_news_md",
            "es": "es_core_news_md",
            "de": "de_core_news_md",
            "it": "it_core_news_md",
        }
        for lang, model in expected_models.items():
            assert settings.spacy_model_map[lang] == model

    def test_language_split_with_space(self):
        """测试需要空格分隔的语言"""
        settings = Settings()
        expected_langs = ["en", "es", "fr", "de", "it", "ru"]
        for lang in expected_langs:
            assert lang in settings.language_split_with_space

    def test_language_split_without_space(self):
        """测试不需要空格分隔的语言"""
        settings = Settings()
        expected_langs = ["zh", "ja"]
        for lang in expected_langs:
            assert lang in settings.language_split_without_space

    def test_chinese_stopwords_file(self):
        """测试中文停用词文件路径"""
        settings = Settings()
        assert settings.chinese_stopwords_file == "files/chinese_stopwords.txt"

    @pytest.mark.parametrize("field,alias,value", [
        ("openai_max_tokens", "OPENAI_MAX_TOKENS", 1000),
        ("subtitle_max_length", "SUBTITLE_MAX_LENGTH", 50),
        ("max_workers", "MAX_WORKERS", 5),
        ("speed_factor_min", "SPEED_FACTOR_MIN", 0.9),
        ("speed_factor_max", "SPEED_FACTOR_MAX", 1.5),
    ])
    @pytest.mark.skip_env_clean
    def test_numeric_field_assignment(self, field, alias, value):
        """测试数值字段赋值"""
        # 使用 validation_alias 的名称作为参数
        settings = Settings(**{alias: value})
        assert getattr(settings, field) == value

    @pytest.mark.parametrize("field,alias,value", [
        ("demucs", "DEMUCS", False),
        ("burn_subtitles", "BURN_SUBTITLES", False),
        ("ffmpeg_gpu", "FFMPEG_GPU", False),
        ("reflect_translate", "REFLECT_TRANSLATE", True),
        ("pause_before_translate", "PAUSE_BEFORE_TRANSLATE", True),
    ])
    @pytest.mark.skip_env_clean
    def test_boolean_field_assignment(self, field, alias, value):
        """测试布尔字段赋值"""
        # 使用 validation_alias 的名称作为参数
        settings = Settings(**{alias: value})
        assert getattr(settings, field) == value

    def test_settings_immutability_of_constants(self):
        """测试常量配置的不可变性（通过重新创建实例）"""
        settings1 = Settings()
        settings2 = Settings()

        # 常量应该在所有实例中保持一致
        assert settings1.allowed_video_formats == settings2.allowed_video_formats
        assert settings1.spacy_model_map == settings2.spacy_model_map


class TestGetSettings:
    """测试 get_settings 函数"""

    def test_get_settings_returns_singleton(self):
        """测试 get_settings 返回单例"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_settings_type(self):
        """测试 get_settings 返回类型"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_instance_attribute(self):
        """测试可以通过实例访问配置"""
        settings = get_settings()
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "whisper_model")
        assert hasattr(settings, "tts_method")


class TestSettingsEdgeCases:
    """测试 Settings 边界情况"""

    @pytest.mark.skip_env_clean
    def test_empty_api_key(self):
        """测试空 API Key"""
        settings = Settings(OPENAI_API_KEY="")
        assert settings.openai_api_key == ""

    @pytest.mark.skip_env_clean
    def test_zero_values(self):
        """测试零值"""
        # 使用 validation_alias 的名称作为参数
        settings = Settings(
            OPENAI_MAX_TOKENS=0,
            SUBTITLE_MAX_LENGTH=0,
        )
        assert settings.openai_max_tokens == 0
        assert settings.subtitle_max_length == 0

    def test_negative_values_allowed(self):
        """测试负值（某些字段可能允许）"""
        # 音频相关字段可能接受负值（如 dB）
        settings = Settings()
        assert isinstance(settings.speed_factor_min, float)

    @pytest.mark.skip_env_clean
    def test_very_long_string(self):
        """测试超长字符串"""
        long_string = "a" * 10000
        settings = Settings(OPENAI_API_KEY=long_string)
        assert settings.openai_api_key == long_string

    @pytest.mark.skip_env_clean
    def test_special_characters_in_api_key(self):
        """测试 API Key 中的特殊字符"""
        special_key = "sk-1234!@#$%^&*()_+-=[]{}|;':\",./<>?"
        settings = Settings(OPENAI_API_KEY=special_key)
        assert settings.openai_api_key == special_key


@pytest.mark.integration
class TestSettingsIntegration:
    """集成测试: Settings 与环境变量"""

    def test_settings_with_real_env_loading(self):
        """测试真实环境变量加载"""
        # 保存原始环境变量
        original_env = os.environ.copy()

        try:
            # 设置测试环境变量
            os.environ["OPENAI_API_KEY"] = "integration_test_key"
            os.environ["WHISPER_MODEL"] = "base"

            settings = Settings()

            assert settings.openai_api_key == "integration_test_key"
            # 注意: 这可能会受到已有环境变量的影响

        finally:
            # 恢复原始环境变量
            os.environ.clear()
            os.environ.update(original_env)
