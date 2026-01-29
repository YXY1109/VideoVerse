"""Test ASR step functionality."""
from unittest.mock import MagicMock, patch

import pytest

from core.steps.step_02_asr import ASRStep


@pytest.mark.asyncio
async def test_asr_step_name():
    """Test ASR step has correct name."""
    step = ASRStep()
    assert step.name == "step_02_asr"


@pytest.mark.asyncio
async def test_asr_step_dependencies():
    """Test ASR step dependencies."""
    step = ASRStep()
    assert "step_01_download" in step.dependencies


@pytest.mark.asyncio
async def test_asr_step_validate():
    """Test ASR step validation."""
    step = ASRStep()
    context = MagicMock()
    context.storage = {"video_path": "test.mp4"}

    with patch("pathlib.Path.exists", return_value=True):
        result = await step.validate(context)
        assert result is True


@pytest.mark.asyncio
async def test_asr_step_validate_missing_video():
    """Test ASR step validation with missing video."""
    step = ASRStep()
    context = MagicMock()
    context.storage = {}

    result = await step.validate(context)
    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asr_step_step_structure():
    """Test ASR step has correct structure for plugin."""
    step = ASRStep(use_demucs=False)

    # Verify it's a proper PipelineStep
    from core.pipeline.base import PipelineStep
    assert isinstance(step, PipelineStep)
    assert hasattr(step, 'name')
    assert hasattr(step, 'dependencies')
    assert hasattr(step, 'validate')
    assert hasattr(step, 'execute')
