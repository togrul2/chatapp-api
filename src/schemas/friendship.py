"""Pydantic validation modelds(schemas) for Friendship related routes."""
from datetime import datetime

from pydantic import BaseModel

from src.schemas.user import UserRead


class FriendshipBase(BaseModel):
    """Base friendship schema"""

    receiver_id: int

    class Config:
        orm_mode = True


class FriendshipRead(FriendshipBase):
    """Friendship schema for reading"""

    id: int
    sender_id: int
    accepted: bool | None
    created_at: datetime


class FriendshipReadWithSender(FriendshipBase):
    """Friendship schema for reading friendships with extended sender field"""

    id: int
    accepted: bool | None
    created_at: datetime
    sender: UserRead


class FriendshipCreate(FriendshipBase):
    """Frienship schema for creation"""

    sender_id: int
    accepted: bool | None = None
