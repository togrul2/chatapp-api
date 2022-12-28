"""
Schemas for validation in controllers via pydantic.
"""
from typing import Optional
from urllib import parse

from pydantic import BaseModel, EmailStr, Field, validator

from config import STATIC_DOMAIN


class UserBase(BaseModel):
    """User schema"""

    username: str = Field(min_length=6)
    email: EmailStr
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)

    class Config:
        orm_mode = True


password_desc = """
Password field must match following pattern.
  - Minimum length of 6.
  - Start with capital letter.
  - Must contain ascii letters, digits and - ? ! @ $ symbols.
"""


class UserCreate(UserBase):
    password: str = Field(
        regex="^[A-Z][\w@?!\-$]*$",  # noqa: W605
        min_length=6,
        description=password_desc,
    )


class UserRead(UserBase):
    id: int = Field(description="id of a user")
    profile_picture: Optional[str]

    @validator("profile_picture")
    def format_profile_picture(cls, value: str):  # noqa
        """Prepends domain to the file path."""
        if value is not None:
            return parse.urljoin(STATIC_DOMAIN, value)
        return value


class UserPartialUpdate(UserBase):
    username: Optional[str] = Field(min_length=6)
    email: Optional[EmailStr]
    first_name: Optional[str] = Field(min_length=2)
    last_name: Optional[str] = Field(min_length=2)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
