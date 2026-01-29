"""Pipeline execution engine."""
from typing import Any

from loguru import logger

from core.config import Settings, get_settings
from core.pipeline.context import PipelineContext
from core.pipeline.registry import StepRegistry


class PipelineEngine:
    """Orchestrates the execution of pipeline steps."""

    def __init__(self, registry: StepRegistry):
        self.registry = registry

    async def run_step(
        self,
        step_name: str,
        context: PipelineContext,
    ) -> Any:
        """Run a single step."""
        step = self.registry.get(step_name)

        logger.info(f"Validating step: {step_name}")
        if not await step.validate(context):
            raise ValueError(f"Step '{step_name}' validation failed")

        logger.info(f"Executing step: {step_name}")
        result = await step.execute(context)
        logger.info(f"Completed step: {step_name}")

        return result

    async def run(
        self,
        steps: list[str],
        video_source: str,
        source_language: str,
        target_language: str,
        config: Settings | None = None,
    ) -> PipelineContext:
        """
        Run multiple steps in dependency-resolved order.

        Args:
            steps: List of step names to run
            video_source: Input video source
            source_language: Source language code
            target_language: Target language code
            config: Optional settings (uses defaults if not provided)

        Returns:
            PipelineContext containing results from all steps
        """
        if config is None:
            config = get_settings()

        context = PipelineContext(
            video_source=video_source,
            source_language=source_language,
            target_language=target_language,
            config=config,
            storage={},
        )

        # Resolve execution order based on dependencies
        execution_order = self.registry.resolve_execution_order(steps)

        logger.info(f"Execution order: {' -> '.join(execution_order)}")

        # Run each step
        for step_name in execution_order:
            await self.run_step(step_name, context)

        logger.info("Pipeline execution complete")
        return context
