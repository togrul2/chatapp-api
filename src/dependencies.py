"""Module with FastAPI dependencies."""
from functools import partial
from typing import Callable, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from authentication import TokenType, get_user_from_token, oauth2_scheme
from config import STATIC_DOMAIN, STATIC_ROOT, STATIC_URL
from db import SessionLocal
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


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Dependency for getting logged user's id.
    Returns 401 if unauthenticated.
    """
    return get_user_from_token(TokenType.ACCESS, token)


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


# Dependencies for services, should be used with Depends().
get_user_service = partial(get_service, UserService)
get_friendship_service = partial(get_service, FriendshipService)
get_chat_service = partial(get_service, ChatService)
