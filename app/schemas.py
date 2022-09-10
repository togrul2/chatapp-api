"""
Schemas for validation in controllers via pydantic.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class DetailMessage(BaseModel):
    """Detail schema for error messages."""
    detail: str


class UserBase(BaseModel):
    """User schema"""
    username: str = Field(min_length=6)
    email: EmailStr
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)

    class Config:
        orm_mode = True


password_desc = '''
Password field must match following pattern.
  - Minimum length of 6.
  - Start with capital letter.
  - Must contain ascii letters, digits and - ? ! @ $ symbols.
'''


class UserCreate(UserBase):
    password: str = Field(regex="^[A-Z][\w@?!\-$]*$",  # noqa: W605
                          min_length=6, description=password_desc)


class UserRead(UserBase):
    id: int = Field(description="id of a user")
    profile_picture: Optional[str]


class UserPartialUpdate(UserBase):
    username: Optional[str] = Field(min_length=6)
    email: EmailStr | None
    first_name: Optional[str] = Field(min_length=2)
    last_name: Optional[str] = Field(min_length=2)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
