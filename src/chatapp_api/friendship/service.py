"""Friendship services module."""
from dataclasses import dataclass

from src.chatapp_api.base.exceptions import NotFoundException
from src.chatapp_api.friendship.exceptions import (
    RequestAlreadySent,
    RequestWithYourself,
)
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.friendship.repository import FriendshipRepository
from src.chatapp_api.paginator import Page
from src.chatapp_api.user.service import UserService


@dataclass
class FrienshipService:
    """Friendship service class with its business logic."""

    user_service: UserService
    friendship_repository: FriendshipRepository

    async def list_pending_friendships(self, user_id: int) -> Page:
        """List of users pending requests."""
        user = await self.user_service.get_or_404(user_id)
        return await self.friendship_repository.find_pending_requests_for_user(
            user.id
        )

    async def list_friends(self, user_id: int) -> Page:
        """List of all friends user has."""
        return await self.friendship_repository.find_friends_for_user(user_id)

    async def _get_friendship_request_from_user(
        self, user_id: int, target_id: int
    ) -> Friendship | None:
        """Returns friendship request sent by target user."""
        return await (
            self.friendship_repository.find_friendship_request_of_user(
                user_id, target_id
            )
        )

    async def _get_friendship_with_user(
        self, user_id: int, target_id: int
    ) -> Friendship | None:
        """Returns matching friendship with target."""
        return await (
            self.friendship_repository.find_friendship_by_user_from_target(
                user_id, target_id
            )
        )

    async def get_friendship_with_user_or_404(
        self, user_id: int, target_id: int
    ) -> Friendship:
        """
        Returns friendship with user.
        Raises NotFound if users are not friends.
        """
        if (
            friendship := await self._get_friendship_with_user(
                user_id, target_id
            )
        ) is None:
            raise NotFoundException(
                "Friendship with given user has not been found."
            )
        return friendship

    async def _get_friendship_request_with_user_or_404(
        self, user_id: int, target_id: int
    ) -> Friendship:
        """
        Returns friendship request from target.
        Raises NotFound if user hasn't sent request.
        """
        if (
            friendship := await self._get_friendship_request_from_user(
                user_id, target_id
            )
        ) is None:
            raise NotFoundException(
                "Friendship request with given user has not been found."
            )
        return friendship

    async def send_to(self, user_id: int, target_id: int) -> Friendship:
        """Send friendship for target user"""
        if target_id == user_id:
            raise RequestWithYourself

        if await self.friendship_repository.exists_friendship_request(
            user_id, target_id
        ):
            raise RequestAlreadySent

        await self.user_service.get_or_404(target_id)

        friendship = Friendship(receiver_id=target_id, sender_id=user_id)
        self.friendship_repository.add(friendship)
        await self.friendship_repository.commit()
        return friendship

    async def approve(self, user_id: int, target_id: int) -> Friendship:
        """Service method for approving pending request"""
        friendship = await self._get_friendship_request_with_user_or_404(
            user_id, target_id
        )
        friendship.accepted = True
        self.friendship_repository.add(friendship)
        await self.friendship_repository.commit()
        await self.friendship_repository.refresh(friendship)
        return friendship

    async def decline(self, user_id: int, target_id: int) -> None:
        """Declines or terminates friendship with target user."""
        friendship = await self._get_friendship_request_with_user_or_404(
            user_id, target_id
        )

        await self.friendship_repository.delete(friendship)
        await self.friendship_repository.commit()
