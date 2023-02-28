"""User related routes."""
import uuid
from urllib import parse

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api import utils
from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.dependencies import (
    get_db_session,
    get_paginator,
    get_staticfiles_manager,
)
from src.chatapp_api.paginator import BasePaginator
from src.chatapp_api.staticfiles import BaseStaticFilesManager
from src.chatapp_api.user import services as user_services
from src.chatapp_api.user.exceptions import BadImageFileMIME
from src.chatapp_api.user.schemas import (
    UserBase,
    UserCreate,
    UserPartialUpdate,
    UserRead,
)

router = APIRouter(prefix="/api", tags=["user"])


@router.get("/users", response_model=PaginatedResponse[UserRead])
async def list_users(
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """
    Lists users, also can perform search with keyword
    which will be compared to users' username and email.
    - **keyword**: keyword url parameter which will be
        used to find users with matching username or email.
    """
    return await user_services.list_users(session, paginator, keyword)


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Taken or invalid properties.",
        }
    },
)
async def create_user(
    payload: UserCreate, session: AsyncSession = Depends(get_db_session)
):
    """
    Create a user in database with given data:
    - **username**: unique name
    - **email**: unique email address
    - **first_name**: first name of a user
    - **last_name**: last name of a user
    - **password**: password
    """
    return await user_services.create_user(session, payload)


@router.get(
    "/users/me",
    response_model=UserRead,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def get_auth_user(
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Returns authenticated user's data.
    Returns 401 error code if unauthenticated."""
    return await user_services.get_or_401(session, user_id)


@router.put(
    "/users/me",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Taken or invalid properties",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def update_auth_user(
    data: UserBase,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    """
    return await user_services.update_user(session, user_id, data)


@router.patch(
    "/users/me",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Taken or invalid properties",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def partial_update_auth_user(
    data: UserPartialUpdate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Partially updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    """
    return await user_services.update_user(session, user_id, data)


@router.delete(
    "/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def delete_auth_user(
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Deletes authenticated user's data or returns 401 if unauthenticated."""
    await user_services.delete_user(session, user_id)


@router.post(
    "/users/me/image",
    response_model=UserRead,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "wrong file type (MIME different than jpeg or png)",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def upload_profile_picture(
    profile_picture: UploadFile,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
    staticfiles_manager: BaseStaticFilesManager = Depends(
        get_staticfiles_manager
    ),
):
    """
    Upload image for authenticated user.
    - **image**: image file.
    """
    if profile_picture.content_type not in ("image/jpeg", "image/png"):
        raise BadImageFileMIME

    path = user_services.get_profile_pictures_dir(user_id)

    # Adding uuid4 to filename
    file_fullname = utils.split_path(profile_picture.filename)[-1]
    filename, ext = file_fullname.rsplit(".", 1)
    filename = f"{filename}_{uuid.uuid4()}"
    profile_picture.filename = ".".join([filename, ext])

    # loading file into storage and generating web link
    staticfiles_manager.load(path, profile_picture)
    url = staticfiles_manager.get_url(
        parse.urljoin(path, profile_picture.filename)
    )

    return await user_services.update_profile_picture(session, user_id, url)


@router.delete(
    "/users/me/image",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad access token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Can't find authenticated user.",
        },
    },
)
async def remove_profile_picture(
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Remove profile picture for authenticated user."""
    return await user_services.remove_profile_picture(session, user_id)


@router.get(
    "/users/{user_id:int}",
    response_model=UserRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "User with given id is not found.",
        }
    },
)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    """
    return await user_services.get_or_404(session, user_id)


@router.get(
    "/users/{username:str}",
    response_model=UserRead,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "User with given username is not found.",
        }
    },
)
async def get_user_by_username(
    username: str, session: AsyncSession = Depends(get_db_session)
):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    """
    return await user_services.get_by_username_or_404(session, username)
