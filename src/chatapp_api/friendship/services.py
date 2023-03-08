"""Friendship services module."""
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload

from src.chatapp_api.base import services as base_services
from src.chatapp_api.base.exceptions import NotFoundException
from src.chatapp_api.friendship.exceptions import (
    RequestAlreadySent,
    RequestWithYourself,
)
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.paginator import BasePaginator, PaginatedResponseDict
from src.chatapp_api.user import services as user_services
from src.chatapp_api.user.models import User


async def list_pending_friendships(
    session: AsyncSession, user_id: int, paginator: BasePaginator
) -> PaginatedResponseDict:
    """List of users pending requests."""
    user = await user_services.get_or_404(session, user_id)
    query = (
        select(Friendship)
        .options(joinedload(Friendship.sender), defer(Friendship.sender_id))
        .where(
            and_(
                Friendship.receiver_id == user.id,
                Friendship.accepted == False,  # noqa: E712
            )
        )
    )

    return await paginator.get_paginated_response_for_model(query)


async def list_friends(
    user_id: int, paginator: BasePaginator
) -> PaginatedResponseDict:
    """List of all friends user has."""
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

    query = sent_query.union(received_query)

    return await paginator.get_paginated_response_for_rows(query)


async def _get_friendship_request_from_user(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship | None:
    """Returns friendship request sent by target user."""
    query = select(Friendship).where(
        and_(
            Friendship.sender_id == target_id,
            Friendship.receiver_id == user_id,
            Friendship.accepted == False,  # noqa: E712
        )
    )
    return await session.scalar(query)


async def _get_friendship_with_user(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship | None:
    """Returns matching friendship with target."""
    query = (
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
        raise NotFoundException(
            "Friendship with given user has not been found."
        )
    return friendship


async def _get_friendship_request_with_user_or_404(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """
    Returns friendship request from target.
    Raises NotFound if user hasn't sent request.
    """
    if (
        friendship := await _get_friendship_request_from_user(
            session, user_id, target_id
        )
    ) is None:
        raise NotFoundException(
            "Friendship request with given user has not been found."
        )
    return friendship


async def send_to(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """Send friendship for target user"""
    if target_id == user_id:
        raise RequestWithYourself

    # Friendship request sent by one of two users
    friendship_request = select(Friendship).where(
        or_(
            and_(
                Friendship.sender_id == target_id,
                Friendship.receiver_id == user_id,
            ),
            and_(
                Friendship.sender_id == user_id,
                Friendship.receiver_id == target_id,
            ),
        )
    )

    if await session.scalar(friendship_request) is not None:
        raise RequestAlreadySent

    await user_services.get_or_404(session, target_id)

    return await base_services.create(
        session, Friendship(receiver_id=target_id, sender_id=user_id)
    )


async def approve(
    session: AsyncSession, user_id: int, target_id: int
) -> Friendship:
    """Service method for approving pending request"""
    friendship = await _get_friendship_request_with_user_or_404(
        session, user_id, target_id
    )
    friendship.accepted = True
    session.add(friendship)
    await session.commit()
    await session.refresh(friendship)
    return friendship


async def decline(session: AsyncSession, user_id: int, target_id: int) -> None:
    """Declines or terminates friendship with target user."""
    friendship = await _get_friendship_request_with_user_or_404(
        session, user_id, target_id
    )

    await session.delete(friendship)
    await session.commit()
