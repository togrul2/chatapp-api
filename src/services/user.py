"""
User services module.
Contains functions and coroutines for
performing business logic related to user and authentication.
"""
import os
from typing import TypedDict, cast

from fastapi import UploadFile
from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import authentication
from src.authentication import password_context
from src.exceptions.base import http_404_not_found
from src.exceptions.user import (
    BadCredentialsException,
    EmailAlreadyTaken,
    HTTPBadTokenException,
    UsernameAlreadyTaken,
)
from src.models.user import User
from src.paginator import BasePaginator
from src.schemas.base import PaginatedResponse
from src.schemas.user import UserBase, UserCreate, UserPartialUpdate, UserRead
from src.services import base as base_services


def get_profile_pictures_dir(user_id: int):
    """Generates path for user profile picture."""
    return f"users/{user_id}/pfp/"


def get_profile_picture_uri(user_id: int, image: UploadFile):
    """Returns URI for given profile picture."""
    return os.path.join(get_profile_pictures_dir(user_id), image.filename)


async def _validate_username_uniqueness(
    session: AsyncSession, username: str, user_id: int | None = None
):
    matching_user: bool = await session.scalar(
        exists()
        .where((User.username == username) & (User.id != user_id))
        .select()
    )

    if matching_user:
        raise UsernameAlreadyTaken


async def _validate_email_uniqueness(
    session: AsyncSession, email: str, user_id: int | None = None
):
    matching_user: bool = await session.scalar(
        exists().where((User.email == email) & (User.id != user_id)).select()
    )

    if matching_user:
        raise EmailAlreadyTaken


async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Returns user with given id or None if no user was found."""
    return await session.get(User, user_id)


async def _get_by_username(
    session: AsyncSession, username: str
) -> User | None:
    """Returns user with matching username."""
    query = select(User).where(User.username == username)
    return await session.scalar(query)


async def get_or_401(session: AsyncSession, user_id: int) -> User:
    """Returns user with given id.
    If not found, raises 401 unauthenticated error."""
    user = await get_by_id(session, user_id)

    if user is None:
        raise HTTPBadTokenException

    return user


async def get_or_404(session: AsyncSession, user_id: int) -> User:
    """Returns user with given id.
    If user with given id does not exist, raises 404 Not Found"""
    user = await get_by_id(session, user_id)

    if user is None:
        raise http_404_not_found("User with given id has not been found.")

    return user


async def get_by_username_or_404(session: AsyncSession, username: str) -> User:
    """Returns user by his username.
    If user is not found, raises 404 not found error"""
    user = await _get_by_username(session, username)

    if user is None:
        raise http_404_not_found(
            "User with given username has not been found."
        )

    return user


async def create_user(session: AsyncSession, schema: UserCreate) -> User:
    """Creates user with hashed password."""
    await _validate_username_uniqueness(session, schema.username)
    await _validate_email_uniqueness(session, schema.email)
    schema.password = password_context.hash(schema.password)
    return await base_services.create(session, User(**schema.dict()))


async def list_users(
    session: AsyncSession,
    paginator: BasePaginator | None = None,
    keyword: str | None = None,
) -> PaginatedResponse[UserRead] | list[User]:
    """Returns list of items matching the given keyword.
    For now, it is simple exact match."""
    query = select(User)

    if keyword:
        expression = keyword + "%"
        query = query.where(
            User.username.like(expression) | User.email.like(expression)
        )

    if paginator:
        return await paginator.get_paginated_response_for_model(query)

    return (await session.scalars(query)).all()


async def update_profile_picture(
    session: AsyncSession, user_id: int, image_url: str
) -> User:
    """
    Sets image as a profile picture of a user
    and returns updated user info.
    """
    user: User = await get_or_404(session, user_id)
    return await base_services.update(
        session, user, {"profile_picture": image_url}
    )


async def remove_profile_picture(session: AsyncSession, user_id: int) -> User:
    """
    Sets user's profile picture to null and returns updated info.
    It doesn't delete file from storage.
    """
    user = await get_or_404(session, user_id)
    user.profile_picture = None
    await session.commit()
    await session.refresh(user)
    return user


class AuthTokens(TypedDict):
    """Typed dict for access and refresh tokens."""

    access_token: str
    refresh_token: str


def _generate_auth_tokens(user_id: int) -> AuthTokens:
    """Generates access and refresh tokens for user with given id."""
    return {
        "access_token": authentication.create_access_token(user_id),
        "refresh_token": authentication.create_refresh_token(user_id),
    }


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> AuthTokens:
    """Authenticates user with given username and password.
    Returns user if credentials are correct, otherwise raises 401"""
    user = await _get_by_username(session, username)

    if (
        user is None
        or password_context.verify(password, user.password) is False
    ):
        raise BadCredentialsException

    return _generate_auth_tokens(cast(int, user.id))


async def refresh_tokens(
    session: AsyncSession, refresh_token: str
) -> AuthTokens:
    """Returns new access and refresh tokens if refresh token is valid."""
    user_id, _ = authentication.get_user_id_from_refresh_token(refresh_token)
    await get_or_401(session, user_id)
    return _generate_auth_tokens(user_id)


async def update_user(
    session: AsyncSession,
    user_id: int,
    schema: (UserPartialUpdate | UserBase),
) -> User:
    """
    Updates user with given user_id
    Validate uniqueness of username and email,
    if they are not met, these validation methods will raise exceptions
    """
    if schema.username:
        await _validate_username_uniqueness(session, schema.username, user_id)

    if schema.email:
        await _validate_email_uniqueness(session, schema.email, user_id)

    user = await get_or_404(session, user_id)
    payload = {k: v for k, v in schema.dict().items() if v is not None}
    return await base_services.update(session, user, payload)


async def delete_user(session: AsyncSession, user_id: int) -> None:
    """Deletes user with given id.
    If user is not found, raises 401 not authenticated."""
    user = await get_or_404(session, user_id)
    await session.execute(delete(User).where(User.id == user.id))
    await session.commit()
