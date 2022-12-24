from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from schemas.user import UserRead


class FriendshipBase(BaseModel):
    receiver_id: int

    class Config:
        orm_mode = True


class FriendshipRead(FriendshipBase):
    id: int
    sender_id: int
    accepted: Optional[bool]
    created_at: datetime


class FriendshipReadWithSender(FriendshipBase):
    id: int
    accepted: Optional[bool]
    created_at: datetime
    sender: UserRead


class FriendshipCreate(FriendshipBase):
    sender_id: int
