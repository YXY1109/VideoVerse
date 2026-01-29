"""Pipeline context for passing data between steps."""
from dataclasses import dataclass, field
from typing import Any, Dict
from core.config import Settings


@dataclass
class PipelineContext:
    """Context passed between pipeline steps."""

    video_source: str
    source_language: str
    target_language: str
    config: Settings
    storage: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from storage."""
        return self.storage.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value in storage."""
        self.storage[key] = value

    def has(self, key: str) -> bool:
        """Check if key exists in storage."""
        return key in self.storage
