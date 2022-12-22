"""Friendship services module."""
from fastapi import Depends
from sqlalchemy.orm import Session

import authentication
from db import get_db
from models import Friendship, User
from services.base import CreateUpdateDeleteService
from services.user import UserService
from schemas.friendship import FriendshipCreate
from exceptions import (base as base_exceptions,
                        friendship as friendship_exceptions)


class FriendshipService(CreateUpdateDeleteService):
    """Friendship service class with db manipulation methods."""
    model = Friendship

    def __init__(self, db: Session, user_id: int):
        super().__init__(db)
        self.user_service = UserService(self.db)
        self.user = self.user_service.get_or_401(user_id)

    def list_pending_friendships(self):
        """List of users pending requests"""
        return self.db.query(self.model).filter(
            (self.model.receiver_id == self.user.id) &
            (self.model.accepted == None)  # noqa: E711
        ).all()

    def list_friends(self):
        """List of all friends user has."""
        # Friends where auth user send request
        q1 = (self.db.query(User)
              .join(self.model, User.id == self.model.receiver_id)
              .filter((self.model.sender_id == self.user.id) &
                      (self.model.accepted == True)))  # noqa: E712

        # Friends where target users send request
        q2 = (self.db.query(User)
              .join(self.model, User.id == self.model.sender_id)
              .filter((self.model.receiver_id == self.user.id) &
                      (self.model.accepted == True)))  # noqa: E712

        return q1.union(q2).all()

    def _get_friendship_request_query(self, target_id: int):
        """Returns query matching friendship request."""
        return self.db.query(self.model).filter(
            (
                    (self.model.sender_id == self.user.id) &
                    (self.model.receiver_id == target_id)
            ) | (
                    (self.model.sender_id == target_id) &
                    (self.model.receiver_id == self.user.id)
            )
        )

    def _get_friendship_request(self, target_id: int):
        """Returns matching friendship request."""
        return self._get_friendship_request_query(target_id).first()

    def _get_friendship(self, target_id: int):
        """
        Returns query matching friendship.
        Besides finding a record, also checks if it is accepted by receiver.
        """
        return self._get_friendship_request_query(target_id).first()

    def _get_friendship_with_user(self, target_id: int):
        """Returns friendship with user or None if users are not friends."""
        return self._get_friendship_request(target_id)

    def get_friendship_with_user_or_404(self, target_id: int):
        """
        Returns friendship with user.
        Raises NotFound if users are not friends.
        """
        if (friendship := self._get_friendship(target_id)) is None:
            raise base_exceptions.NotFound
        return friendship

    def create(self, target_id: int) -> Friendship:
        """Send friendship for target user """
        self.user_service.get_or_404(target_id)

        if target_id == self.user.id:
            raise friendship_exceptions.RequestWithYourself

        if self._get_friendship_request(target_id) is not None:
            raise friendship_exceptions.RequestAlreadySent

        return super().create(FriendshipCreate(
            receiver_id=target_id, sender_id=self.user.id, accepted=None
        ))

    def approve(self, target_id: int) -> Friendship:
        """Service method for approving pending request"""
        friendship = self.db.query(self.model).filter(
            (self.model.receiver_id == self.user.id) &
            (self.model.sender_id == target_id)).first()
        if friendship is None:
            raise base_exceptions.NotFound

        friendship.accepted = True
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def delete(self, target_id: int) -> None:
        """Deletes friendship with target user."""
        friendship = self._get_friendship_with_user(target_id)

        if friendship is None:
            raise base_exceptions.NotFound

        self.db.delete(friendship)
        self.db.commit()


def get_friendship_service(
        db: Session = Depends(get_db),
        user_id: int = Depends(authentication.get_current_user_id)):
    """Dependency for friendship service."""
    yield FriendshipService(db, user_id)
