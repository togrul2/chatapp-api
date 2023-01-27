"""Module with FastAPI dependencies."""
from collections.abc import AsyncIterator

from fastapi import Cookie, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.authentication import (
    AuthTokens,
    get_user_id_from_token,
    oauth2_scheme,
)
from src.config import (
    PAGE_SIZE_DEFAULT,
    STATIC_DOMAIN,
    STATIC_ROOT,
    STATIC_URL,
)
from src.db import async_session
from src.exceptions.chat import WebSocketBadTokenException
from src.exceptions.user import HTTPBadTokenException
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


def get_current_user_id_from_bearer(
    access_token: str = Depends(oauth2_scheme),
) -> int:
    """
    Dependency for getting logged user's id from `Authorization` header.
    Returns 401 if unauthenticated.
    """
    user_id, err = get_user_id_from_token(AuthTokens.ACCESS, access_token)

    if err:
        raise HTTPBadTokenException

    return user_id


def get_current_user_id_from_cookie(access_token: str = Cookie()) -> int:
    """
    Dependency for getting logged user's id from `access_token` cookie.
    Returns 401 if unauthenticated.
    """
    user_id, err = get_user_id_from_token(AuthTokens.ACCESS, access_token)

    if err:
        raise WebSocketBadTokenException

    return user_id


def get_paginator(
    request: Request,
    page: int = Query(default=1),
    page_size: int = Query(default=PAGE_SIZE_DEFAULT),
    session: AsyncSession = Depends(get_db),
):
    """Returns pagination with page and page size query params."""
    return LimitOffsetPaginator(session, page, page_size, request)
