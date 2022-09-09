"""
Services module with crud tools for models.
"""
from abc import ABC
from typing import Any, Optional

from fastapi import HTTPException, status, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import BASE_DIR
from db import get_db
from models import User
from jwt import get_hashed_password, verify_password
from schemas import UserCreate, UserPartialUpdate, UserBase

UsernameAlreadyTaken = HTTPException(
    status_code=400,
    detail="User with given username already exists."
)

EmailAlreadyTaken = HTTPException(
    status_code=400,
    detail="User with given email already exists."
)


def get_file_path(user_id: int, image: UploadFile):
    """Generates path for user profile pictures."""

    base_path = BASE_DIR / "app" / "static" / str(user_id)
    base_path.mkdir(exist_ok=True, parents=True)
    return base_path / image.filename


def get_file_url(user_id: int, image: UploadFile):
    """Returns url for file."""
    return f"/static/{user_id}/{image.filename}"


class BaseService(ABC):
    """
    Base service class with database operation for models.

    Must override model attribute and assign model
    which service is related to.

    Example:
        class BaseService(ABC):
            model: Any

        class UserService(BaseService):
            model = User
    """
    model: Any

    def __init__(self, db: Session):
        self.db = db

    def get_by_pk(self, pk: Any) -> Any:
        return self.db.query(self.model).get(pk)

    def all(self):
        return self.db.query(self.model).all()

    def get_or_404(self, pk: Any) -> Any:
        """
        Returns item matching the query. If item is not found
        raises HTTPException with status code of 404.
        """
        item = self.get_by_pk(pk)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Not found."
            )
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


class UserService(BaseService):
    model = User

    def _validate_username_uniqueness(self, username: str,
                                      user_id: Optional[int] = None):
        """Validates uniqueness of a username against given user_id."""
        if (self.db.query(self.model.id, self.model.username).filter(
                (self.model.username == username) &
                (self.model.id != user_id)
        ).first()) is not None:
            raise UsernameAlreadyTaken

    def _validate_email_uniqueness(self, email: str,
                                   user_id: Optional[int] = None):
        """Validates uniqueness of a email against given user_id."""
        if (self.db.query(self.model.id, self.model.email).filter(
                (self.model.email == email) &
                (self.model.id != user_id)
        ).first()) is not None:
            raise EmailAlreadyTaken

    def _get_by_username(self, username: str):
        """Returns user with matching username"""
        return self.db.query(self.model).filter_by(username=username).first()

    def create(self, fields: UserCreate):
        """Creates user with hashed password."""
        self._validate_username_uniqueness(fields.username)
        self._validate_email_uniqueness(fields.email)
        fields.password = get_hashed_password(fields.password)
        return super().create(fields)

    def filter_by_username_or_email(self, username: str,
                                    email: str) -> list[Any]:
        """List users by matching username or email"""
        return self.db.query(self.model).filter(
            (self.model.username.like(username)) |
            (self.model.email.like(email))
        ).all()

    def update_profile_picture(self, user_id: int, path: str):
        user = self.get_by_pk(user_id)
        user.profile_picture = path
        self.db.commit()
        self.db.refresh(user)
        return user

    def remove_profile_picture(self, user_id: int):
        user = self.get_by_pk(user_id)
        user.profile_picture = None
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, username: str, password: str):
        user = self._get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if not user or verify_password(password, user.password) is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid username or password"
            )
        return user

    def update(self, pk, fields: UserPartialUpdate | UserBase) -> Any:
        # Validate uniqueness of username and email,
        # if they are not met, these validation methods will raise exception
        self._validate_username_uniqueness(fields.username, pk)
        self._validate_email_uniqueness(fields.email, pk)
        return super(UserService, self).update(pk, fields)


def get_user_service(db: Session = Depends(get_db)):
    """
    User service dependency for using with fastapi dependency injection tool.
    It gives us a user service with established db connection and settings.

    Example:
        >>> def get_users(service: UserService = Depends(get_user_service)):
        >>>     return service.all()
    """
    yield UserService(db)
