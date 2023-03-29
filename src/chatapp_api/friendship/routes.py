"""Friendship related routes."""
from fastapi import APIRouter, Depends, status

from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.friendship.dependencies import get_friendship_service
from src.chatapp_api.friendship.schemas import (
    FriendshipRead,
    FriendshipReadWithSender,
)
from src.chatapp_api.friendship.service import FrienshipService
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
    friendship_service: FrienshipService = Depends(get_friendship_service),
):
    """Returns list of user's friendship requests pending for response."""
    return await friendship_service.list_pending_friendships(user_id)


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
    friendship_service: FrienshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Sends friendship request to the target user.
    - **target_id**: user id who receives the request.
    """
    return await friendship_service.send_to(user_id, target_id)


@router.post(
    "/requests/users/{target_id}/accept",
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
    friendship_service: FrienshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Accepts friendship request from target.
    Returns 404 if there is no request from target user.
    """
    return await friendship_service.approve(user_id, target_id)


@router.post(
    "/requests/users/{target_id}/decline",
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
    friendship_service: FrienshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Deletes friendship with given user if it exists."""
    await friendship_service.decline(user_id, target_id)


@router.get("/friends", response_model=PaginatedResponse[UserRead])
async def list_friends(
    user_id: int = Depends(get_current_user_id_from_bearer),
    friendship_service: FrienshipService = Depends(get_friendship_service),
):
    """Returns list of friends."""
    return await friendship_service.list_friends(user_id)


@router.get(
    "/friends/{target_id}",
    response_model=FriendshipRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Friendship request from given user is not found.",
        }
    },
)
async def get_frienship(
    target_id: int,
    friendship_service: FrienshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Returns friendship with given user."""
    return await friendship_service.get_friendship_with_user_or_404(
        user_id, target_id
    )
