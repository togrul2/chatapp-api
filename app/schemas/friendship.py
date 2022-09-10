from datetime import datetime

from fastapi import Depends
from pydantic import BaseModel, validator

from services import UserService, get_user_service


class FriendshipBase(BaseModel):
    receiver_id: int

    @validator('receiver_id')
    def validate_receiver_existence(
            self, value: int,
            user_service: UserService = Depends(get_user_service)):
        user_service.get_or_404(value)


class FriendshipRead(FriendshipBase):
    id: int
    sender_id: int
    accepted: bool
    created_at: datetime

    @validator('sender_id')
    def validate_sender_existence(
            self, value: int,
            user_service: UserService = Depends(get_user_service)):
        user_service.get_or_404(value)
