"""Chat schemas module."""
from pydantic import BaseModel, Field


class BaseChat(BaseModel):
    """Base pydantic validation schema for chat model"""

    name: str = Field()
    private: bool


class ChatCreate(BaseChat):
    """Pydantic validation schema for hanlding chat model write"""

    creator_id: int


class ChatRead(BaseChat):
    """Pydantic validation schema for hanlding chat model read"""

    id: int
    number_of_members: int
