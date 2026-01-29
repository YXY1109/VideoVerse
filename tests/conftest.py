"""Shared pytest fixtures for VideoVerse tests."""
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.config import Settings
from core.pipeline.context import PipelineContext


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Test data directory."""
    test_dir = project_root / "tests" / "fixtures"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def test_settings() -> Settings:
    """Test environment configuration."""
    return Settings(
        openai_api_key="test_key",
        openai_api_base="http://mock.openai.com/v1",
        openai_model="gpt-4o",
        model_cache_dir="tests/fixtures/models",
        output_dir="tests/fixtures/output",
        whisper_runtime="local",
        tts_method="edge",
        disable_auto_download=True,
    )


@pytest.fixture
def pipeline_context(test_settings: Settings) -> PipelineContext:
    """Pipeline execution context."""
    from core.pipeline.context import PipelineContext
    return PipelineContext(
        video_source="tests/fixtures/video/demo.mp4",
        source_language="zh",
        target_language="en",
        config=test_settings,
        storage={},
    )


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    mock = AsyncMock()
    mock.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mock response"))]
        )
    )
    return mock
