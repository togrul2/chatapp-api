"""
Authentication module with all stuff related to authentication via jwt.
"""
from datetime import datetime, timedelta
from enum import Enum

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    settings,
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


class AuthTokens(str, Enum):
    """Enum class with authentication token types"""

    ACCESS = "auth-access"
    REFRESH = "aut-refresh"


def _create_auth_token(
    type_: AuthTokens, expires_delta: timedelta, user_id: int
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
        AuthTokens.ACCESS,
        timedelta(seconds=ACCESS_TOKEN_EXPIRE_MINUTES),
        user_id,
    )


def create_refresh_token(user_id: int) -> str:
    """Creates refresh token for given user id."""
    return _create_auth_token(
        AuthTokens.REFRESH,
        timedelta(seconds=REFRESH_TOKEN_EXPIRE_MINUTES),
        user_id,
    )


def get_user_id_from_token(
    token_type: AuthTokens, token: str
) -> tuple[int, str]:
    """Base function for retrieving user's id from token.
    Raises given exception if token is incorrect or expired."""
    error_msg = "Given token is either invalid or expired."

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if (
            not (curr_date := payload.get("expire"))
            or datetime.fromisoformat(curr_date) <= datetime.utcnow()
            or payload.get("type") != token_type
            or not user_id
        ):
            return 0, error_msg

        return user_id, ""

    except JWTError:
        return 0, error_msg


def get_user_id_from_refresh_token(token: str):
    """Retrieves user from refresh token"""
    return get_user_id_from_token(AuthTokens.REFRESH, token)
