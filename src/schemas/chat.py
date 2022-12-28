"""Chat schemas module."""
from pydantic import BaseModel, Field


class BaseChat(BaseModel):
    name: str = Field()
    private: bool


class ChatCreate(BaseChat):
    creator_id: int


class ChatRead(BaseChat):
    id: int
    number_of_members: int
