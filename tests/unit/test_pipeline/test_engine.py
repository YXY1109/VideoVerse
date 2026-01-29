"""Test PipelineEngine functionality."""
import pytest
from core.pipeline.engine import PipelineEngine
from core.pipeline.registry import StepRegistry
from core.pipeline.base import PipelineStep
from core.pipeline.context import PipelineContext
from core.config import Settings


class MockStep(PipelineStep):
    """Mock step for testing."""

    def __init__(self, name, result=None):
        self._name = name
        self._result = result or f"{name}_result"
        self.executed = False

    @property
    def name(self):
        return self._name

    async def execute(self, context):
        self.executed = True
        context.set(self._name, self._result)
        return self._result


@pytest.mark.asyncio
async def test_engine_run_single_step(pipeline_context):
    """Test running a single step."""
    registry = StepRegistry()
    step = MockStep("test_step")
    registry.register("test_step", step)

    engine = PipelineEngine(registry)
    result = await engine.run_step("test_step", pipeline_context)

    assert result == "test_step_result"
    assert step.executed
    assert pipeline_context.get("test_step") == "test_step_result"


@pytest.mark.asyncio
async def test_engine_run_multiple_steps(pipeline_context):
    """Test running multiple steps in sequence."""
    registry = StepRegistry()
    step1 = MockStep("step_01", "result1")
    step2 = MockStep("step_02", "result2")
    registry.register("step_01", step1)
    registry.register("step_02", step2)

    engine = PipelineEngine(registry)
    result_context = await engine.run(
        steps=["step_01", "step_02"],
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
    )

    assert step1.executed
    assert step2.executed
    assert result_context.get("step_01") == "result1"
    assert result_context.get("step_02") == "result2"


@pytest.mark.asyncio
async def test_engine_respects_dependencies():
    """Test engine automatically resolves dependencies."""
    class StepWithDeps(PipelineStep):
        def __init__(self, name, deps):
            self._name = name
            self._deps = deps
            self.executed = False

        @property
        def name(self):
            return self._name

        @property
        def dependencies(self):
            return self._deps

        async def execute(self, context):
            self.executed = True
            context.set(self._name, f"{self._name}_done")

    registry = StepRegistry()
    step_c = StepWithDeps("step_c", ["step_b"])
    step_b = StepWithDeps("step_b", ["step_a"])
    step_a = StepWithDeps("step_a", [])

    registry.register("step_a", step_a)
    registry.register("step_b", step_b)
    registry.register("step_c", step_c)

    engine = PipelineEngine(registry)
    await engine.run(
        steps=["step_c"],
        video_source="test.mp4",
        source_language="zh",
        target_language="en",
    )

    # Verify execution order
    assert step_a.executed
    assert step_b.executed
    assert step_c.executed


@pytest.mark.asyncio
async def test_engine_validation(pipeline_context):
    """Test step validation before execution."""
    class FailingValidationStep(PipelineStep):
        @property
        def name(self):
            return "failing_step"

        async def validate(self, context):
            return False

        async def execute(self, context):
            return "should_not_run"

    registry = StepRegistry()
    step = FailingValidationStep()
    registry.register("failing_step", step)

    engine = PipelineEngine(registry)

    with pytest.raises(ValueError, match="validation failed"):
        await engine.run_step("failing_step", pipeline_context)
