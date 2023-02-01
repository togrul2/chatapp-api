"""
Authentication module with all stuff related to authentication via jwt.
"""
from datetime import datetime
from typing import cast

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import BadTokenException
from src.auth.jwt import (
    AuthTokens,
    AuthTokenTypes,
    generate_auth_tokens,
    password_context,
)
from src.config import ALGORITHM, settings
from src.user.exceptions import BadCredentialsException
from src.user.services import get_by_username, get_or_401


def get_user_id_from_token(token_type: AuthTokenTypes, token: str) -> int:
    """Base function for retrieving user's id from token.
    Raises JWTError if token is incorrect or expired."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

    user_id = payload.get("user_id")

    if (
        not (curr_date := payload.get("expire"))
        or datetime.fromisoformat(curr_date) <= datetime.utcnow()
        or payload.get("type") != token_type
        or not user_id
    ):
        raise JWTError

    return user_id


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> AuthTokens:
    """Authenticates user with given username and password.
    Returns user if credentials are correct, otherwise raises 401"""
    user = await get_by_username(session, username)

    if (
        user is None
        or password_context.verify(password, user.password) is False
    ):
        raise BadCredentialsException

    return generate_auth_tokens(cast(int, user.id))


async def refresh_tokens(
    session: AsyncSession, refresh_token: str
) -> AuthTokens:
    """Returns new access and refresh tokens if refresh token is valid."""
    try:
        user_id = get_user_id_from_token(AuthTokenTypes.REFRESH, refresh_token)
        await get_or_401(session, user_id)
        return generate_auth_tokens(user_id)
    except JWTError:
        raise BadTokenException
