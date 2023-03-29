"""Module with Chat API Routes & Websockets"""
from fastapi import APIRouter, Depends, Form, status

from src.chatapp_api.auth.dependencies import get_current_user_id_from_bearer
from src.chatapp_api.base.schemas import DetailMessage, PaginatedResponse
from src.chatapp_api.chat.dependencies import (
    get_chat_service,
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
    MembershipBase,
    MembershipRead,
    MembershipUpdate,
    MessageRead,
)
from src.chatapp_api.chat.service import ChatService
from src.chatapp_api.chat.websocket_managers import AsyncWebsocketManager

router = APIRouter(prefix="/api", tags=["chat"])


@router.websocket("/chats/users/{target_id}", name="Private messaging")
async def private_messaging(
    manager: AsyncWebsocketManager = Depends(
        get_private_chat_messaging_manager
    ),
):
    """Websocket for sending and receiving private messages."""
    await manager.accept()
    await manager.run()


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
    chat_service: ChatService = Depends(get_chat_service),
):
    """Returns messages with target user."""
    return await chat_service.list_private_chat_messages(user_id, target_id)


@router.websocket("/chats/{chat_id}")
async def public_chat_messaging(
    manager: AsyncWebsocketManager = Depends(
        get_public_chat_messaging_manager
    ),
):
    """Websocket route for sending and receiving public chat messages."""
    await manager.accept()
    await manager.run()


@router.get("/chats", response_model=PaginatedResponse[ChatReadWithUsersCount])
async def list_public_chats(
    keyword: str | None = None,
    chat_service: ChatService = Depends(get_chat_service),
):
    """List public chats as well as search through them."""
    return await chat_service.list_chats(keyword)


@router.post(
    "/chats",
    response_model=ChatRead,
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
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create public chat. Makes creator of chat owner."""
    return await chat_service.create_public_chat(
        user_id, chat.name, chat.members
    )


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
    chat_id: int,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get public chat detail with given id.
    If no public chat is found returns 404."""
    return await chat_service.get_public_chat_with_members_count_or_404(
        chat_id
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
    chat: ChatUpdate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Update public chat info. If user is not admin, returns 403."""
    return await chat_service.update_chat(user_id, chat_id, chat.name)


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
    chat_service: ChatService = Depends(get_chat_service),
):
    """Deletes chat with given id. If user is not owner, returns 403."""
    await chat_service.delete_chat(user_id, chat_id)


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
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Generates and returns invite link for chat with expiration link."""
    return await chat_service.get_invite_link_for_chat(user_id, chat_id)


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
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Enrolls user into chat.
    If token is expired or incorrect returns 400 error code."""
    return await chat_service.enroll_user_with_token(user_id, chat_id, token)


@router.patch(
    "/chats/{chat_id}/members/{target_id}",
    response_model=MembershipRead,
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
async def update_chat_member(
    chat_id: int,
    target_id: int,
    membership: MembershipUpdate,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Updates user membership info in chat (is_admin).
    If non admin user, returns 403 error code."""
    return await chat_service.update_membership(
        chat_id, user_id, target_id, membership.is_admin
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
async def remove_chat_member(
    chat_id: int,
    target_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Removes user from chat. If non admin user, returns 403 error code."""
    await chat_service.remove_member(chat_id, user_id, target_id)


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
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Lists chat messages. If user is not chat member,
    returns 403 http error code."""
    return await chat_service.list_public_chat_messages(chat_id, user_id)


@router.get(
    "/chats/{chat_id}/members",
    response_model=PaginatedResponse[MembershipRead],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DetailMessage,
            "description": "User is not chat member.",
        }
    },
)
async def list_chat_members(
    chat_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Lists chat members. If user is not chat member,
    returns 403 http error code."""
    return await chat_service.list_chat_members(chat_id, user_id)


@router.get(
    "/users/me/chats",
    response_model=PaginatedResponse[ChatReadWithLastMessage],
)
async def list_user_chats(
    keyword: str | None = None,
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Returns auth user's chats sorted by the date of their last message."""
    return await chat_service.list_user_chats(user_id, keyword)


@router.websocket("/chats/notifications", name="Notifications receiver")
async def get_notifications(
    manager: AsyncWebsocketManager = Depends(
        get_notification_messaging_manager
    ),
):
    """Websocket route for getting notifications for new messages."""
    await manager.accept()
    await manager.run()
