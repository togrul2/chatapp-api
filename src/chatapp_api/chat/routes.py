"""Module with Chat API Routes & Websockets"""
from fastapi import APIRouter, Depends, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.chat import services as chat_services
from src.chatapp_api.chat.dependencies import (
    get_notification_messaging_manager,
    get_private_chat_messaging_manager,
    get_public_chat_messaging_manager,
)
from src.chatapp_api.chat.schemas import (
    ChatCreate,
    ChatRead,
    ChatReadWithLastMessage,
    ChatReadWithUsersCount,
    ChatUpdate,
    MemberRead,
    MembershipBase,
    MembershipUpdate,
    MessageRead,
)
from src.chatapp_api.chat.websocket_managers import Receiver, Sender
from src.chatapp_api.dependencies import get_db_session, get_paginator
from src.chatapp_api.paginator import BasePaginator

router = APIRouter(prefix="/api", tags=["chat"])


@router.websocket("/chats/users/{target_id}", name="Private messaging")
async def private_messaging(
    manager: Sender | Receiver = Depends(get_private_chat_messaging_manager),
):
    """Websocket for sending and receiving private messages."""
    await manager.accept()
    await manager.run_manager()


@router.get(
    "/chats/users/{target_id}/messages",
    response_model=PaginatedResponse[MessageRead],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Chat with target user does not exist.",
        }
    },
)
async def get_private_messages_from_user(
    target_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns messages with target user."""
    return await chat_services.list_private_chat_messages(
        session, user_id, target_id, paginator
    )


@router.websocket("/chats/{chat_id}")
async def public_chat_messaging(
    manager: Sender | Receiver = Depends(get_public_chat_messaging_manager),
):
    """Websocket route for sending and receiving public chat messages."""
    await manager.accept()
    await manager.run_manager()


@router.get("/chats", response_model=PaginatedResponse[ChatReadWithUsersCount])
async def list_public_chats(
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """List public chats as well as search through them."""
    return await chat_services.list_chats(session, paginator, keyword)


@router.post(
    "/chats",
    response_model=ChatReadWithUsersCount,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "User with given id does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "Chat name is taken.",
        },
    },
)
async def create_public_chat(
    chat: ChatCreate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Create public chat. Makes creator of chat owner."""
    return await chat_services.create_public_chat(session, user_id, chat)


@router.get(
    "/chats/{chat_id}",
    response_model=ChatReadWithUsersCount,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Chat is not found.",
        }
    },
)
async def get_public_chat(
    chat_id: int, session: AsyncSession = Depends(get_db_session)
):
    """Get public chat detail with given id.
    If no public chat is found returns 404."""
    return await chat_services.get_public_chat_with_members_or_404(
        session, chat_id
    )


@router.put(
    "/chats/{chat_id}",
    response_model=ChatRead,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not group admin.",
        }
    },
)
async def update_public_chat(
    chat_id: int,
    data: ChatUpdate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Update public chat info. If user is not admin, returns 403."""
    return await chat_services.update_chat(session, user_id, chat_id, data)


@router.delete(
    "/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not group owner.",
        }
    },
)
async def delete_public_chat(
    chat_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
):
    """Deletes chat with given id. If user is not owner, returns 403."""
    await chat_services.delete_chat(session, user_id, chat_id)


@router.post(
    "/chats/{chat_id}/invite-token",
    response_model=str,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "Authenticated user is not chat admin.",
        }
    },
)
async def get_invite_link_for_chat(
    chat_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Generates and returns invite link for chat with expiration link."""
    return await chat_services.get_invite_link_for_chat(
        session, user_id, chat_id
    )


@router.post(
    "/chats/{chat_id}/enroll",
    response_model=MembershipBase,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DetailMessage,
            "description": "Token is invalid or expired.",
        },
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "User is already enrolled into the chat.",
        },
    },
)
async def enroll_into_chat(
    chat_id: int,
    token: str = Form(alias="t"),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Enrolls user into chat.
    If token is expired or incorrect returns 400 error code."""
    return await chat_services.enroll_user_with_token(
        session, user_id, chat_id, token
    )


@router.patch(
    "/chats/{chat_id}/members/{target_id}",
    response_model=MemberRead,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not admin.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Member not found.",
        },
    },
)
async def update_user_membership(
    chat_id: int,
    target_id: int,
    payload: MembershipUpdate,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Updates user membership info in chat (is_admin).
    If non admin user, returns 403 error code."""
    return await chat_services.update_membership(
        session, chat_id, user_id, target_id, payload.dict()
    )


@router.delete(
    "/chats/{chat_id}/members/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "Target is owner or auth user is not admin.",
        }
    },
)
async def remove_user_from_chat(
    chat_id: int,
    target_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Removes user from chat. If non admin user, returns 403 error code."""
    await chat_services.remove_member(session, chat_id, user_id, target_id)


@router.get(
    "/chats/{chat_id}/messages",
    response_model=PaginatedResponse[MessageRead],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not chat member.",
        }
    },
)
async def list_chat_messages(
    chat_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Lists chat messages. If user is not chat member,
    returns 403 http error code."""
    return await chat_services.list_public_chat_messages(
        session, chat_id, user_id, paginator
    )


@router.get(
    "/chats/{chat_id}/members",
    response_model=PaginatedResponse[MemberRead],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not chat member.",
        }
    },
)
async def list_chat_members(
    chat_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Lists chat members. If user is not chat member,
    returns 403 http error code."""
    return await chat_services.list_chat_members(
        session, chat_id, user_id, paginator
    )


@router.get(
    "/users/me/chats",
    response_model=PaginatedResponse[ChatReadWithLastMessage],
)
async def list_user_chats(
    keyword: str | None = None,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db_session),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns auth user's chats sorted by the date of their last message."""
    return await chat_services.list_user_chats(
        session, user_id, paginator, keyword
    )


@router.websocket("/chats/notifications", name="Notifications receiver")
async def get_notifications(
    manager: Sender = Depends(get_notification_messaging_manager),
):
    """Websocket route for getting notifications for new messages."""
    await manager.accept()
    await manager.run_manager()
