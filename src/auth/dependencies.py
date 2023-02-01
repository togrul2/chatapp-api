"""Module with auth related dependencies."""
from fastapi import Depends
from jose import JWTError

from src.auth.exceptions import BadTokenException, WebSocketBadTokenException
from src.auth.jwt import oauth2_cookie_scheme, oauth2_scheme
from src.auth.services import AuthTokenTypes, get_user_id_from_token


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


def get_current_user_id_from_cookie(
    access_token: str = Depends(oauth2_cookie_scheme),
) -> int:
    """
    Dependency for getting logged user's id from `access_token` cookie.
    Returns 401 if unauthenticated.
    """
    try:
        return get_user_id_from_token(AuthTokenTypes.ACCESS, access_token)
    except JWTError as exc:
        raise WebSocketBadTokenException from exc
