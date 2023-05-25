"""
Schemas for validation in controllers via pydantic.
"""
from pydantic import BaseModel, EmailStr, Field, constr

from src.chatapp_api.base.schemas import BaseOrmModel

PasswordField = constr(regex=r"^[A-Z][\w@?!\-$]*$", min_length=6)  # noqa: W605


class UserBase(BaseOrmModel):
    """Base schema for User"""

    username: str = Field(min_length=6)
    email: EmailStr
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)


class UserCreate(UserBase):
    """Schema for validating user create func"""

    password: PasswordField


class UserRead(UserBase):
    """Schema for validating public user read."""

    id: int = Field(description="id of a user")
    full_profile_picture: str | None = Field(alias="profile_picture")


class UserPartialUpdate(BaseOrmModel):
    """Schema for validating partial user update fields."""

    username: str | None = Field(min_length=6)
    email: EmailStr | None
    first_name: str | None = Field(min_length=2)
    last_name: str | None = Field(min_length=2)


class UpdatePassword(BaseModel):
    old_password: str
    new_password: PasswordField
