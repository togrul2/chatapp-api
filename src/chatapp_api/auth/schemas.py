"""Module with auth related schemas."""
from src.chatapp_api.base.schemas import BaseOrmModel
from src.chatapp_api.user.schemas import UserRead


class RefreshTokenDto(BaseOrmModel):
    """Schema for validating request body with refresh token."""

    refresh_token: str


class UserWithTokens(BaseOrmModel):
    """Schema for validating user model with access and refresh tokens"""

    user: UserRead
    access_token: str
    refresh_token: str
