from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from chatapp_api_hex.domain.ports.repositories.user_repository import (
    UserRepository,
)


class UnitOfWork(ABC):
    """Unit of Work interface defining transaction boundaries."""

    user_repository: UserRepository

    async def __aenter__(self) -> Self:
        """Enter the transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the transaction context and handle commit/rollback."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
