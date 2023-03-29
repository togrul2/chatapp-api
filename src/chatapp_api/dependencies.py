"""Module with FastAPI dependencies."""
from collections.abc import AsyncIterator
from typing import cast

from broadcaster import Broadcast  # type: ignore
from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.config import (
    PAGE_SIZE_DEFAULT,
    STATIC_DOMAIN,
    STATIC_ROOT,
    STATIC_URL,
    settings,
)
from src.chatapp_api.db import async_session
from src.chatapp_api.paginator import LimitOffsetPaginator
from src.chatapp_api.staticfiles import (
    BaseStaticFilesManager,
    LocalStaticFilesManager,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Returns db session for FastAPI dependency injection."""
    db_session = cast(AsyncSession, async_session())
    try:
        yield db_session
    finally:
        await db_session.close()


def get_staticfiles_manager() -> BaseStaticFilesManager:
    """Dependency for staticfiles manager."""
    return LocalStaticFilesManager(STATIC_DOMAIN, STATIC_URL, STATIC_ROOT)


async def get_broadcaster() -> AsyncIterator[Broadcast]:
    """Dependency for broadcaster."""
    broadcast = Broadcast(settings.messaging_url)
    await broadcast.connect()
    yield broadcast
    await broadcast.disconnect()


def get_paginator(
    request: Request,
    page: int = Query(default=1),
    page_size: int = Query(default=PAGE_SIZE_DEFAULT),
    session: AsyncSession = Depends(get_db_session),
):
    """Returns pagination with page and page size query params."""
    return LimitOffsetPaginator(session, page, page_size, request)
