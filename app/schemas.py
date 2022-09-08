"""
Schemas for validation in controllers via pydantic.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """User model"""
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
    password: str = Field(regex="^[A-Z][\w@?!\-$]*$", min_length=6,
                          description=password_desc)


class UserRead(UserBase):
    id: int = Field(description="id of a user")


class UserPartialUpdate(UserBase):
    username: Optional[str] = Field(min_length=6)
    email: EmailStr | None
    first_name: Optional[str] = Field(min_length=2)
    last_name: Optional[str] = Field(min_length=2)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str


class RefreshData(BaseModel):
    refresh_token: str
