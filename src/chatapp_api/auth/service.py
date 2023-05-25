"""
Authentication module with all stuff related to authentication via jwt.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jose import JWTError, jwt

from src.chatapp_api.auth.exceptions import BadTokenException
from src.chatapp_api.auth.jwt import (
    AuthTokenTypes,
    generate_auth_tokens,
    password_context,
)
from src.chatapp_api.config import JWT_ALGORITHM, settings
from src.chatapp_api.user.exceptions import BadCredentialsException
from src.chatapp_api.user.service import UserService


@dataclass
class AuthService:
    """Auth service with auth related business logic."""

    user_service: UserService

    @staticmethod
    def _parse_token(token_type: AuthTokenTypes, token: str) -> dict:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("user_id")
        curr_date = payload.get("expire")

        if curr_date is None or user_id is None:
            raise JWTError

        is_expired = datetime.fromisoformat(curr_date) <= datetime.utcnow()
        is_correct_type = payload.get("type") == token_type

        if is_expired is True or is_correct_type is False:
            raise JWTError

        return {
            "user_id": int(user_id),
            "expire": datetime.fromisoformat(curr_date),
        }

    def get_user_id_from_token(
        self, token_type: AuthTokenTypes, token: str
    ) -> int:
        """Base function for retrieving user's id from token.
        Raises JWTError if token is incorrect or expired."""
        return self._parse_token(token_type, token)["user_id"]

    async def authenticate_user(
        self, username: str, password: str
    ) -> dict[str, Any]:
        """Authenticates user with given username and password.
        Returns user if credentials are correct, otherwise raises 401"""
        user = await self.user_service.get_by_username(username)

        if user is None:
            raise BadCredentialsException

        is_password_matching = password_context.verify(password, user.password)

        if is_password_matching is False:
            raise BadCredentialsException

        return {"user": user, **generate_auth_tokens(user.id)}

    async def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        """Returns new access and refresh tokens if refresh token is valid."""
        try:
            user_id = self.get_user_id_from_token(
                AuthTokenTypes.REFRESH, refresh_token
            )
            user = await self.user_service.get_or_401(user_id)
            return {"user": user, **generate_auth_tokens(user.id)}
        except JWTError:
            raise BadTokenException

    async def validate_access_token(self, access_token: str) -> None:
        """validates access token, raises exception if it is invalid."""
        try:
            self._parse_token(AuthTokenTypes.ACCESS, access_token)
        except JWTError as exc:
            raise BadTokenException from exc
