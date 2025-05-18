from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from chatapp_api_hex.domain.entities.base import Entity

T = TypeVar("T", bound=Entity)


class Repository(Generic[T], ABC):
    """Base repository interface for all domain entities."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> None:
        """Delete an entity."""
        pass
