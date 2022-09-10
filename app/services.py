"""
Services module with crud tools for models.
"""
import shutil
from abc import ABC
from functools import partial
from typing import Any, Optional, Type

from fastapi import HTTPException, status, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

import jwt
from db import get_db
from config import BASE_DIR
from models import User, Chat, Friendship
from exceptions import (user as user_exceptions,
                        base as base_exception)
from schemas.user import UserCreate, UserPartialUpdate, UserBase


def get_file_path(user_id: int, image: UploadFile):
    """Generates path for user profile pictures."""
    base_path = BASE_DIR / "app" / "static" / str(user_id)
    base_path.mkdir(exist_ok=True, parents=True)
    return base_path / image.filename


def get_file_url(user_id: int, image: UploadFile):
    """Returns url for file."""
    return f"/static/{user_id}/{image.filename}"


def upload_static_file(path: str, file: UploadFile):
    """Uploads file to given path"""
    with open(path, "wb") as fp:
        shutil.copyfileobj(file.file, fp)


class BaseService(ABC):
    """
    Base service class with database operation for models.

    Must override model attribute and assign model
    which service is related to.
    """
    model: Any

    def __init__(self, db: Session):
        self.db = db

    def _get_by_pk(self, pk: Any) -> Any:
        return self.db.query(self.model).get(pk)

    def all(self):
        return self.db.query(self.model).all()

    def get_or_404(self, pk: Any) -> Any:
        """
        Returns item matching the query. If item is not found
        raises HTTPException with status code of 404.
        """
        item = self._get_by_pk(pk)
        if item is None:
            raise base_exception.NotFound
        return item

    def create(self, fields: BaseModel) -> Any:
        item = self.model(**fields.dict())
        self.db.add(item)
        self.db.commit()
        return item

    def update(self, pk, fields: BaseModel) -> Any:
        item = self.get_or_404(pk)

        for field, value in fields.dict().items():
            if value is not None:
                setattr(item, field, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, pk: Any) -> bool:
        """
        Delete method

        :return: True, if delete was successful.
        """
        item = self.get_or_404(pk)
        self.db.delete(item)
        self.db.commit()
        return True


def _get_service(service: Type[BaseService],
                 db: Session = Depends(get_db)):
    """
    Base function for creating service dependency
    for using with fastapi dependency injection tool.
    Services give us a class with crud operations etc.
    with established db connection and settings.
    """
    yield service(db)


class UserService(BaseService):
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

    def create(self, fields: UserCreate):
        """Creates user with hashed password."""
        self._validate_username_uniqueness(fields.username)
        self._validate_email_uniqueness(fields.email)
        fields.password = jwt.get_hashed_password(fields.password)
        return super().create(fields)

    def filter_by_username_or_email(self, username: str,
                                    email: str) -> list[Any]:
        """List users by matching username or email"""
        return self.db.query(self.model).filter(
            (self.model.username.like(username)) |
            (self.model.email.like(email))
        ).all()

    def update_profile_picture(self, user_id: int,
                               url: str):
        """
        Uploads image to static files and sets it
        as a profile picture of a user.
        """
        user = self.get_or_404(user_id)
        user.profile_picture = url
        self.db.commit()
        self.db.refresh(user)
        return user

    def remove_profile_picture(self, user_id: int):
        """
        Sets user's profile picture to null.
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
        if not user or jwt.verify_password(password, user.password) is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password"
            )
        return user

    def refresh_tokens(self, refresh_token: str):
        user_id = jwt.verify_refresh_token(refresh_token)
        if self._get_by_pk(user_id) is None:
            raise jwt.CredentialsException

        return {
            "access_token": jwt.create_access_token(user_id),
            "refresh_token": jwt.create_refresh_token(user_id)
        }

    def update(self, pk, fields: UserPartialUpdate | UserBase) -> Any:
        # Validate uniqueness of username and email,
        # if they are not met, these validation methods will raise exceptions
        self._validate_username_uniqueness(fields.username, pk)
        self._validate_email_uniqueness(fields.email, pk)
        return super(UserService, self).update(pk, fields)


get_user_service = partial(_get_service, UserService)


class FriendshipService(BaseService):
    """Friendship service class with db manipulation methods."""
    model = Friendship

    def __init__(self, db: Session,
                 user_id: int = Depends(jwt.get_current_user_id)):
        super().__init__(db)
        self.user_service = UserService(self.db)
        self.user = self.user_service.get_or_401(user_id)

    def list_pending_friendships(self):
        return self.db.query(self.model).filter(
            self.model.receiver_id == self.user.id).all()

    def friendship_exists(self):
        return self.db.query(self.model).filter()

    def create(self, target_id: int) -> Friendship:
        """Send friendship for target user """
        try:
            self.user_service.get_or_404(target_id)
        except base_exception.NotFound as err:
            raise HTTPException(
                status_code=404,
                detail='User with given id does not exist.') from err
        return super().create(BaseModel.construct())

    def approve(self, friendship_id: int) -> Friendship:
        """Service method for approving pending request"""
        friendship = self.db.query(self.model).filter(
            sender_id=self.user.id, friendship_id=friendship_id)
        friendship.accept = True
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def delete(self, pk: Any) -> bool:
        item = self.db.query(self.model).filter(
            (self.model.sender_id == self.user.id) |
            (self.model.receiver_id == self.user.id)
        ).filter(
            self.model.id == pk).first()
        if item is None:
            raise base_exception.NotFound
        self.db.delete(item)
        return True


get_friendship_service = partial(_get_service, FriendshipService)


class ChatService(BaseService):
    model = Chat


get_chat_service = partial(_get_service, ChatService)
