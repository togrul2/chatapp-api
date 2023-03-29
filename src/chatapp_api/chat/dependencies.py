"""Module with chat dependencies."""
from broadcaster import Broadcast  # type: ignore
from fastapi import Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.dependencies import (
    get_current_user_id_from_cookie_websocket,
)
from src.chatapp_api.chat.repository import (
    ChatRepository,
    MembershipRepository,
    MessageRepository,
)
from src.chatapp_api.chat.service import ChatService
from src.chatapp_api.chat.websocket_managers import (
    NotificationsMessagingManager,
    PrivateChatMessagingManager,
    PublicChatMessagingManager,
)
from src.chatapp_api.dependencies import (
    get_broadcaster,
    get_db_session,
    get_paginator,
)
from src.chatapp_api.paginator import BasePaginator
from src.chatapp_api.user.dependencies import get_user_repository
from src.chatapp_api.user.repository import UserRepository


def get_chat_repository(
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Chat repository dependency injector"""
    return ChatRepository(session, paginator)


def get_message_repository(
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Message repository dependency injector"""
    return MessageRepository(session, paginator)


def get_membership_repository(
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Membership repository dependency injector"""
    return MembershipRepository(session, paginator)


def get_chat_service(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    message_repository: MessageRepository = Depends(get_message_repository),
    membership_repository: MembershipRepository = Depends(
        get_membership_repository
    ),
):
    """Chat service dependency injector"""
    return ChatService(
        chat_repository, message_repository, membership_repository
    )


def get_private_chat_messaging_manager(
    target_id: int,  # Path variable
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service),
    user_repository: UserRepository = Depends(get_user_repository),
    broadcaster: Broadcast = Depends(get_broadcaster),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
):
    """Dependency for getting private chat messaging manager."""
    return PrivateChatMessagingManager(
        broadcaster,
        websocket,
        chat_service,
        user_repository,
        user_id,
        target_id,
    )


def get_public_chat_messaging_manager(
    chat_id: int,  # Path variable
    websocket: WebSocket,
    broadcaster: Broadcast = Depends(get_broadcaster),
    chat_service: ChatService = Depends(get_chat_service),
    user_repository: UserRepository = Depends(get_user_repository),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
):
    """Dependency for getting public chat messaging manager."""
    return PublicChatMessagingManager(
        broadcaster, websocket, chat_service, user_repository, user_id, chat_id
    )


def get_notification_messaging_manager(
    websocket: WebSocket,
    broadcaster: Broadcast = Depends(get_broadcaster),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
    user_repository: UserRepository = Depends(get_user_repository),
):
    """Dependency for getting notifications messaging manager."""
    return NotificationsMessagingManager(
        broadcaster, websocket, user_repository, user_id
    )
