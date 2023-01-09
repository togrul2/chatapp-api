"""Module with Chat API Routes & Websockets"""
from fastapi import APIRouter, Depends, Form, status
from fastapi.concurrency import run_until_first_complete

from db import broadcast
from dependencies import (
    AuthWebSocket,
    get_auth_websocket,
    get_chat_service,
    get_current_user_id_from_bearer,
    get_paginator,
    get_user_service,
)
from paginator import BasePaginator
from schemas.base import DetailMessage, PaginatedResponse
from schemas.chat import ChatCreate, ChatRead, MessageRead
from services.chat import ChatService
from services.user import UserService
from websocket_managers.chat import PrivateMessageManager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/privates")
async def private_messages(
    auth_websocket: AuthWebSocket = Depends(get_auth_websocket),
    chat_service: ChatService = Depends(get_chat_service),
    user_service: UserService = Depends(get_user_service),
):
    """Websocket for sending and receiving private messages."""
    await auth_websocket.accept()
    manager = PrivateMessageManager(broadcast, chat_service, user_service)

    await run_until_first_complete(
        (manager.receiver, {"websocket": auth_websocket}),
        (manager.sender, {"websocket": auth_websocket}),
    )


@router.get(
    "/messages/{target_id}", response_model=PaginatedResponse[MessageRead]
)
def get_messages(
    target_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator[MessageRead] = Depends(get_paginator),
):
    """Returns messages with target user."""
    chat_service.set_user(user_id)
    chat_service.set_paginator(paginator)
    return chat_service.get_messages_from_private_chat(target_id)


@router.get("/chats")
def list_public_chats(
    keyword: str | None = None,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator[ChatRead] = Depends(get_paginator),
):
    """List public chats as well as search through them."""


@router.post(
    "/chats",
    response_model=ChatRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_400_BAD_REQUEST: {"model": DetailMessage}},
)
def create_public_chat(
    chat: ChatCreate,
    user_id: int = Depends(get_current_user_id_from_bearer),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Create public chat."""
    chat_service.set_user(user_id)
    return chat_service.create_public_chat(chat)


@router.get("/chats/{chat_id}")
def get_public_chat(chat_id: int):
    """Get public chat detail."""


@router.put("/chats/{chat_id}")
def update_public_chat(chat_id: int):
    """Update public chat info. If user is not admin, returns 403."""


@router.delete("/chats/{chat_id}")
def delete_public_chat(chat_id: int):
    """Deletes chat with given id. If user is not owner, returns 403."""


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
