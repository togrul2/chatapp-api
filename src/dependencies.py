"""Module with FastAPI dependencies."""
from collections.abc import AsyncIterator

from fastapi import Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import (
    PAGE_SIZE_DEFAULT,
    STATIC_DOMAIN,
    STATIC_ROOT,
    STATIC_URL,
)
from src.db import async_session
from src.paginator import LimitOffsetPaginator
from src.staticfiles import BaseStaticFilesManager, LocalStaticFilesManager


async def get_db() -> AsyncIterator[AsyncSession]:
    """Returns db session for FastAPI dependency injection."""
    db_session = async_session()
    try:
        yield db_session
    finally:
        await db_session.close()


def get_staticfiles_manager() -> BaseStaticFilesManager:
    """Dependency for staticfiles"""
    return LocalStaticFilesManager(STATIC_DOMAIN, STATIC_URL, STATIC_ROOT)


def get_paginator(
    request: Request,
    page: int | None = Query(default=1),
    page_size: int | None = Query(default=PAGE_SIZE_DEFAULT),
    session: AsyncSession = Depends(get_db),
):
    """Returns pagination with page and page size query params."""
    return LimitOffsetPaginator(session, page, page_size, request)
