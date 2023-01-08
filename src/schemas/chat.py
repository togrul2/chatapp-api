"""Chat schemas module."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from schemas.user import UserRead


class BaseChat(BaseModel):
    """Base pydantic validation schema for chat model"""

    name: Optional[str] = Field()
    private: bool


class ChatCreate(BaseChat):
    """Pydantic validation schema for handling chat model write"""

    users: list[int]


class ChatRead(BaseChat):
    """Pydantic validation schema for handling chat model read"""

    id: int
    admin: UserRead
    number_of_members: int


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
