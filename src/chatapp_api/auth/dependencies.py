"""Module with auth related dependencies."""
from fastapi import Cookie, Depends
from jose import JWTError

from src.chatapp_api.auth.exceptions import (
    BadTokenException,
    WebSocketBadTokenException,
)
from src.chatapp_api.auth.jwt import AuthTokenTypes, oauth2_scheme
from src.chatapp_api.auth.service import AuthService
from src.chatapp_api.user.dependencies import get_user_service
from src.chatapp_api.user.service import UserService


def get_auth_service(user_service: UserService = Depends(get_user_service)):
    """Dependency for auth service."""
    return AuthService(user_service)


def get_current_user_id_from_bearer(
    access_token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> int:
    """
    Dependency for getting logged user's id from `Authorization` header.
    Returns 401 if unauthenticated.
    """
    try:
        return auth_service.get_user_id_from_token(
            AuthTokenTypes.ACCESS, access_token
        )
    except JWTError as exc:
        raise BadTokenException from exc


def get_current_user_id_from_cookie_websocket(
    access_token: str = Cookie(alias="Authorization"),
    auth_service: AuthService = Depends(get_auth_service),
) -> int:
    """
    Websocket dependency for getting logged user's id
    from `Authorization` cookie. Returns 403 if unauthenticated.
    """
    try:
        bearer, token = access_token.split()

        if bearer.lower() != "bearer":
            raise WebSocketBadTokenException

        return auth_service.get_user_id_from_token(
            AuthTokenTypes.ACCESS, token
        )
    except JWTError as exc:
        raise WebSocketBadTokenException from exc
