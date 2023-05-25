"""Module with friendship repository"""
from dataclasses import dataclass

from sqlalchemy import Row, and_, exists, or_, select
from sqlalchemy.orm import defer, joinedload

from src.chatapp_api.base.repository import BaseRepository
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.paginator import BasePaginator, Page
from src.chatapp_api.user.models import User


@dataclass
class FriendshipRepository(BaseRepository[Friendship]):
    """Friendship repository class"""

    paginator: BasePaginator

    async def find_pending_requests_for_user(
        self, user_id: int
    ) -> Page[Friendship]:
        """Returns pending requests for given user"""
        return await self.paginator.get_page_for_model(
            select(Friendship)
            .options(
                joinedload(Friendship.sender), defer(Friendship.sender_id)
            )
            .where(
                and_(
                    Friendship.receiver_id == user_id,
                    Friendship.accepted == False,  # noqa: E712
                )
            )
        )

    async def find_friends_for_user(self, user_id: int) -> Page[Row]:
        """Returns list of friends for user."""
        sent_query = (
            select(User)
            .join(Friendship, User.id == Friendship.receiver_id)
            .where(
                and_(
                    Friendship.sender_id == user_id,
                    Friendship.accepted == True,  # noqa: E712
                )
            )
        )

        received_query = (
            select(User)
            .join(Friendship, User.id == Friendship.sender_id)
            .where(
                and_(
                    Friendship.receiver_id == user_id,
                    Friendship.accepted == True,  # noqa: E712
                )
            )
        )

        return await self.paginator.get_page_for_rows(
            sent_query.union(received_query)
        )

    async def find_friendship_request_of_user(
        self, user_id: int, target_id: int
    ) -> Friendship | None:
        """Returns friendship target request for user."""
        return await self.session.scalar(
            select(Friendship).where(
                and_(
                    Friendship.sender_id == target_id,
                    Friendship.receiver_id == user_id,
                    Friendship.accepted == False,  # noqa: E712
                )
            )
        )

    async def find_friendship_by_user_from_target(
        self, user_id: int, target_id: int
    ) -> Friendship | None:
        """Returns friendship between two users."""
        return await self.session.scalar(
            select(Friendship)
            .where(Friendship.accepted == True)  # noqa: E712
            .where(
                or_(
                    and_(
                        Friendship.sender_id == user_id,
                        Friendship.receiver_id == target_id,
                    ),
                    and_(
                        Friendship.sender_id == target_id,
                        Friendship.receiver_id == user_id,
                    ),
                )
            )
        )

    async def exists_friendship_request(
        self, user1_id: int, user2_id: int
    ) -> bool:
        """Returns whether two users are friends or not"""
        # Friendship request sent by one of two users
        return (
            await self.session.scalar(
                exists()
                .where(
                    or_(
                        and_(
                            Friendship.sender_id == user2_id,
                            Friendship.receiver_id == user1_id,
                        ),
                        and_(
                            Friendship.sender_id == user1_id,
                            Friendship.receiver_id == user2_id,
                        ),
                    )
                )
                .select()
            )
        ) or False
