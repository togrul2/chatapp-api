from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Entity:
    """Base class for all domain entities."""

    id: Optional[int]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        now = datetime.now(timezone.utc)
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
