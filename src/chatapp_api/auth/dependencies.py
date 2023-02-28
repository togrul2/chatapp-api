"""Module with auth related dependencies."""
from fastapi import Cookie, Depends
from jose import JWTError

from src.chatapp_api.auth.exceptions import (
    BadTokenException,
    WebSocketBadTokenException,
)
from src.chatapp_api.auth.jwt import oauth2_scheme
from src.chatapp_api.auth.services import (
    AuthTokenTypes,
    get_user_id_from_token,
)


def get_current_user_id_from_bearer(
    access_token: str = Depends(oauth2_scheme),
) -> int:
    """
    Dependency for getting logged user's id from `Authorization` header.
    Returns 401 if unauthenticated.
    """
    try:
        return get_user_id_from_token(AuthTokenTypes.ACCESS, access_token)
    except JWTError as exc:
        raise BadTokenException from exc


def get_current_user_id_from_cookie_websocket(
    access_token: str = Cookie(alias="Authorization"),
) -> int:
    """
    Websocket dependency for getting logged user's id
    from `Authorization` cookie. Returns 403 if unauthenticated.
    """
    try:
        bearer, token = access_token.split()

        if bearer.lower() != "bearer":
            raise WebSocketBadTokenException

        return get_user_id_from_token(AuthTokenTypes.ACCESS, token)
    except JWTError as exc:
        raise WebSocketBadTokenException from exc
