"""
Schemas for validation in controllers via pydantic.
"""
from urllib import parse

from pydantic import EmailStr, Field, validator

from src.base.schemas import BaseOrmModel
from src.config import STATIC_DOMAIN


class UserBase(BaseOrmModel):
    """Base schema for User"""

    username: str = Field(min_length=6)
    email: EmailStr
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)


class UserCreate(UserBase):
    """Schema for validating user create func"""

    password: str = Field(
        regex=r"^[A-Z][\w@?!\-$]*$",  # noqa: W605
        min_length=6,
        description="""
        Password field must match following pattern.
        - Minimum length of 6.
        - Start with capital letter.
        - Must contain ascii letters, digits and - ? ! @ $ symbols.
        """,
    )


class UserRead(UserBase):
    """Schema for validating public user read."""

    id: int = Field(description="id of a user")
    profile_picture: str | None

    @validator("profile_picture")
    def format_profile_picture(cls, value: str):
        """Prepends domain to the file path."""

        if value is not None:
            return parse.urljoin(STATIC_DOMAIN, parse.quote(value))
        return value


class UserPartialUpdate(BaseOrmModel):
    """Schema for validating partial user update fields."""

    username: str | None = Field(min_length=6)
    email: EmailStr | None
    first_name: str | None = Field(min_length=2)
    last_name: str | None = Field(min_length=2)
