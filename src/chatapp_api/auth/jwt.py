from datetime import datetime, timedelta
from enum import Enum

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from src.chatapp_api.auth.utils import OAuth2PasswordBearerWithCookie
from src.chatapp_api.config import (
    JWT_ACCESS_TOKEN_EXPIRE,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRE,
    settings,
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")  # nosec: B106

oauth2_cookie_scheme = OAuth2PasswordBearerWithCookie(  # nosec: B106
    token_url="api/token"
)


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
    encoded_jwt = jwt.encode(
        payload, settings.secret_key, algorithm=JWT_ALGORITHM
    )
    return encoded_jwt


def create_access_token(user_id: int) -> str:
    """Creates access token for given user id."""
    return _create_auth_token(
        AuthTokenTypes.ACCESS,
        timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRE),
        user_id,
    )


def create_refresh_token(user_id: int) -> str:
    """Creates refresh token for given user id."""
    return _create_auth_token(
        AuthTokenTypes.REFRESH,
        timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRE),
        user_id,
    )


def generate_auth_tokens(user_id: int) -> dict[str, str]:
    """Generates access and refresh tokens for user with given id."""
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
    }
