"""User related routes."""
from fastapi import APIRouter, Depends, UploadFile, status

from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.routes import (
    BadCredentialsResponse,
    BadDataResponse,
    NotFoundResponse,
    RouteResponse,
)
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.user.dependencies import get_user_service
from src.chatapp_api.user.schemas import (
    UpdatePassword,
    UserBase,
    UserCreate,
    UserPartialUpdate,
    UserRead,
)
from src.chatapp_api.user.service import UserService

router = APIRouter(prefix="/api", tags=["user"])

DataConflictResponse: RouteResponse = {
    status.HTTP_409_CONFLICT: {
        "model": DetailMessage,
        "description": "Username or email is already taken",
    }
}


@router.get("/users", response_model=PaginatedResponse[UserRead])
async def list_users(
    keyword: str | None = None,
    user_service: UserService = Depends(get_user_service),
):
    """
    Lists users, also can perform search with keyword
    which will be compared to users' username and email.
    - **keyword**: keyword url parameter which will be
        used to find users with matching username or email.
    """
    return await user_service.list_users(keyword)


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    responses=BadDataResponse,
)
async def create_user(
    user_create_dto: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a user in database with given data:
    - **username**: unique name
    - **email**: unique email address
    - **first_name**: first name of a user
    - **last_name**: last name of a user
    - **password**: password
    """
    return await user_service.create_user(
        user_create_dto.username,
        user_create_dto.email,
        user_create_dto.first_name,
        user_create_dto.last_name,
        user_create_dto.password,
    )


@router.get(
    "/users/me",
    response_model=UserRead,
    responses=BadCredentialsResponse,
)
async def get_auth_user(
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """Returns authenticated user's data.
    Returns 401 error code if unauthenticated."""
    return await user_service.get_or_401(user_id)


@router.put(
    "/users/me",
    response_model=UserRead,
    responses=DataConflictResponse | BadDataResponse | BadCredentialsResponse,
)
async def update_auth_user(
    user_update_dto: UserBase,
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """
    Updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    """
    return await user_service.update_user(
        user_id,
        user_update_dto.username,
        user_update_dto.email,
        user_update_dto.first_name,
        user_update_dto.last_name,
    )


@router.patch(
    "/users/me",
    response_model=UserRead,
    responses=DataConflictResponse | BadDataResponse | BadCredentialsResponse,
)
async def partial_update_auth_user(
    user_partial_update_dto: UserPartialUpdate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """
    Partially updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    """
    return await user_service.update_user(
        user_id,
        user_partial_update_dto.username,
        user_partial_update_dto.email,
        user_partial_update_dto.first_name,
        user_partial_update_dto.last_name,
    )


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=BadCredentialsResponse,
)
async def delete_auth_user(
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """Deletes authenticated user's data or returns 401 if unauthenticated."""
    await user_service.delete_user(user_id)


@router.post(
    "/users/me/image",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "wrong file type (MIME different than jpeg or png)",
        },
        **BadCredentialsResponse,
    },
)
async def upload_profile_picture(
    profile_picture: UploadFile,
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """
    Upload image for authenticated user.
    - **image**: image file.
    """
    return await user_service.update_profile_picture(user_id, profile_picture)


@router.delete(
    "/users/me/image",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=BadCredentialsResponse,
)
async def remove_profile_picture(
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    """Remove profile picture for authenticated user."""
    return await user_service.remove_profile_picture(user_id)


@router.post(
    "/users/me/change-password",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Old password is incorrect",
        },
        **BadCredentialsResponse,
    },
)
async def change_password(
    passwords: UpdatePassword,
    user_id: int = Depends(get_current_user_id_from_bearer),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.update_user_password(
        user_id, passwords.old_password, passwords.new_password
    )


@router.get(
    "/users/{user_id:int}",
    response_model=UserRead,
    responses=NotFoundResponse,
)
async def get_user_by_id(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    """
    return await user_service.get_or_404(user_id)


@router.get(
    "/users/{username:str}",
    response_model=UserRead,
    responses=NotFoundResponse,
)
async def get_user_by_username(
    username: str, user_service: UserService = Depends(get_user_service)
):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    """
    return await user_service.get_by_username_or_404(username)
