from abc import ABC, abstractmethod


class Repository[T](ABC):
    """Base repository interface for all domain entities."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> T | None:
        """Get entity by ID."""

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""

    @abstractmethod
    async def delete(self, entity_id: int) -> None:
        """Delete an entity."""
