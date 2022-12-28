"""
Authentication module with all stuff related to authentication via jwt.
"""
from datetime import datetime, timedelta
from enum import IntEnum
from functools import partial

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    settings,
)
from exceptions.user import CredentialsException, ExpiredTokenException

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


def _create_token(type_: int, expires_delta, user_id: int) -> str:
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


def _get_user_from_token(token_type: int, token: str) -> int:
    """Base function for retrieving user's id from token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM]
        )
        curr_date = str(payload.get("expire"))
        type_ = payload.get("type")

        if not curr_date:
            # FIXME: think of better handling
            raise ExpiredTokenException

        expire = datetime.fromisoformat(curr_date)

        if type_ != token_type:
            raise CredentialsException

        if expire <= datetime.utcnow():
            raise ExpiredTokenException

        user_id = payload.get("user_id")
        return user_id

    except JWTError as exc:
        raise CredentialsException from exc


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """
    Dependency for getting logged user's id.
    Returns 401 if unauthenticated.
    """
    return _get_user_from_token(TokenType.ACCESS, token)


verify_refresh_token = partial(_get_user_from_token, TokenType.REFRESH)