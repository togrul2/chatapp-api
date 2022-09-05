"""
Models for validation in controllers via pydantic.
"""
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    """User model"""
    username: str
    email: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None
