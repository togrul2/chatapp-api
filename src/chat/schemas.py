"""Chat schemas module."""
from datetime import datetime

from pydantic import BaseModel, ConstrainedStr

from src.base.schemas import BaseOrmModel
from src.user.schemas import UserRead


class BaseMessage(BaseOrmModel):
    """Base Message schema."""

    body: str
    chat_id: int


class MessageRead(BaseMessage):
    """Schema for validating message read model"""

    id: int
    sender: UserRead
    created_at: datetime


class MembershipBase(BaseOrmModel):
    """Base schema for validating membership related operations.
    Can be used for create validation"""

    user_id: int
    chat_id: int
    is_admin: bool
    is_owner: bool


class MembershipUpdate(BaseOrmModel):
    """Schema for validation membership update payload from request."""

    is_admin: bool


class MemberRead(UserRead):
    """Schema for validating user data for chat members list."""

    chat_id: int
    is_admin: bool
    is_owner: bool


class BaseChat(BaseOrmModel):
    """Base Schema for chat model"""

    name: str | None


class UserDict(BaseModel):
    """Schema for validating user field in chat operations."""

    id: int
    is_admin: bool = False


class ChatNameStr(ConstrainedStr):
    """Validator for checking chat name"""

    min_length = 2
    strip_whitespace = True


class ChatCreate(BaseChat):
    """Schema for handling chat model write"""

    name: ChatNameStr
    users: list[UserDict]


class ChatRead(BaseChat):
    """Schema for handling chat model read."""

    id: int
    created_at: datetime


class ChatReadWithUsersCount(ChatRead):
    """Schema for handling chat model read with members field."""

    users_count: int


class ChatUpdate(BaseChat):
    """Schema for validating chat update payload."""

    name: ChatNameStr


class ChatReadWithLastMessage(ChatRead):
    last_message: MessageRead | None
