"""User services module."""
from typing import Any

from fastapi import UploadFile

from src import authentication
from src.exceptions.base import NotFound
from src.exceptions.user import (
    EmailAlreadyTaken,
    HTTPBadTokenException,
    UsernameAlreadyTaken,
)
from src.models.user import User
from src.schemas import user as user_schemas
from src.schemas.base import PaginatedResponse
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

    def _validate_username_uniqueness(
        self, username: str, user_id: int | None = None
    ):
        """Validates uniqueness of a username against given user_id."""
        if (
            self.session.query(self.model.id, self.model.username)
            .filter(
                (self.model.username == username) & (self.model.id != user_id)
            )
            .first()
        ) is not None:
            raise UsernameAlreadyTaken

    def _validate_email_uniqueness(
        self, email: str, user_id: int | None = None
    ):
        """Validates uniqueness of a email against given user_id."""
        if (
            self.session.query(self.model.id, self.model.email)
            .filter((self.model.email == email) & (self.model.id != user_id))
            .first()
        ) is not None:
            raise EmailAlreadyTaken

    def get_by_pk(self, pk: Any) -> Any:
        """Returns ites based on its primary key"""
        return self._get_by_pk(pk)

    def _get_by_username(self, username: str):
        """Returns user with matching username"""
        return (
            self.session.query(self.model).filter_by(username=username).first()
        )

    def get_or_401(self, user_id: int):
        """Returns user with given id or raises 401"""
        user = self._get_by_pk(user_id)
        if user is None:
            raise HTTPBadTokenException
        return user

    def get_by_username_or_404(self, username: str):
        """Returns user by his username. Raises 404 if not found"""
        user = self._get_by_username(username)
        if user is None:
            raise NotFound
        return user

    def create_user(self, schema: user_schemas.UserCreate):
        """Creates user with hashed password."""
        self._validate_username_uniqueness(schema.username)
        self._validate_email_uniqueness(schema.email)
        schema.password = authentication.get_hashed_password(schema.password)

        return self.create(schema.dict())

    def _filter_by_username_or_email(
        self, username: str, email: str
    ) -> PaginatedResponse[user_schemas.UserRead]:
        """Returns query with users by matching username or email."""
        return self.session.query(self.model).filter(
            (self.model.username.like(username))
            | (self.model.email.like(email))
        )

    def search(self, keyword: str) -> PaginatedResponse[user_schemas.UserRead]:
        """Returns list of items matching the given keyword.
        For now it is simple exact match."""

        expression = keyword + "%"
        query = self._filter_by_username_or_email(expression, expression)

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def update_profile_picture(self, user_id: int, image_url: str) -> User:
        """
        Sets image as a profile picture of a user
        and returns updated user info.
        """
        user = self.get_or_404(user_id)
        user.profile_picture = image_url
        self.session.commit()
        self.session.refresh(user)
        return user

    def remove_profile_picture(self, user_id: int):
        """
        Sets user's profile picture to null and returns updated info.
        It doesn't delete file from storage.
        """
        user = self.get_or_404(user_id)
        user.profile_picture = None
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str):
        """Returns user model if given username and password are correct."""
        user = self._get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if (
            not user
            or authentication.verify_password(password, user.password) is False
        ):
            raise HTTPBadTokenException
        return user

    def refresh_tokens(self, refresh_token: str):
        """Returns new access and refresh tokens if refresh token is valid."""
        user_id = authentication.verify_refresh_token(refresh_token)
        if self._get_by_pk(user_id) is None:
            raise HTTPBadTokenException

        return {
            "access_token": authentication.create_access_token(user_id),
            "refresh_token": authentication.create_refresh_token(user_id),
        }

    def update_user(
        self,
        pk,
        schema: (user_schemas.UserPartialUpdate | user_schemas.UserBase),
    ) -> User:
        """
        Updates user with given pk
        Validate uniqueness of username and email,
        if they are not met, these validation methods will raise exceptions
        """
        if schema.username:
            self._validate_username_uniqueness(schema.username, pk)

        if schema.email:
            self._validate_email_uniqueness(schema.email, pk)

        return super().update(pk, schema.dict())
