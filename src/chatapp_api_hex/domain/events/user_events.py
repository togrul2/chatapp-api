from dataclasses import dataclass
from typing import Any, Dict, Optional

from chatapp_api_hex.domain.events.base import DomainEvent


@dataclass
class UserCreated(DomainEvent):
    """Event raised when a new user is created."""

    def __init__(self, user_id: Optional[int], username: str, email: str):
        event_data: Dict[str, Any] = {
            "user_id": user_id,
            "username": username,
            "email": email,
        }
        super().__init__(
            event_id="",
            event_type="UserCreated",
            event_data=event_data,
        )
