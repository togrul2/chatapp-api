"""Module with Chat API Routes & Websockets"""
from fastapi import APIRouter, Depends
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
from schemas.base import PaginatedResponse
from schemas.chat import MessageRead
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
async def get_messages(
    target_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
    paginator: BasePaginator[MessageRead] = Depends(get_paginator),
):
    """Returns messages with target user."""
    chat_service.set_user(user_id)
    chat_service.set_paginator(paginator)
    return chat_service.get_messages_with_user(target_id)
