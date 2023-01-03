"""
Authentication module with all stuff related to authentication via jwt.
"""
from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    settings,
)
from exceptions.user import HTTPBadTokenException

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


class TokenType(IntEnum):
    """Enum class with authentication token types"""

    ACCESS = 1
    REFRESH = 2


def get_hashed_password(password: str) -> str:
    """Hashes the password."""
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    """Compares raw and hashed passwords."""
    return password_context.verify(password, hashed_pass)


def _create_token(type_: int, expires_delta: timedelta, user_id: int) -> str:
    """
    Base function for creating tokens with given type,
    user_id and expiration time.
    """
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "user_id": user_id,
        "expire": expire.isoformat(),
        "type": type_,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=ALGORITHM
    )
    return encoded_jwt


create_access_token = partial(
    _create_token,
    TokenType.ACCESS,
    timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
)
create_refresh_token = partial(
    _create_token,
    TokenType.REFRESH,
    timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
)


def get_user_from_token(
    token_type: int, exception: BaseException, token: str
) -> int:
    """Base function for retrieving user's id from token.
    Raises given exception if token is incorrect or expired."""
    try:
        payload: dict[str, str] = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM]
        )
        curr_date = payload.get("expire")
        type_ = payload.get("type")
        user_id = payload.get("user_id")

        if (
            not curr_date
            or datetime.fromisoformat(curr_date) <= datetime.utcnow()
            or type_ != token_type
            or not user_id
        ):
            # FIXME: think of better handling
            raise exception

        return int(user_id)

    except JWTError as exc:
        raise exception from exc


verify_refresh_token = partial(
    get_user_from_token, TokenType.REFRESH, HTTPBadTokenException
)
