"""User related routes."""
import uuid
from urllib import parse
from typing import List, Optional

from fastapi import APIRouter, Depends, status, Form, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

import authentication
from schemas.user import UserCreate, UserRead, UserBase, UserPartialUpdate
from schemas.base import DetailMessage
from services.user import (UserService, get_user_service, get_pfp_path)
from staticfiles import BaseStaticFilesManager, get_staticfiles_manager

router = APIRouter(prefix='/api', tags=["user"])


@router.post('/token', status_code=status.HTTP_201_CREATED,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {
                     'model': DetailMessage
                 }
             })
async def token(user_service: UserService = Depends(get_user_service),
                credentials: OAuth2PasswordRequestForm = Depends()):
    """
    Creates access and refresh token for user:
    - **username**: username of a user.
    - **password**: password of a user.
    \f
    :param credentials: User's credentials.
    :param user_service: service providing user model operations.
    """
    user = user_service.authenticate_user(credentials.username,
                                          credentials.password)

    return {
        'access_token': authentication.create_access_token(user.id),
        'refresh_token': authentication.create_refresh_token(user.id)
    }


@router.post('/refresh', status_code=status.HTTP_201_CREATED,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {
                     'model': DetailMessage
                 }
             })
async def refresh(refresh_token: str = Form(),
                  user_service: UserService = Depends(get_user_service)):
    """
    Creates access & refresh tokens based on refresh token.
    - **refresh_token**: refresh token
    \f
    :param refresh_token: refresh token of a user.
    :param user_service: service providing user model operations.
    """
    return user_service.refresh_tokens(refresh_token)


@router.get('/users', response_model=List[UserRead])
async def get_users(keyword: Optional[str] = None,
                    user_service: UserService = Depends(get_user_service)):
    """
    Lists users, also can perform search with keyword
    which will be compared to users' username and password.
    - **keyword**: keyword url parameter which will be
        used to find users with matching username or password.
    \f
    :param keyword: query param for user search.
    :param user_service: service providing user model operations.
    :return: List of searched users.
    """
    # If we have a present keyword, we would filter result,
    # otherwise send all data.
    if keyword:
        expression = keyword + '%'
        return user_service.filter_by_username_or_email(expression, expression)

    return user_service.all()


@router.post('/users', status_code=status.HTTP_201_CREATED,
             response_model=UserRead,
             responses={
                 status.HTTP_400_BAD_REQUEST: {
                     'model': DetailMessage
                 }
             })
async def create_user(data: UserCreate,
                      user_service: UserService = Depends(get_user_service)):
    """
    Create a user in database with given data:
    - **username**: unique name
    - **email**: unique email address
    - **first_name**: first name of a user
    - **last_name**: last name of a user
    - **password**: password
    \f
    :param data: User input.
    :param user_service: service providing user model operations.
    """
    return user_service.create(data)


@router.get('/users/me', response_model=UserRead)
async def get_auth_user(
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Returns authenticated user's data or returns 401 if unauthenticated.
    \f
    :param user_id: id of authenticated user.
    :param user_service: service providing user model operations.
    :return: Auth user's data.
    """
    return user_service.get_or_404(user_id)


@router.put('/users/me', response_model=UserRead,
            responses={
                status.HTTP_400_BAD_REQUEST: {
                    'model': DetailMessage
                }
            })
async def update_auth_user(
        data: UserBase,
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    \f
    :param data: request's body
    :param user_id: id of authenticated user
    :param user_service: service providing user model operations.
    :return: Updated user data
    """

    return user_service.update(user_id, data)


@router.patch('/users/me', response_model=UserRead,
              responses={
                  status.HTTP_400_BAD_REQUEST: {
                      'model': DetailMessage
                  }
              })
async def partial_update_auth_user(
        data: UserPartialUpdate,
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Partially updates authenticated user's data,
    - **username**: username of a user, must be at least 6 characters
    - **email**: email address of a user, must be a valid email
    - **first_name**: first name of a user, must be at least 2 characters
    - **last_name**: last name of a user, must be at least 2 characters
    \f
    :param data: request's body
    :param user_id: id of authenticated user
    :param user_service: service providing user model operations.
    :return: Updated user data
    """
    return user_service.update(user_id, data)


@router.post('/users/me/image', response_model=UserRead)
async def upload_profile_picture(
        profile_picture: UploadFile,
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service),
        staticfiles_manager: BaseStaticFilesManager = Depends(
            get_staticfiles_manager)):
    """
    Upload image for authenticated user.
    - **image**: image file.
    \f
    :param profile_picture: Profile image user uploads.
    :param user_id: id of an authenticated user.
    :param user_service: service providing user model operations.
    :param staticfiles_manager: staticfiles manager dependency
    :return: user info.
    """
    if profile_picture.content_type not in ('image/jpeg', 'image/png'):
        raise HTTPException(
            status_code=400,
            detail="Wrong file type, only jpeg and png files are allowed"
        )

    path = get_pfp_path(user_id)

    # Adding uuid4 to filename
    filename, ext = profile_picture.filename.rsplit('.', 1)
    filename = f'{filename}_{uuid.uuid4()}'
    profile_picture.filename = '.'.join([filename, ext])

    # loading file into storage and generating web link
    staticfiles_manager.load(path, profile_picture)
    url = staticfiles_manager.get_url(
        parse.urljoin(path, profile_picture.filename))

    return user_service.update_profile_picture(user_id, url)


@router.delete('/users/me/image', status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile_picture(
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Remove profile picture for authenticated user.
    \f
    :param user_id: id of an authenticated user.
    :param user_service: service providing user model operations.
    """
    user_service.remove_profile_picture(user_id)


@router.delete('/users/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_auth_user(
        user_id: int = Depends(authentication.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Deletes authenticated user's data or returns 401 if unauthenticated.
    \f
    Here we return response with empty body, so no return value needed.
    :param user_id: id of authenticated user
    :param user_service: service providing user model operations.
    """
    user_service.delete(user_id)


@router.get('/users/{user_id:int}', response_model=UserRead,
            responses={
                status.HTTP_404_NOT_FOUND: {
                    'model': DetailMessage
                }
            })
async def get_user_by_username(
        user_id: int, user_service: UserService = Depends(get_user_service)):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    \f
    :param user_id: id of a user.
    :param user_service: service providing user model operations.
    :return: user with given id.
    """
    return user_service.get_or_404(user_id)


@router.get('/users/{username:str}', response_model=UserRead,
            responses={
                status.HTTP_404_NOT_FOUND: {
                    'model': DetailMessage
                }
            })
async def get_user_by_username(
        username: str, user_service: UserService = Depends(get_user_service)):
    """
    Returns user with corresponding username or returns 404 error.
    - **user_id**: id of a user.
    \f
    :param username: username of a user.
    :param user_service: service providing user model operations.
    :return: user with given id.
    """
    return user_service.get_by_username_or_404(username)
