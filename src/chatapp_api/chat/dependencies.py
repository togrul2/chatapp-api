from broadcaster import Broadcast  # type: ignore
from fastapi import Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.dependencies import (
    get_current_user_id_from_cookie_websocket,
)
from src.chatapp_api.chat.websocket_managers import (
    NotificationsMessagingManager,
    PrivateChatMessagingManager,
    PublicChatMessagingManager,
)
from src.chatapp_api.dependencies import get_broadcaster, get_db_session


def get_private_chat_messaging_manager(
    target_id: int,
    websocket: WebSocket,
    broadcaster: Broadcast = Depends(get_broadcaster),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
    session: AsyncSession = Depends(get_db_session),
):
    """Dependency for getting private chat messaging manager."""
    return PrivateChatMessagingManager(
        broadcaster, websocket, session, user_id, target_id
    )


def get_public_chat_messaging_manager(
    chat_id: int,
    websocket: WebSocket,
    broadcaster: Broadcast = Depends(get_broadcaster),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
    session: AsyncSession = Depends(get_db_session),
):
    """Dependency for getting public chat messaging manager."""
    return PublicChatMessagingManager(
        broadcaster, websocket, session, user_id, chat_id
    )


def get_notification_messaging_manager(
    websocket: WebSocket,
    broadcaster: Broadcast = Depends(get_broadcaster),
    user_id: int = Depends(get_current_user_id_from_cookie_websocket),
    session: AsyncSession = Depends(get_db_session),
):
    """Dependency for getting notifications messaging manager."""
    return NotificationsMessagingManager(
        broadcaster, websocket, session, user_id
    )
