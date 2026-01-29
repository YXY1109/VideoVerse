"""Test PipelineContext functionality."""
from core.config import Settings
from core.pipeline.context import PipelineContext


def test_context_creation():
    """Test creating pipeline context."""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    assert context.video_source == "test.mp4"
    assert context.source_language == "zh"
    assert context.target_language == "en"
    assert context.storage == {}


def test_context_storage():
    """Test storing and retrieving data in context."""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    context.storage["test_key"] = "test_value"
    assert context.storage["test_key"] == "test_value"


def test_context_get():
    """Test get method."""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    context.set("key1", "value1")
    assert context.get("key1") == "value1"
    assert context.get("nonexistent") is None
    assert context.get("nonexistent", "default") == "default"


def test_context_has():
    """Test has method."""
    settings = Settings()
    context = PipelineContext(
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
        config=settings,
        storage={},
    )
    assert context.has("key1") is False
    context.set("key1", "value1")
    assert context.has("key1") is True
