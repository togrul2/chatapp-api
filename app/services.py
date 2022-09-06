from abc import ABC
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import User
from jwt import get_hashed_password, verify_password
from schemas import UserCreate


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
    __slots__ = ["model"]
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
                detail="Item with given pk was not found."
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

        Returns:
            bool: True, if delete was successful.
        Raises:
            HTTPException: if object is not found.
        """
        item = self.get_or_404(pk)
        self.db.delete(item)
        self.db.commit()
        return True


class UserService(BaseService):
    model = User

    def create(self, fields: UserCreate):
        """Creates user with hashed password."""
        fields.password = get_hashed_password(fields.password)
        return super().create(fields)

    def get_by_username(self, username: str):
        """Returns user with matching username"""
        return self.db.query(self.model).filter_by(username=username).first()

    def get_by_email(self, email: str):
        """Returns user with matching email"""
        return self.db.query(self.model).filter_by(email=email).first()

    def filter_by_username_or_email(self, username: str,
                                    email: str) -> list[Any]:
        """List users by matching username or email"""
        return self.db.query(self.model).filter(
            (self.model.username.like(username)) |
            (self.model.email.like(email))
        ).all()

    def authenticate_user(self, username: str, password: str):
        user = self.get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if not user or verify_password(password, user.password) is False:
            return None
        return user
