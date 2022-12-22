"""User services module."""
from functools import partial
from typing import Any, Optional

from fastapi import UploadFile

import authentication
from config import STATIC_FILES_DIR, STATIC_FILES_URL
from exceptions import (user as user_exceptions,
                        base as base_exception)
from models import User
from services.base import get_service, CreateUpdateDeleteService
from schemas import user as user_schemas


user_profile_picture_path = 'users/{user_id}/pfp'


def get_pfp_dir(user_id: int):
    """Returns user's profile pictures directory."""
    return STATIC_FILES_DIR / 'users' / str(user_id) / 'pfp'


def get_pfp_path(user_id: int, image: UploadFile):
    """Generates path for user profile picture."""
    base_path = get_pfp_dir(user_id)
    base_path.mkdir(exist_ok=True, parents=True)
    return base_path / image.filename


def get_pfp_url(user_id: int, image: UploadFile):
    """Returns url for file."""
    # return STATIC_FILES_URL + f'users/{user_id}/pfp/{image.filename}'
    return (STATIC_FILES_URL +
            user_profile_picture_path.format(user_id=user_id) +
            '/' + image.filename)


class UserService(CreateUpdateDeleteService):
    model = User

    def _validate_username_uniqueness(self, username: str,
                                      user_id: Optional[int] = None):
        """Validates uniqueness of a username against given user_id."""
        if (self.db.query(self.model.id, self.model.username).filter(
                (self.model.username == username) &
                (self.model.id != user_id)
        ).first()) is not None:
            raise user_exceptions.UsernameAlreadyTaken

    def _validate_email_uniqueness(self, email: str,
                                   user_id: Optional[int] = None):
        """Validates uniqueness of a email against given user_id."""
        if (self.db.query(self.model.id, self.model.email).filter(
                (self.model.email == email) &
                (self.model.id != user_id)
        ).first()) is not None:
            raise user_exceptions.EmailAlreadyTaken

    def _get_by_username(self, username: str):
        """Returns user with matching username"""
        return self.db.query(self.model).filter_by(username=username).first()

    def get_or_401(self, user_id: int):
        user = self._get_by_pk(user_id)
        if user is None:
            raise user_exceptions.CredentialsException
        return user

    def get_by_username_or_404(self, username: str):
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

    def filter_by_username_or_email(self, username: str,
                                    email: str) -> list[Any]:
        """List users by matching username or email."""
        return self.db.query(self.model).filter(
            (self.model.username.like(username)) |
            (self.model.email.like(email))
        ).all()

    def update_profile_picture(self, user_id: int, image_url: str) -> Any:
        """
        Sets image as a profile picture of a user
        and returns updated user info.
        """
        user = self.get_or_404(user_id)
        user.profile_picture = image_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def remove_profile_picture(self, user_id: int):
        """
        Sets user's profile picture to null and returns updated info.
        It doesn't delete file from storage.
        """
        user = self.get_or_404(user_id)
        user.profile_picture = None
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str):
        user = self._get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if not user or authentication.verify_password(password,
                                                      user.password) is False:
            raise user_exceptions.CredentialsException
        return user

    def refresh_tokens(self, refresh_token: str):
        user_id = authentication.verify_refresh_token(refresh_token)
        if self._get_by_pk(user_id) is None:
            raise user_exceptions.CredentialsException

        return {
            'access_token': authentication.create_access_token(user_id),
            'refresh_token': authentication.create_refresh_token(user_id)
        }

    def update(self, pk, schema: (user_schemas.UserPartialUpdate |
                                  user_schemas.UserBase)) -> Any:
        # Validate uniqueness of username and email,
        # if they are not met, these validation methods will raise exceptions
        self._validate_username_uniqueness(schema.username, pk)
        self._validate_email_uniqueness(schema.email, pk)
        return super(UserService, self).update(pk, schema)


# Dependency with user services, should be used with Depends().
get_user_service = partial(get_service, UserService)
