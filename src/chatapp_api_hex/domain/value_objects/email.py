import re
from dataclasses import dataclass

from chatapp_api_hex.domain.value_objects.base import ValueObject


@dataclass(frozen=True)
class Email(ValueObject):
    """Email value object with validation."""

    value: str

    def __post_init__(self) -> None:
        """Validate email format."""
        if not self._is_valid_email(self.value):
            raise ValueError("Invalid email format")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email format is valid."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        """String representation of email."""
        return self.value
