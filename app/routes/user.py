from typing import List, Optional

from fastapi import APIRouter, Depends, status, Form, UploadFile
from fastapi.security import OAuth2PasswordRequestForm

import schemas
import jwt
from services import UserService, get_user_service

router = APIRouter()


@router.post("/api/token", status_code=status.HTTP_201_CREATED,
             response_model=schemas.TokenData,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {
                     "model": schemas.DetailMessage
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
        "access_token": jwt.create_access_token(user.id),
        "refresh_token": jwt.create_refresh_token(user.id)
    }


@router.post("/api/refresh", status_code=status.HTTP_201_CREATED,
             response_model=schemas.TokenData,
             responses={
                 status.HTTP_401_UNAUTHORIZED: {
                     "model": schemas.DetailMessage
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


@router.post("/api/register", status_code=status.HTTP_201_CREATED,
             response_model=schemas.UserRead,
             responses={
                 status.HTTP_400_BAD_REQUEST: {
                     "model": schemas.DetailMessage
                 }
             })
async def register(data: schemas.UserCreate,
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


@router.get("/api/users/me", response_model=schemas.UserRead)
async def get_auth_user(user_id: int = Depends(jwt.get_current_user_id),
                        user_service: UserService = Depends(get_user_service)):
    """
    Returns authenticated user's data or returns 401 if unauthenticated.
    \f
    :param user_id: id of authenticated user.
    :param user_service: service providing user model operations.
    :return: Auth user's data.
    """
    return user_service.get_or_404(user_id)


@router.put("/api/users/me", response_model=schemas.UserRead,
            responses={
                status.HTTP_400_BAD_REQUEST: {
                    "model": schemas.DetailMessage
                }
            })
async def update_auth_user(
        data: schemas.UserBase,
        user_id: int = Depends(jwt.get_current_user_id),
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


@router.patch("/api/users/me", response_model=schemas.UserRead,
              responses={
                  status.HTTP_400_BAD_REQUEST: {
                      "model": schemas.DetailMessage
                  }
              })
async def partial_update_auth_user(
        data: schemas.UserPartialUpdate,
        user_id: int = Depends(jwt.get_current_user_id),
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


@router.post("/api/users/me/image", response_model=schemas.UserRead)
async def upload_profile_picture(
        profile_picture: Optional[UploadFile] = None,
        user_id: int = Depends(jwt.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Upload image for authenticated user.
    - **image**: image file.
    \f
    :param profile_picture: Profile image user uploads.
    :param user_id: id of an authenticated user.
    :param user_service: service providing user model operations.
    :return: user info.
    """
    if profile_picture:
        return user_service.update_profile_picture(user_id, profile_picture)
    return user_service.remove_profile_picture(user_id)


@router.delete("/api/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auth_user(
        user_id: int = Depends(jwt.get_current_user_id),
        user_service: UserService = Depends(get_user_service)):
    """
    Deletes authenticated user's data or returns 401 if unauthenticated.
    \f
    Here we return response with empty body, so no return value needed.
    :param user_id: id of authenticated user
    :param user_service: service providing user model operations.
    """
    user_service.delete(user_id)


@router.get("/api/users", response_model=List[schemas.UserRead])
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
        expression = keyword + "%"
        return user_service.filter_by_username_or_email(expression, expression)

    return user_service.all()


@router.get("/api/users/{username}", response_model=schemas.UserRead)
async def get_user(username: str,
                   user_service: UserService = Depends(get_user_service)):
    """
    Returns user with corresponding id or returns 404 error.
    - **user_id**: id of a user.
    \f
    :param username: username of a user.
    :param user_service: service providing user model operations.
    :return: user with given id.
    """
    return user_service.get_by_username(username)
