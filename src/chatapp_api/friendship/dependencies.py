"""Module with friendship dependencies."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.dependencies import get_db_session, get_paginator
from src.chatapp_api.friendship.repository import FriendshipRepository
from src.chatapp_api.friendship.service import FrienshipService
from src.chatapp_api.paginator import BasePaginator
from src.chatapp_api.user.dependencies import get_user_service
from src.chatapp_api.user.service import UserService


def get_friendship_repository(
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Friendship repository injector."""
    return FriendshipRepository(session, paginator)


def get_friendship_service(
    user_service: UserService = Depends(get_user_service),
    friendship_repository: FriendshipRepository = Depends(
        get_friendship_repository
    ),
):
    """Friendship service injector."""
    return FrienshipService(user_service, friendship_repository)
