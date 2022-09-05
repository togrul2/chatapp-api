"""
Models for validation in controllers via pydantic.
"""
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


class TokenData(BaseModel):
    access_token: str
    refresh_token: str


class RefreshData(BaseModel):
    refresh: str
