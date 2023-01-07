"""Friendship services module."""
from sqlalchemy.orm import defer, joinedload

import config
from exceptions import base as base_exceptions
from exceptions import friendship as friendship_exceptions
from models.user import Friendship, User
from schemas.friendship import FriendshipCreate
from services.base import CreateUpdateDeleteService
from services.user import UserService


class FriendshipService(CreateUpdateDeleteService):
    """Friendship service class with db manipulation methods."""

    user_service: UserService
    user: User
    model = Friendship

    def set_user(self, user_id: int):
        self.user_service = UserService(self.session)
        self.user = self.user_service.get_or_401(user_id)

    def list_pending_friendships(self):
        """List of users pending requests"""
        query = (
            self.session.query(self.model)
            .options(
                joinedload(self.model.sender), defer(self.model.sender_id)
            )
            .filter(
                (self.model.receiver_id == self.user.id)
                & (self.model.accepted == None)  # noqa: E711
            )
        )
        return query.all()

    def list_friends(self, page: int = 1, page_size: int = config.PAGE_SIZE_DEFAULT):
        """List of all friends user has."""
        sent = (
            self.session.query(User)
            .join(self.model, User.id == self.model.receiver_id)
            .filter(
                (self.model.sender_id == self.user.id)
                & (self.model.accepted == True)  # noqa: E712
            )
        )

        received = (
            self.session.query(User)
            .join(self.model, User.id == self.model.sender_id)
            .filter(
                (self.model.receiver_id == self.user.id)
                & (self.model.accepted == True)  # noqa: E712
            )
        )

        query = sent.union(received)

        if self.paginator:
            self.paginator.paginate(query, page, page_size)

        return query.all()

    def _get_friendship_request(self, target_id: int):
        """Returns matching friendship request with target."""
        query = self.session.query(self.model).filter(
            (self.model.sender_id == target_id) &
            (self.model.receiver_id == self.user.id) &
            (self.model.accepted == None)  # noqa: E712
        )
        return query.first()

    def _get_friendship(self, target_id: int):
        """Returns matching friendship with target."""
        query = self.session.query(self.model).filter(
            (
                (self.model.sender_id == self.user.id)
                & (self.model.receiver_id == target_id)
            )
            | (
                (self.model.sender_id == target_id)
                & (self.model.receiver_id == self.user.id)
            )
        )
        return query.first()

    def get_friendship_with_user_or_404(self, target_id: int):
        """
        Returns friendship with user.
        Raises NotFound if users are not friends.
        """
        if (friendship := self._get_friendship(target_id)) is None:
            raise base_exceptions.NotFound
        return friendship

    def get_friendship_request_with_user_or_404(self, target_id: int):
        """
        Returns friendship request from target.
        Raises NotFound if user hasn't sent request.
        """
        if (friendship := self._get_friendship_request(target_id)) is None:
            raise base_exceptions.NotFound
        return friendship

    def send_to(self, target_id: int) -> Friendship:
        """Send friendship for target user"""
        if target_id == self.user.id:
            raise friendship_exceptions.RequestWithYourself

        if self._get_friendship(target_id) is not None:
            raise friendship_exceptions.RequestAlreadySent

        self.user_service.get_or_404(target_id)

        return self.create(
            FriendshipCreate(receiver_id=target_id, sender_id=self.user.id)
        )

    def approve(self, target_id: int) -> Friendship:
        """Service method for approving pending request"""
        friendship = self.get_friendship_request_with_user_or_404(target_id)
        friendship.accepted = True
        self.session.commit()
        self.session.refresh(friendship)
        return friendship

    def decline(self, target_id: int) -> None:
        """Declines or terminates friendship with target user."""
        friendship = self.get_friendship_request_with_user_or_404(target_id)
        self.session.delete(friendship)
        self.session.commit()
