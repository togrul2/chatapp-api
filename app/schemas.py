"""
Models for validation in controllers via pydantic.
"""
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """User model"""
    username: str = Field(min_length=6, default="johndoe")
    email: EmailStr = Field(...)
    first_name: str = Field(min_length=2, default="John")
    last_name: str = Field(min_length=2, default="Doe")

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
    id: int = Field(description="id of a user", default=1)


class TokenData(BaseModel):
    access_token: str
    refresh_token: str


class RefreshData(BaseModel):
    refresh: str
