"""Module with user related dependencies"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.dependencies import (
    get_db_session,
    get_paginator,
    get_staticfiles_manager,
)
from src.chatapp_api.paginator import BasePaginator
from src.chatapp_api.staticfiles import BaseStaticFilesManager
from src.chatapp_api.user.repository import UserRepository
from src.chatapp_api.user.service import UserService


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Dependency injector for user repository"""
    return UserRepository(session, paginator)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    staticfiles_manager: BaseStaticFilesManager = Depends(
        get_staticfiles_manager
    ),
):
    """Dependency injector for user service"""
    return UserService(user_repository, staticfiles_manager)
