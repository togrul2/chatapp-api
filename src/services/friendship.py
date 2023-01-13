"""Friendship services module."""
from sqlalchemy import delete, select
from sqlalchemy.orm import defer, joinedload

from src.exceptions.base import NotFound
from src.exceptions.friendship import RequestAlreadySent, RequestWithYourself
from src.models.user import Friendship, User
from src.services.base import CreateUpdateDeleteService
from src.services.user import UserService


class FriendshipService(CreateUpdateDeleteService[Friendship]):
    """Friendship service class with db manipulation methods."""

    user_service: UserService
    user: User
    model = Friendship

    async def set_user(self, user_id: int):
        """Sets user model and service based on given user id."""
        self.user_service = UserService(self.session)
        self.user = await self.user_service.get_or_401(user_id)

    async def list_pending_friendships(self):
        """List of users pending requests"""
        query = (
            select(self.model)
            .options(joinedload(self.model.sender), defer("sender_id"))
            .where(
                (self.model.receiver_id == self.user.id)
                & (self.model.accepted == None)  # noqa: E711
            )
        )

        if self._paginator:
            return await self._paginator.get_paginated_response(query)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_friends(self):
        """List of all friends user has."""
        sent = (
            select(User)
            .join(self.model, User.id == self.model.receiver_id)
            .where(
                (self.model.sender_id == self.user.id)
                & (self.model.accepted == True)  # noqa: E712
            )
        )

        received = (
            select(User)
            .join(self.model, User.id == self.model.sender_id)
            .where(
                (self.model.receiver_id == self.user.id)
                & (self.model.accepted == True)  # noqa: E712
            )
        )

        query = sent.union(received)

        if self._paginator:
            return await self._paginator.get_paginated_response(query)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def _get_friendship_request(self, target_id: int):
        """Returns matching friendship request with target."""
        query = select(self.model).where(
            (self.model.sender_id == target_id)
            & (self.model.receiver_id == self.user.id)
            & (self.model.accepted == None)  # noqa: E711
        )
        result = await self.session.execute(query)
        return result.scalar()

    async def _get_friendship(self, target_id: int):
        """Returns matching friendship with target."""
        query = select(self.model).where(
            (
                (self.model.sender_id == self.user.id)
                & (self.model.receiver_id == target_id)
            )
            | (
                (self.model.sender_id == target_id)
                & (self.model.receiver_id == self.user.id)
            )
        )

        result = await self.session.execute(query)
        return result.scalar()

    async def get_friendship_with_user_or_404(self, target_id: int):
        """
        Returns friendship with user.
        Raises NotFound if users are not friends.
        """
        if (friendship := await self._get_friendship(target_id)) is None:
            raise NotFound
        return friendship

    async def get_friendship_request_with_user_or_404(self, target_id: int):
        """
        Returns friendship request from target.
        Raises NotFound if user hasn't sent request.
        """
        if (
            friendship := await self._get_friendship_request(target_id)
        ) is None:
            raise NotFound
        return friendship

    async def send_to(self, target_id: int):
        """Send friendship for target user"""
        if target_id == self.user.id:
            raise RequestWithYourself

        if await self._get_friendship(target_id) is not None:
            raise RequestAlreadySent

        await self.user_service.get_or_404(target_id)

        return await self.create(
            {"receiver_id": target_id, "sender_id": self.user.id}
        )

    async def approve(self, target_id: int):
        """Service method for approving pending request"""
        friendship = await self.get_friendship_request_with_user_or_404(
            target_id
        )
        return await self.update(friendship.id, {"accepted": True})

    async def decline(self, target_id: int) -> None:
        """Declines or terminates friendship with target user."""
        friendship = await self.get_friendship_request_with_user_or_404(
            target_id
        )
        query = delete(Friendship).where(Friendship.id == friendship.id)
        await self.session.execute(query)
        await self.session.commit()
