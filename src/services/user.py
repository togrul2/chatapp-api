"""User services module."""
from typing import Any

from fastapi import UploadFile

import authentication
from exceptions import base as base_exception
from exceptions import user as user_exceptions
from models.user import User
from schemas import user as user_schemas
from schemas.base import PaginatedResponse
from services.base import CreateUpdateDeleteService


def get_pfp_path(user_id: int):
    """Generates path for user profile picture."""
    return f"users/{user_id}/pfp/"


def get_pfp_url(user_id: int, image: UploadFile):
    """Returns url for file."""
    return f"users/{user_id}/pfp/{image.filename}"


class UserService(CreateUpdateDeleteService):
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
            raise user_exceptions.UsernameAlreadyTaken

    def _validate_email_uniqueness(
        self, email: str, user_id: int | None = None
    ):
        """Validates uniqueness of a email against given user_id."""
        if (
            self.session.query(self.model.id, self.model.email)
            .filter((self.model.email == email) & (self.model.id != user_id))
            .first()
        ) is not None:
            raise user_exceptions.EmailAlreadyTaken

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
            raise user_exceptions.HTTPBadTokenException
        return user

    def get_by_username_or_404(self, username: str):
        """Returns user by his username. Raises 404 if not found"""
        user = self._get_by_username(username)
        if user is None:
            raise base_exception.NotFound
        return user

    def create(self, schema: user_schemas.UserCreate):
        """Creates user with hashed password."""
        self._validate_username_uniqueness(schema.username)
        self._validate_email_uniqueness(schema.email)
        schema.password = authentication.get_hashed_password(schema.password)
        return super().create(schema)

    def filter_by_username_or_email(
        self, username: str, email: str
    ) -> PaginatedResponse[user_schemas.UserRead]:
        """List users by matching username or email."""
        query = self.session.query(self.model).filter(
            (self.model.username.like(username))
            | (self.model.email.like(email))
        )

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def update_profile_picture(self, user_id: int, image_url: str) -> Any:
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
            raise user_exceptions.HTTPBadTokenException
        return user

    def refresh_tokens(self, refresh_token: str):
        """Returns new access and refresh tokens if refresh token is valid."""
        user_id = authentication.verify_refresh_token(refresh_token)
        if self._get_by_pk(user_id) is None:
            raise user_exceptions.HTTPBadTokenException

        return {
            "access_token": authentication.create_access_token(user_id),
            "refresh_token": authentication.create_refresh_token(user_id),
        }

    def update(
        self,
        pk,
        schema: (user_schemas.UserPartialUpdate | user_schemas.UserBase),
    ) -> Any:
        # Validate uniqueness of username and email,
        # if they are not met, these validation methods will raise exceptions
        if schema.username:
            self._validate_username_uniqueness(schema.username, pk)

        if schema.email:
            self._validate_email_uniqueness(schema.email, pk)

        return super().update(pk, schema)
