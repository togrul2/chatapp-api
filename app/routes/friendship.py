"""Friendship related routes."""
from fastapi import APIRouter, Depends, status
from schemas.base import DetailMessage
from schemas.friendship import FriendshipRead, FriendshipReadWithSender
from schemas.user import UserRead
from services.friendship import FriendshipService, get_friendship_service

router = APIRouter(
    prefix="/api/friendship",
    tags=["friendship"],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": DetailMessage}},
)


@router.get("/requests", response_model=list[FriendshipReadWithSender])
async def get_pending_requests(
    service: FriendshipService = Depends(get_friendship_service),
):
    """Returns list of user's friendship requests pending for response."""
    return service.list_pending_friendships()


@router.get(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
)
async def get_request(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
):
    """Returns friendship with given user."""
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
):
    """
    Sends friendship request to the target user.
    - **target_id**: user id who receives the request.
    """
    return service.send_to(target_id)


@router.patch(
    "/requests/users/{target_id}",
    response_model=FriendshipRead,
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
)
async def accept_request(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
):
    return service.approve(target_id)


@router.delete(
    "/requests/users/{target_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": DetailMessage}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_friendship(
    target_id: int,
    service: FriendshipService = Depends(get_friendship_service),
):
    """Deletes friendship with given user if it exists."""
    service.decline(target_id)


@router.get("/friends", response_model=list[UserRead])
async def get_friends(
    service: FriendshipService = Depends(get_friendship_service),
):
    """Returns list of friends."""
    return service.list_friends()
