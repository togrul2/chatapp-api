from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth import services as auth_services
from src.chatapp_api.auth.schemas import RefreshTokenDto, UserWithTokens
from src.chatapp_api.base.schemas import DetailMessage
from src.chatapp_api.dependencies import get_db_session

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
    session: AsyncSession = Depends(get_db_session),
):
    """
    Creates access and refresh token for user:
    - **username**: username of a user.
    - **password**: password of a user.

    """
    return await auth_services.authenticate_user(
        session, credentials.username, credentials.password
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
    dto: RefreshTokenDto,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Creates access & refresh tokens based on refresh token.
    - **refresh_token**: refresh token
    """
    return await auth_services.refresh_tokens(session, dto.refresh_token)
