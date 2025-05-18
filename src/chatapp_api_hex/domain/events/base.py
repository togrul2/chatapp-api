from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_data: dict[str, Any]
    event_id: str
    occurred_on: datetime | None = None
    event_type: str | None = None

    def __post_init__(self) -> None:
        """Initialize event ID and timestamp if not provided."""
        if not self.event_id:
            self.event_id = str(uuid4())
        if not self.occurred_on:
            self.occurred_on = datetime.now(timezone.utc)
        if not self.event_type:
            self.event_type = self.__class__.__name__
