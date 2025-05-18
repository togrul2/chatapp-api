from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for all value objects."""

    def __eq__(self, other: Any) -> bool:
        """Compare value objects for equality."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Generate hash for value object."""
        return hash(tuple(sorted(self.__dict__.items())))
