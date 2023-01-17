"""Module with Chat API Routes & Websockets"""
import asyncio

from fastapi import APIRouter, Depends, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import broadcaster
from src.dependencies import (
    AuthWebSocket,
    get_auth_websocket,
    get_current_user_id_from_bearer,
    get_db,
    get_paginator,
)
from src.paginator import BasePaginator
from src.schemas.base import DetailMessage, PaginatedResponse
from src.schemas.chat import (
    ChatCreate,
    ChatRead,
    ChatReadWithMembers,
    ChatUpdate,
    MessageRead,
)
from src.services import chat as chat_services
from src.websocket_managers.chat import PrivateMessageManager

router = APIRouter(prefix="/api", tags=["chat"])


@router.websocket("/privates")
async def private_messages(
    auth_websocket: AuthWebSocket = Depends(get_auth_websocket),
    session: AsyncSession = Depends(get_db),
):
    """Websocket for sending and receiving private messages."""
    await auth_websocket.accept()
    manager = PrivateMessageManager(broadcaster, session)

    await asyncio.wait(
        [
            asyncio.create_task(manager.receiver(auth_websocket)),
            asyncio.create_task(manager.sender(auth_websocket)),
        ],
        return_when=asyncio.FIRST_COMPLETED,
    )


@router.get(
    "/users/{target_id}/messages",
    response_model=PaginatedResponse[MessageRead],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "detail": DetailMessage,
            "description": "Chat with target user does not exist.",
        }
    },
)
async def get_private_messages_from_user(
    target_id: int,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
    paginator: BasePaginator = Depends(get_paginator),
):
    """Returns messages with target user."""
    return await chat_services.get_messages_from_private_chat(
        session, user_id, target_id, paginator
    )


@router.get("/chats", response_model=PaginatedResponse[ChatReadWithMembers])
async def list_public_chats(
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db),
    paginator: BasePaginator = Depends(get_paginator),
):
    """List public chats as well as search through them."""
    return await chat_services.list_chats(session, paginator, keyword)


@router.post(
    "/chats",
    response_model=ChatReadWithMembers,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": DetailMessage,
            "description": "Chat name is taken.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "User with given id does not exist.",
        },
    },
)
async def create_public_chat(
    chat: ChatCreate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    session: AsyncSession = Depends(get_db),
):
    """Create public chat. Makes creator of chat owner."""
    return await chat_services.create_public_chat(session, user_id, chat)


@router.get(
    "/chats/{chat_id}",
    response_model=ChatReadWithMembers,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DetailMessage,
            "description": "Chat is not found.",
        }
    },
)
async def get_public_chat(
    chat_id: int, session: AsyncSession = Depends(get_db)
):
    """Get public chat detail with given id.
    If no public chat is found returns 404."""
    return await chat_services.get_public_chat_or_404(session, chat_id)


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
    session: AsyncSession = Depends(get_db),
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
    session: AsyncSession = Depends(get_db),
):
    """Deletes chat with given id. If user is not owner, returns 403."""
    await chat_services.delete_chat(session, user_id, chat_id)


@router.post("/chats/{chat_id}/invite-link")
def get_invite_link_for_chat(chat_id: int):
    """Generates and returns invite link for chat with expiration link."""


@router.post("/chats/{chat_id}/enroll")
def enroll_into_chat(chat_id: int, token: str = Form()):
    """Enrolls user into chat.
    If token is expired or incorrect returns 400 error code."""


@router.patch("/chats/{chat_id}/users/{target_id}")
def update_user_membership(chat_id: int, target_id: int):
    """Updates user membership info in chat (is_admin).
    If non admin user, returns 403 error code."""


@router.delete("/chats/{chat_id}/users/{target_id}")
def remove_user_from_chat(chat_id: int, target_id: int):
    """Removes user from chat. If non admin user, returns 403 error code."""


@router.get("/chats/{chat_id}/messages")
def list_chat_messages(chat_id: int):
    """Lists chat messages."""
