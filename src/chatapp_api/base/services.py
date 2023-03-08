"""Base services module."""
from collections.abc import Mapping
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.base.models import CustomBase

T = TypeVar("T", bound=CustomBase)


async def create(
    session: AsyncSession, item: T, *, commit: bool = True, flush: bool = False
) -> T:
    """Creates and returns item."""
    session.add(item)

    if flush:
        await session.flush()

    if commit:
        await session.commit()
        await session.refresh(item)

    return item


async def update(
    session: AsyncSession,
    item: T,
    schema: Mapping[str, Any],
    *,
    commit: bool = True,
) -> T:
    """Updates and returns updated item."""
    for key, value in schema.items():
        setattr(item, key, value)

    if commit:
        await session.commit()
        await session.refresh(item)

    return item
