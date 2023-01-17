"""Chat schemas module."""
from datetime import datetime

from pydantic import BaseModel, constr

from src.schemas.user import UserRead


class BaseChat(BaseModel):
    """Base pydantic validation schema for chat model"""

    name: str | None

    class Config:
        orm_mode = True


class UserDict(BaseModel):
    """Pydantic validation model for
    validating user field in chat operations."""

    id: int
    is_admin: bool = False


class ChatCreate(BaseChat):
    """Pydantic validation schema for handling chat model write"""

    name: constr(min_length=2, strip_whitespace=True)
    users: list[UserDict]


class ChatRead(BaseChat):
    """Pydantic validation schema for handling chat model read."""

    id: int
    created_at: datetime


class ChatReadWithMembers(ChatRead):
    """Pydantic validation schema for
    handling chat model read with members field."""

    members: int


class ChatUpdate(BaseChat):
    """Pydantic model for validating chat update payload."""

    name: constr(min_length=2, strip_whitespace=True)


class BaseMessage(BaseModel):
    """Base Message model pydantic model(schema)"""

    body: str
    chat_id: int

    class Config:
        orm_mode = True


class MessageRead(BaseMessage):
    """Pydantic model for validating message read model"""

    id: int
    sender: UserRead
    created_at: datetime


class MembershipBase(BaseModel):
    """Base pydantic model for validating membership related operations.
    Can be used for create validation"""

    user_id: int
    chat_id: int
    is_admin: bool
    is_owner: bool

    class Config:
        orm_mode = True
