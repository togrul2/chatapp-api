from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.chatapp_api.auth.dependencies import get_auth_service
from src.chatapp_api.auth.schemas import RefreshTokenDto, UserWithTokens
from src.chatapp_api.auth.service import AuthService
from src.chatapp_api.base.schemas import DetailMessage

router = APIRouter(prefix="/api", tags=["auth"])


@router.post(
    "/token",
    status_code=status.HTTP_201_CREATED,
    response_model=UserWithTokens,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad credentials",
        }
    },
)
async def token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Creates access and refresh token for user:
    - **username**: username of a user.
    - **password**: password of a user.

    """
    return await auth_service.authenticate_user(
        credentials.username, credentials.password
    )


@router.post(
    "/refresh",
    status_code=status.HTTP_201_CREATED,
    response_model=UserWithTokens,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": DetailMessage,
            "description": "Bad refresh token",
        }
    },
)
async def refresh(
    refresh_dto: RefreshTokenDto,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Creates access & refresh tokens based on refresh token.
    - **refresh_token**: refresh token
    """
    return await auth_service.refresh_tokens(refresh_dto.refresh_token)
