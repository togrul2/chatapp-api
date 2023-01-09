"""Chat schemas module."""
from datetime import datetime

from pydantic import BaseModel

from schemas.user import UserRead


class BaseChat(BaseModel):
    """Base pydantic validation schema for chat model"""

    name: str | None

    class Config:
        orm_mode = True


class ChatCreate(BaseChat):
    """Pydantic validation schema for handling chat model write"""

    name: str
    users: list[int]


class ChatRead(BaseChat):
    """Pydantic validation schema for handling chat model read"""

    id: int
    number_of_members: int
    created_at: datetime


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
