"""Test PipelineStep base class."""
import pytest

from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext


class DummyStep(PipelineStep):
    """Test step implementation."""

    @property
    def name(self) -> str:
        return "dummy_step"

    async def execute(self, context: PipelineContext):
        return "executed"


@pytest.mark.asyncio
async def test_step_name():
    """Test step has a name."""
    step = DummyStep()
    assert step.name == "dummy_step"


@pytest.mark.asyncio
async def test_step_execute(pipeline_context):
    """Test step execution."""
    step = DummyStep()
    result = await step.execute(pipeline_context)
    assert result == "executed"


@pytest.mark.asyncio
async def test_step_dependencies_default():
    """Test default dependencies is empty list."""
    step = DummyStep()
    assert step.dependencies == []


@pytest.mark.asyncio
async def test_step_validate_default(pipeline_context):
    """Test default validation returns True."""
    step = DummyStep()
    assert await step.validate(pipeline_context) is True


class StepWithDeps(DummyStep):
    """Step with dependencies."""

    @property
    def dependencies(self):
        return ["step_01", "step_02"]


def test_step_with_dependencies():
    """Test step can declare dependencies."""
    step = StepWithDeps()
    assert step.dependencies == ["step_01", "step_02"]
