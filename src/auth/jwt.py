from datetime import datetime, timedelta
from enum import Enum
from typing import TypedDict

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from src.auth.utils import OAuth2PasswordBearerWithCookie
from src.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    settings,
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")
oauth2_cookie_scheme = OAuth2PasswordBearerWithCookie(token_url="api/token")


class AuthTokens(TypedDict):
    """Typed dict for access and refresh tokens."""

    access_token: str
    refresh_token: str


class AuthTokenTypes(str, Enum):
    """Enum class with authentication token types"""

    ACCESS = "auth-access"
    REFRESH = "aut-refresh"


def _create_auth_token(
    type_: AuthTokenTypes, expires_delta: timedelta, user_id: int
) -> str:
    """
    Base function for creating authentication tokens
    (either access or refresh), for given user_id and expiration time.
    """
    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "expire": expire.isoformat(),
        "type": type_,
    }
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(user_id: int) -> str:
    """Creates access token for given user id."""
    return _create_auth_token(
        AuthTokenTypes.ACCESS,
        timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES),
        user_id,
    )


def create_refresh_token(user_id: int) -> str:
    """Creates refresh token for given user id."""
    return _create_auth_token(
        AuthTokenTypes.REFRESH,
        timedelta(seconds=REFRESH_TOKEN_EXPIRE_MINUTES),
        user_id,
    )


def generate_auth_tokens(user_id: int) -> AuthTokens:
    """Generates access and refresh tokens for user with given id."""
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
    }
