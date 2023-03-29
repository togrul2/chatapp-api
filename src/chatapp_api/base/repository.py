"""Module with base repository and related stuff."""
from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.base.models import CustomBase

T = TypeVar("T", bound=CustomBase)


@dataclass
class BaseRepository(ABC, Generic[T]):
    """Base db repository for models."""

    session: AsyncSession

    def add(self, item: T) -> None:
        """Adds given item into database session."""
        self.session.add(item)

    def add_all(self, items: Iterable[T]) -> None:
        """Adds given items into database session."""
        self.session.add_all(items)

    async def delete(self, item: T) -> None:
        """Removes given item into database session."""
        await self.session.delete(item)

    async def flush(self) -> None:
        """Flushes changes to the database session."""
        await self.session.flush()

    async def refresh(self, item: T) -> None:
        """Commits changes to the database session."""
        await self.session.refresh(item)

    async def commit(self) -> None:
        """Commits changes to the database session."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollbacks changes in the database session."""
        await self.session.rollback()
