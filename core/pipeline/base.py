"""Base class for pipeline steps."""
from abc import ABC, abstractmethod
from typing import Any

from core.pipeline.context import PipelineContext


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique step name."""
        pass

    @property
    def dependencies(self) -> list[str]:
        """List of step names this step depends on."""
        return []

    @abstractmethod
    async def execute(self, context: PipelineContext) -> Any:
        """Execute the step logic."""
        pass

    async def validate(self, context: PipelineContext) -> bool:
        """Validate preconditions before execution."""
        return True
