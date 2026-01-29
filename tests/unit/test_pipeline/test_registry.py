"""Test StepRegistry functionality."""
import pytest

from core.pipeline.base import PipelineStep
from core.pipeline.registry import StepRegistry


class TestStep1(PipelineStep):
    @property
    def name(self):
        return "step_01"

    async def execute(self, context):
        return "step1_result"


class TestStep2(PipelineStep):
    @property
    def name(self):
        return "step_02"

    @property
    def dependencies(self):
        return ["step_01"]

    async def execute(self, context):
        return "step2_result"


def test_register_step():
    """Test registering a step."""
    registry = StepRegistry()
    step = TestStep1()
    registry.register("step_01", step)
    assert "step_01" in registry.list_steps()


def test_get_step():
    """Test retrieving registered step."""
    registry = StepRegistry()
    step = TestStep1()
    registry.register("step_01", step)
    retrieved = registry.get("step_01")
    assert retrieved is step


def test_get_nonexistent_step():
    """Test getting nonexistent step raises error."""
    registry = StepRegistry()
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_list_steps():
    """Test listing all registered steps."""
    registry = StepRegistry()
    step1 = TestStep1()
    step2 = TestStep2()
    registry.register("step_01", step1)
    registry.register("step_02", step2)
    steps = registry.list_steps()
    assert set(steps) == {"step_01", "step_02"}


def test_resolve_execution_order():
    """Test resolving step execution order based on dependencies."""
    registry = StepRegistry()
    step1 = TestStep1()
    step2 = TestStep2()
    registry.register("step_01", step1)
    registry.register("step_02", step2)

    order = registry.resolve_execution_order(["step_02"])
    assert order == ["step_01", "step_02"]


def test_resolve_circular_dependencies():
    """Test circular dependency detection."""
    class CircularA(PipelineStep):
        @property
        def name(self):
            return "a"

        @property
        def dependencies(self):
            return ["b"]

        async def execute(self, context):
            pass

    class CircularB(PipelineStep):
        @property
        def name(self):
            return "b"

        @property
        def dependencies(self):
            return ["a"]

        async def execute(self, context):
            pass

    registry = StepRegistry()
    registry.register("a", CircularA())
    registry.register("b", CircularB())

    with pytest.raises(ValueError, match="Circular"):
        registry.resolve_execution_order(["a", "b"])
