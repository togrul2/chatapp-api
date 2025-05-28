from dataclasses import dataclass

from chatapp_api_hex.domain.entities.base import Entity
from chatapp_api_hex.domain.value_objects.email import Email


@dataclass
class User(Entity):
    """User entity representing a user in the domain."""

    username: str
    email: Email
    password: str
    first_name: str | None = None
    last_name: str | None = None
    profile_picture: str | None = None

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, username={self.username}, email={self.email})"
        )
