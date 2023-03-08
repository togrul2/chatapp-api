"""
Authentication module with all stuff related to authentication via jwt.
"""
from datetime import datetime

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.exceptions import BadTokenException
from src.chatapp_api.auth.jwt import (
    AuthTokenTypes,
    generate_auth_tokens,
    password_context,
)
from src.chatapp_api.auth.schemas import UserWithTokens
from src.chatapp_api.config import JWT_ALGORITHM, settings
from src.chatapp_api.user.exceptions import BadCredentialsException
from src.chatapp_api.user.services import get_by_username, get_or_401


def get_user_id_from_token(token_type: AuthTokenTypes, token: str) -> int:
    """Base function for retrieving user's id from token.
    Raises JWTError if token is incorrect or expired."""
    payload = jwt.decode(
        token, settings.secret_key, algorithms=[JWT_ALGORITHM]
    )

    user_id = payload.get("user_id")
    curr_date = payload.get("expire")

    if curr_date is None:
        raise JWTError

    is_expired = datetime.fromisoformat(curr_date) <= datetime.utcnow()
    is_correct_type = payload.get("type") != token_type

    if is_expired or is_correct_type or not user_id:
        raise JWTError

    return user_id


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> UserWithTokens:
    """Authenticates user with given username and password.
    Returns user if credentials are correct, otherwise raises 401"""
    user = await get_by_username(session, username)

    if user is None:
        raise BadCredentialsException

    is_password_matching = password_context.verify(password, user.password)

    if is_password_matching is False:
        raise BadCredentialsException

    return UserWithTokens(user=user, **generate_auth_tokens(user.id))


async def refresh_tokens(
    session: AsyncSession, refresh_token: str
) -> UserWithTokens:
    """Returns new access and refresh tokens if refresh token is valid."""
    try:
        user_id = get_user_id_from_token(AuthTokenTypes.REFRESH, refresh_token)
        user = await get_or_401(session, user_id)
        return UserWithTokens(user=user, **generate_auth_tokens(user.id))
    except JWTError:
        raise BadTokenException
