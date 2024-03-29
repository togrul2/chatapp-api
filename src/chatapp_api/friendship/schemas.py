"""Pydantic validation modelds(schemas) for Friendship related routes."""
from datetime import datetime

from src.chatapp_api.base.schemas import BaseOrmModel
from src.chatapp_api.user.schemas import UserRead


class FriendshipBase(BaseOrmModel):
    """Base friendship schema"""

    receiver_id: int


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
