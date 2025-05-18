from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from chatapp_api_hex.domain.entities.base import Entity
from chatapp_api_hex.domain.value_objects.email import Email


@dataclass
class User(Entity):
    """User entity representing a user in the domain."""

    username: str
    email: Email
    password: str  # Note: This should be hashed before storage
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
    ) -> None:
        """Update user profile information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if profile_picture is not None:
            self.profile_picture = profile_picture
        self.updated_at = datetime.now(timezone.utc)
