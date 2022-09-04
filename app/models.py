"""
Models for validation in controllers via pydantic.
"""

from datetime import date
from typing import Optional

from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    """User model"""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    dob: date


class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True)
    profile_picture: Optional[str]
