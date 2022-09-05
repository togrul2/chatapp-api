from abc import ABC
from typing import Mapping, Any

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
    model: Any

    def __init__(self, db: Session):
        self.db = db

    def get_by_pk(self, pk: Any):
        return self.db.query(self.model).get(pk)

    def get_or_404(self, pk: Any):
        """
        Returns item matching the query. If item is not found
        raises HTTPException with status code of 404.

        Make sure to use unique identifier, if multiple items
        match the query unexpected behavior might occur.
        """
        item = self.get_by_pk(pk)
        if item is None:
            raise HTTPException(
                status_code=404,
                detail="Item with given pk was not found."
            )
        return item

    def create(self, fields: BaseModel):
        item = self.model(**fields.dict())
        self.db.add(item)
        self.db.commit()
        return item

    @classmethod
    def update(cls, db: Session,  fields: Mapping[str, Any]):
        ...


class UserService(BaseService):
    model = User

    def create(self, fields: UserCreate):
        fields.password = get_hashed_password(fields.password)
        return super().create(fields)

    def get_by_username(self, username: str):
        return self.db.query(self.model).filter_by(username=username).first()

    def get_by_email(self, email: str):
        return self.db.query(self.model).filter_by(email=email).first()

    def authenticate_user(self, username: str, password: str):
        user = self.get_by_username(username)
        # If user with that username is not found or password is wrong, fail.
        if not user or verify_password(password, user.password) is False:
            return None
        return user
