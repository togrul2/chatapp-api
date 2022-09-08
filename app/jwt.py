"""
JWT module with all stuff related to authentication via jwt.
"""
from datetime import datetime, timedelta
from functools import partial

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from config import (SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM,
                    REFRESH_TOKEN_EXPIRE_MINUTES)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


class TokenType:
    ACCESS = 1
    REFRESH = 2


def get_hashed_password(password: str) -> str:
    """Hashes the password."""
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    """Compares raw and hashed passwords."""
    return password_context.verify(password, hashed_pass)


def _create_token(type_: int, expires_delta, user_id: int):
    """
    Base function for creating tokens with given type,
    user_id and expiration time.
    """
    expire = datetime.utcnow() + expires_delta
    to_encode = {"user_id": user_id,
                 "expire": expire.isoformat(),
                 "type": type_}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


create_access_token = partial(_create_token, TokenType.ACCESS,
                              timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
create_refresh_token = partial(_create_token, TokenType.REFRESH,
                               timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
ExpiredTokenException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Access token expired",
    headers={"WWW-Authenticate": "Bearer"},
)


def _get_user_from_token(token_type: int, token: str):
    """Base function for retrieving user's id from token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expire = datetime.fromisoformat(payload.get("expire"))
        type_ = payload.get("type")

        if type_ != token_type:
            raise CredentialsException

        if expire > datetime.utcnow():
            user_id = payload.get("user_id")
            return user_id
        else:
            raise ExpiredTokenException
    except JWTError:
        raise CredentialsException


async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    return _get_user_from_token(TokenType.ACCESS, token)


verify_refresh = partial(_get_user_from_token, TokenType.REFRESH)
