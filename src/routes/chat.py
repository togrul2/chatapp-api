"""Module with Chat API Routes & Websockets"""
import asyncio

from fastapi import APIRouter, Depends

from db import redis_conn
from dependencies import (
    AuthWebSocket,
    get_auth_websocket,
    get_chat_service,
    get_current_user_id_from_bearer,
)
from schemas.chat import MessageRead
from services.chat import ChatService
from ws_managers import redis as redis_manager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/privates")
async def private_messages(
    auth_websocket: AuthWebSocket = Depends(get_auth_websocket),
    chat_service: ChatService = Depends(get_chat_service),
):
    """Websocket for sending and receiving private messages."""
    await auth_websocket.accept()
    manager = redis_manager.PrivateMessageManager(redis_conn, chat_service)
    consumer_task = asyncio.create_task(manager.consume(auth_websocket))
    producer_task = asyncio.create_task(manager.produce(auth_websocket))

    await asyncio.wait(
        (consumer_task, producer_task),
        return_when=asyncio.FIRST_COMPLETED,
    )


@router.get("/messages/{target_id}", response_model=list[MessageRead])
async def get_messages(
    target_id: int,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: int = Depends(get_current_user_id_from_bearer),
):
    """Returns messages with target user"""
    chat_service.set_user(user_id)
    return chat_service.get_messages_with_user(target_id)
