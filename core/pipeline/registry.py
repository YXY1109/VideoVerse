"""Registry for managing pipeline steps."""

from core.pipeline.base import PipelineStep


class StepRegistry:
    """Pipeline step registry with dependency resolution."""

    def __init__(self):
        self._steps: dict[str, PipelineStep] = {}

    def register(self, name: str, step: PipelineStep) -> None:
        """Register a step."""
        self._steps[name] = step

    def get(self, name: str) -> PipelineStep:
        """Get a registered step."""
        if name not in self._steps:
            raise KeyError(f"Step '{name}' is not registered")
        return self._steps[name]

    def list_steps(self) -> list[str]:
        """List all registered step names."""
        return list(self._steps.keys())

    def resolve_execution_order(self, step_names: list[str]) -> list[str]:
        """
        Resolve execution order based on dependencies.

        Uses topological sorting to order steps by their dependencies.
        Automatically includes all transitive dependencies.
        """
        # Collect all steps including transitive dependencies
        all_steps = set(step_names)
        to_process = list(step_names)

        while to_process:
            name = to_process.pop(0)
            if name in self._steps:
                step = self.get(name)
                for dep in step.dependencies:
                    if dep not in all_steps and dep in self._steps:
                        all_steps.add(dep)
                        to_process.append(dep)

        step_names = list(all_steps)

        # Build dependency graph
        graph: dict[str, set[str]] = {name: set() for name in step_names}
        in_degree: dict[str, int] = {name: 0 for name in step_names}

        for name in step_names:
            step = self.get(name)
            for dep in step.dependencies:
                if dep in step_names:
                    graph[dep].add(name)
                    in_degree[name] += 1

        # Use DFS to detect cycles
        visiting = set()
        visited = set()

        def has_cycle(node: str) -> bool:
            if node in visiting:
                return True  # Cycle detected
            if node in visited:
                return False
            visiting.add(node)
            for neighbor in graph.get(node, set()):
                if has_cycle(neighbor):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for node in step_names:
            if has_cycle(node):
                raise ValueError(f"Circular dependency detected involving step '{node}'")

        # Topological sort (Kahn's algorithm)
        queue = [name for name in step_names if in_degree[name] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(step_names):
            raise ValueError("Could not resolve execution order - possible cycle")

        return result
