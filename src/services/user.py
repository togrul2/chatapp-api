"""User services module."""
from typing import Any

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.sql import Select

from src import authentication
from src.exceptions.base import NotFound
from src.exceptions.user import (
    BadCredentialsException,
    EmailAlreadyTaken,
    HTTPBadTokenException,
    UsernameAlreadyTaken,
)
from src.models.user import User
from src.schemas import user as user_schemas
from src.services.base import CreateUpdateDeleteService, ListMixin


def get_pfp_path(user_id: int):
    """Generates path for user profile picture."""
    return f"users/{user_id}/pfp/"


def get_pfp_url(user_id: int, image: UploadFile):
    """Returns url for file."""
    return f"users/{user_id}/pfp/{image.filename}"


class UserService(ListMixin[User], CreateUpdateDeleteService[User]):
    """Service class for User model"""

    model = User

    async def _validate_username_uniqueness(
        self, username: str, user_id: int | None = None
    ):
        result = await self.session.execute(
            select(self.model.id, self.model.username).where(
                (self.model.username == username) & (self.model.id != user_id)
            )
        )
        if result.first() is not None:
            raise UsernameAlreadyTaken

    async def _validate_email_uniqueness(
        self, email: str, user_id: int | None = None
    ):
        """Validates uniqueness of a email against given user_id."""
        result = await self.session.execute(
            select(self.model.id, self.model.email).where(
                (self.model.email == email) & (self.model.id != user_id)
            )
        )
        if result.first() is not None:
            raise EmailAlreadyTaken

    async def get_by_pk(self, pk: Any) -> Any:
        """Returns ites based on its primary key"""
        return await self._get_by_pk(pk)

    async def _get_by_username(self, username: str):
        """Returns user with matching username"""
        query = select(self.model).where(self.model.username == username)
        result = await self.session.execute(query)
        return result.scalar()

    async def get_or_401(self, user_id: int):
        """Returns user with given id. If not found, raises 401."""
        user = await self._get_by_pk(user_id)
        if user is None:
            raise HTTPBadTokenException
        return user

    async def get_by_username_or_404(self, username: str):
        """Returns user by his username. Raises 404 if not found"""
        user = await self._get_by_username(username)

        if user is None:
            raise NotFound

        return user

    async def create_user(self, schema: user_schemas.UserCreate):
        """Creates user with hashed password."""
        await self._validate_username_uniqueness(schema.username)
        await self._validate_email_uniqueness(schema.email)
        schema.password = authentication.get_hashed_password(schema.password)
        return await self.create(schema.dict())

    async def _filter_by_username_or_email(
        self, username: str, email: str
    ) -> Select:
        """Returns query with users by matching username or email."""
        return select(self.model).where(
            self.model.username.like(username) | (self.model.email.like(email))
        )

    async def search(self, keyword: str):
        """Returns list of items matching the given keyword.
        For now it is simple exact match."""

        expression = keyword + "%"
        query = await self._filter_by_username_or_email(expression, expression)

        if self._paginator:
            return await self._paginator.get_paginated_response(query)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_profile_picture(
        self, user_id: int, image_url: str
    ) -> User:
        """
        Sets image as a profile picture of a user
        and returns updated user info.
        """
        query = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(profile_picture=image_url)
        )
        await self.session.execute(query)
        await self.session.commit()
        user = await self.get_or_404(user_id)
        return user

    async def remove_profile_picture(self, user_id: int):
        """
        Sets user's profile picture to null and returns updated info.
        It doesn't delete file from storage.
        """
        query = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(profile_picture=None)
        )
        await self.session.execute(query)
        await self.session.commit()
        user = await self.get_or_404(user_id)
        return user

    async def authenticate_user(self, username: str, password: str):
        """Returns user model if given username and password are correct."""
        user = await self._get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if (
            not user
            or authentication.verify_password(password, user.password) is False
        ):
            raise BadCredentialsException
        return user

    async def refresh_tokens(self, refresh_token: str):
        """Returns new access and refresh tokens if refresh token is valid."""
        user_id = authentication.verify_refresh_token(refresh_token)
        if await self._get_by_pk(user_id) is None:
            raise HTTPBadTokenException

        return {
            "access_token": authentication.create_access_token(user_id),
            "refresh_token": authentication.create_refresh_token(user_id),
        }

    async def update_user(
        self,
        pk: int,
        schema: (user_schemas.UserPartialUpdate | user_schemas.UserBase),
    ) -> User:
        """
        Updates user with given pk
        Validate uniqueness of username and email,
        if they are not met, these validation methods will raise exceptions
        """
        if schema.username:
            await self._validate_username_uniqueness(schema.username, pk)

        if schema.email:
            await self._validate_email_uniqueness(schema.email, pk)

        return await self.update(pk, schema.dict())
