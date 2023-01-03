"""Module with FastAPI dependencies."""
from collections.abc import Callable, Generator
from functools import partial

from fastapi import Cookie, Depends, WebSocket
from sqlalchemy.orm import Session

from authentication import TokenType, get_user_from_token, oauth2_scheme
from config import STATIC_DOMAIN, STATIC_ROOT, STATIC_URL
from db import SessionLocal
from exceptions.chat import WebSocketBadTokenException
from exceptions.user import HTTPBadTokenException
from services.base import BaseService
from services.chat import ChatService
from services.friendship import FriendshipService
from services.user import UserService
from staticfiles import BaseStaticFilesManager, LocalStaticFilesManager


def get_db() -> Generator[Session, None, None]:
    """Returns db session for FastAPI dependency injection."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_staticfiles_manager() -> BaseStaticFilesManager:
    """Dependency for staticfiles"""
    return LocalStaticFilesManager(STATIC_DOMAIN, STATIC_URL, STATIC_ROOT)


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


def get_service(
    service: Callable[[Session], BaseService],
    db_session: Session = Depends(get_db),
) -> Generator[BaseService, None, None]:
    """
    Base function for creating service dependency
    for using with fastapi dependency injection tool.
    Services give us a class with crud operations etc.
    with established db connection and settings.
    """
    yield service(db_session)


def get_auth_websocket(
    websocket: WebSocket,
    user_id: int = Depends(get_current_user_id_from_cookie),
) -> WebSocket:
    """
    Dependency returns websocket with the id of the logged in user.
    Access token is taken from the `access_token` cookie.
    If no token is provided(unauthorized) handshake response returns 403"""
    websocket.user_id = user_id
    return websocket


# Dependencies for services, should be used with Depends().
get_user_service = partial(get_service, UserService)
get_friendship_service = partial(get_service, FriendshipService)
get_chat_service = partial(get_service, ChatService)
