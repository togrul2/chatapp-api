from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from chatapp_api_hex.domain.events.base import DomainEvent


@dataclass
class UserCreated(DomainEvent):
    """Event raised when a new user is created."""

    def __init__(self, user_id: int | None, username: str, email: str):
        event_data: dict[str, Any] = {
            "user_id": user_id,
            "username": username,
            "email": email,
        }
        super().__init__(
            event_type="UserCreated",
            event_data=event_data,
        )
