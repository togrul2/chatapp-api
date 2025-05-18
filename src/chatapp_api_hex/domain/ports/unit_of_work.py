from abc import ABC, abstractmethod

from chatapp_api_hex.domain.ports.repositories.user_repository import (
    UserRepository,
)


class UnitOfWork(ABC):
    """Unit of Work interface defining transaction boundaries."""

    user_repository: UserRepository

    async def __aenter__(self):
        """Enter the transaction context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the transaction context and handle commit/rollback."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    @abstractmethod
    async def commit(self):
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction."""
        pass
