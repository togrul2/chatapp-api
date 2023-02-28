"""Friendship related routes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.dependencies import get_db_session, get_paginator
from src.chatapp_api.friendship import services as friendship_services
from src.chatapp_api.friendship.schemas import (
    FriendshipRead,
    FriendshipReadWithSender,
)
from src.chatapp_api.paginator import BasePaginator
from src.chatapp_api.user.schemas import UserRead

router = APIRouter(
    prefix="/api/friendship",
    tags=["friendship"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Authentication token is expired or incorrect.",
        }
    },
)


@router.get(
    "/requests", response_model=PaginatedResponse[FriendshipReadWithSender]
)
async def get_pending_requests(
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns list of user's friendship requests pending for response."""
    return await friendship_services.list_pending_friendships(
        session, user_id, paginator
    )


@router.get(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Friendship request from given user is not found.",
        }
    },
)
async def get_request(
    target_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Returns friendship with given user."""
    return await friendship_services.get_friendship_with_user_or_404(
        session, user_id, target_id
    )


@router.post(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "Can't send request to yourself.",
        }
    },
    status_code=status.HTTP_201_CREATED,
)
async def send_request(
    target_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Sends friendship request to the target user.
    - **target_id**: user id who receives the request.
    """
    return await friendship_services.send_to(session, user_id, target_id)


@router.patch(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Friendship request is not found",
        }
    },
)
async def accept_request(
    target_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Accepts friendship request from target.
    Returns 404 if there is no request from target user.
    """
    return await friendship_services.approve(session, user_id, target_id)


@router.delete(
    "/requests/users/{target_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Friendship request is not found",
        }
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_friendship(
    target_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Deletes friendship with given user if it exists."""
    await friendship_services.decline(session, user_id, target_id)


@router.get("/friends", response_model=PaginatedResponse[UserRead])
async def list_friends(
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns list of friends."""
    return await friendship_services.list_friends(session, user_id, paginator)
