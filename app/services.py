"""
Services module with crud tools for models.
"""
import shutil
from functools import partial
from typing import Any, Optional, ClassVar

from fastapi import HTTPException, status, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

import authentication
from db import get_db
from config import BASE_DIR
from models import User, Chat, Friendship
from exceptions import (user as user_exceptions,
                        base as base_exception)
from schemas.user import UserCreate, UserPartialUpdate, UserBase




class FriendshipService(BaseService):
    """Friendship service class with db manipulation methods."""
    model = Friendship

    def __init__(self, db: Session,
                 user_id: int = Depends(jwt.get_current_user_id)):
        super().__init__(db)
        self.user_service = UserService(self.db)
        self.user = self.user_service.get_or_401(user_id)

    def list_pending_friendships(self):
        return self.db.query(self.model).filter(
            self.model.receiver_id == self.user.id).all()

    def friendship_exists(self):
        return self.db.query(self.model).filter()

    def create(self, target_id: int) -> Friendship:
        """Send friendship for target user """
        try:
            self.user_service.get_or_404(target_id)
        except base_exception.NotFound as err:
            raise HTTPException(
                status_code=404,
                detail='User with given id does not exist.') from err
        return super().create(BaseModel.construct())

    def approve(self, friendship_id: int) -> Friendship:
        """Service method for approving pending request"""
        friendship = self.db.query(self.model).filter(
            sender_id=self.user.id, friendship_id=friendship_id)
        friendship.accept = True
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def delete(self, pk: Any) -> bool:
        item = self.db.query(self.model).filter(
            (self.model.sender_id == self.user.id) |
            (self.model.receiver_id == self.user.id)
        ).filter(
            self.model.id == pk).first()
        if item is None:
            raise base_exception.NotFound
        self.db.delete(item)
        return True


get_friendship_service = partial(_get_service, FriendshipService)


class ChatService(BaseService):
    model = Chat


get_chat_service = partial(_get_service, ChatService)
