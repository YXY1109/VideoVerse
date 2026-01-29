"""Test configuration management."""
from core.config import Settings, get_settings


def test_model_cache_dir_from_env(monkeypatch):
    """Test MODEL_CACHE_DIR can be set from environment variable."""
    monkeypatch.setenv("MODEL_CACHE_DIR", "/custom/models")
    settings = Settings()
    assert settings.model_cache_dir == "/custom/models"


def test_default_output_dir():
    """Test default output directory."""
    settings = Settings()
    assert settings.output_dir == "output"


def test_output_dir_from_env(monkeypatch):
    """Test OUTPUT_DIR can be overridden."""
    monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
    settings = Settings()
    assert settings.output_dir == "/custom/output"


def test_disable_auto_download(monkeypatch):
    """Test DISABLE_AUTO_DOWNLOAD setting."""
    monkeypatch.setenv("DISABLE_AUTO_DOWNLOAD", "true")
    settings = Settings()
    assert settings.disable_auto_download is True


def test_settings_model_config():
    """Test Settings model configuration."""
    settings = Settings()
    assert hasattr(settings, "model_config")


def test_get_settings_singleton():
    """Test get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2
