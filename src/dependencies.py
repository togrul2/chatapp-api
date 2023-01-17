"""Module with FastAPI dependencies."""
from collections.abc import Generator
from typing import cast

from fastapi import Cookie, Depends, Query, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src import config
from src.authentication import TokenType, get_user_from_token, oauth2_scheme
from src.db import async_session
from src.exceptions.chat import WebSocketBadTokenException
from src.exceptions.user import HTTPBadTokenException
from src.paginator import LimitOffsetPaginator
from src.staticfiles import BaseStaticFilesManager, LocalStaticFilesManager


async def get_db() -> Generator[AsyncSession, None, None]:
    """Returns db session for FastAPI dependency injection."""
    db_session = async_session()
    try:
        yield db_session
    finally:
        await db_session.close()


def get_staticfiles_manager() -> BaseStaticFilesManager:
    """Dependency for staticfiles"""
    return LocalStaticFilesManager(
        config.STATIC_DOMAIN, config.STATIC_URL, config.STATIC_ROOT
    )


def get_current_user_id_from_bearer(
    access_token: str = Depends(oauth2_scheme),
) -> int:
    """
    Dependency for getting logged user's id from `authorization` header.
    Returns 401 if unauthenticated.
    """
    return get_user_from_token(
        TokenType.ACCESS, HTTPBadTokenException, access_token
    )


def get_current_user_id_from_cookie(access_token: str = Cookie()) -> int:
    """
    Dependency for getting logged user's id from `access_token` cookie.
    Returns 401 if unauthenticated.
    """
    return get_user_from_token(
        TokenType.ACCESS, WebSocketBadTokenException, access_token
    )


def get_paginator(
    page: int = Query(default=1),
    page_size: int = Query(default=config.PAGE_SIZE_DEFAULT),
    session: AsyncSession = Depends(get_db),
):
    """Returns pagination with page and page size query params."""
    return LimitOffsetPaginator(session, page, page_size)


class AuthWebSocket(WebSocket):
    """Websocket with authenticated user's id attribute."""

    user_id: int


def get_auth_websocket(
    websocket: WebSocket,
    user_id: int = Depends(get_current_user_id_from_cookie),
) -> AuthWebSocket:
    """
    Dependency returns websocket with the id of the logged in user.
    Access token is taken from the `access_token` cookie.
    If no token is provided(unauthorized) handshake response returns 403"""
    websocket.user_id = user_id
    return cast(AuthWebSocket, websocket)
