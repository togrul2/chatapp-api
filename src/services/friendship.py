"""Friendship services module."""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from src.exceptions.base import http_404_not_found
from src.exceptions.friendship import RequestAlreadySent, RequestWithYourself
from src.models.user import Friendship, User
from src.paginator import BasePaginator
from src.schemas.base import PaginatedResponse
from src.schemas.friendship import FriendshipReadWithSender
from src.schemas.user import UserRead
from src.services import base as base_services
from src.services import user as user_services


async def list_pending_friendships(
    session: AsyncSession, user_id: int, paginator: BasePaginator | None = None
) -> list[Friendship] | PaginatedResponse[FriendshipReadWithSender]:
    """List of users pending requests."""
    user = await user_services.get_or_404(session, user_id)
    query = (
        select(Friendship)
        .options(joinedload(Friendship.sender), defer("sender_id"))
        .where(
            (Friendship.receiver_id == user.id)
            & (Friendship.accepted == None)  # noqa: E711
        )
    )

    if paginator:
        return await paginator.get_paginated_response_for_model(query)

    return (await session.scalars(query)).all()


async def list_friends(
    session: AsyncSession, user_id: int, paginator: BasePaginator | None = None
) -> list[User] | PaginatedResponse[UserRead]:
    """List of all friends user has."""
    sent_query = (
        select(User)
        .join(Friendship, User.id == Friendship.receiver_id)
        .where(
            (Friendship.sender_id == user_id)
            & (Friendship.accepted == True)  # noqa: E712
        )
    )

    received_query = (
        select(User)
        .join(Friendship, User.id == Friendship.sender_id)
        .where(
            (Friendship.receiver_id == user_id)
            & (Friendship.accepted == True)  # noqa: E712
        )
    )

    query = sent_query.union(received_query)

    if paginator:
        return await paginator.get_paginated_response_for_rows(query)

    return (await session.scalars(query)).all()


async def _get_friendship_request_with_user(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship | None:
    """Returns matching friendship request with target."""
    query = select(Friendship).where(
        (Friendship.sender_id == target_id)
        & (Friendship.receiver_id == user_id)
        & (Friendship.accepted == None)  # noqa: E711
    )
    return await session.scalar(query)


async def _get_friendship_with_user(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship | None:
    """Returns matching friendship with target."""
    query = select(Friendship).where(
        (
            (Friendship.sender_id == user_id)
            & (Friendship.receiver_id == target_id)
        )
        | (
            (Friendship.sender_id == target_id)
            & (Friendship.receiver_id == user_id)
        )
    )

    return await session.scalar(query)


async def get_friendship_with_user_or_404(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """
    Returns friendship with user.
    Raises NotFound if users are not friends.
    """
    if (
        friendship := await _get_friendship_with_user(
            session, user_id, target_id
        )
    ) is None:
        raise http_404_not_found(
            "Friendship with given user has not been found."
        )
    return friendship


async def get_friendship_request_with_user_or_404(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """
    Returns friendship request from target.
    Raises NotFound if user hasn't sent request.
    """
    if (
        friendship := await _get_friendship_request_with_user(
            session, user_id, target_id
        )
    ) is None:
        raise http_404_not_found(
            "Friendship request with given user has not been found."
        )
    return friendship


async def send_to(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """Send friendship for target user"""
    if target_id == user_id:
        raise RequestWithYourself

    if (
        await _get_friendship_with_user(session, user_id, target_id)
        is not None
    ):
        raise RequestAlreadySent

    await user_services.get_or_404(session, target_id)

    return await base_services.create(
        session, Friendship(receiver_id=target_id, sender_id=user_id)
    )


async def approve(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """Service method for approving pending request"""
    friendship = await get_friendship_request_with_user_or_404(
        session, user_id, target_id
    )
    return await base_services.update(session, friendship, {"accepted": True})


async def decline(session: AsyncSession, user_id: int, target_id: int) -> None:
    """Declines or terminates friendship with target user."""
    friendship = await get_friendship_request_with_user_or_404(
        session, user_id, target_id
    )

    await session.execute(
        delete(Friendship).where(Friendship.id == friendship.id)
    )
    await session.commit()
