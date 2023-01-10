"""Friendship related routes."""
from fastapi import APIRouter, Depends, status

from src.dependencies import (
    get_current_user_id_from_bearer,
    get_friendship_service,
    get_paginator,
)
from src.paginator import BasePaginator
from src.schemas.base import DetailMessage, PaginatedResponse
from src.schemas.friendship import FriendshipRead, FriendshipReadWithSender
from src.schemas.user import UserRead
from src.services.friendship import FriendshipService

router = APIRouter(
    prefix="/api/friendship",
    tags=["friendship"],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": DetailMessage}},
)


@router.get(
    "/requests", response_model=PaginatedResponse[FriendshipReadWithSender]
)
async def get_pending_requests(
    user_id: int = Depends(get_current_user_id_from_bearer),
    service: FriendshipService = Depends(get_friendship_service),
    paginator: BasePaginator[FriendshipReadWithSender] = Depends(
        get_paginator
    ),
):
    """Returns list of user's friendship requests pending for response."""
    service.set_user(user_id)
    service.set_paginator(paginator)
    return service.list_pending_friendships()


@router.get(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
)
async def get_request(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Returns friendship with given user."""
    service.set_user(user_id)
    return service.get_friendship_with_user_or_404(target_id)


@router.post(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={status.HTTP_409_CONFLICT: {"model": DetailMessage}},
    status_code=status.HTTP_201_CREATED,
)
async def send_request(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Sends friendship request to the target user.
    - **target_id**: user id who receives the request.
    """
    service.set_user(user_id)
    return service.send_to(target_id)


@router.patch(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
)
async def accept_request(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """
    Accepts frienship request from target.
    Returns 404 if there is no request from target user.
    """
    service.set_user(user_id)
    return service.approve(target_id)


@router.delete(
    "/requests/users/{target_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_friendship(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Deletes friendship with given user if it exists."""
    service.set_user(user_id)
    service.decline(target_id)


@router.get("/friends", response_model=PaginatedResponse[UserRead])
async def get_friends(
    user_id: int = Depends(get_current_user_id_from_bearer),
    service: FriendshipService = Depends(get_friendship_service),
    paginator: BasePaginator[UserRead] = Depends(get_paginator),
):
    """Returns list of friends."""
    service.set_user(user_id)
    service.set_paginator(paginator)
    return service.list_friends()
