"""Module with Chat API Routes & Websockets"""
import asyncio

from fastapi import APIRouter, Depends, WebSocket

from db import redis_conn
from dependencies import get_auth_websocket
from ws_managers import redis as redis_manager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/privates")
async def private_messages(
    auth_websocket: WebSocket = Depends(get_auth_websocket),
):
    await auth_websocket.accept()
    manager = redis_manager.PrivateMessageManager(redis_conn)
    consumer_task = asyncio.create_task(manager.consume(auth_websocket))
    producer_task = asyncio.create_task(manager.produce(auth_websocket))

    await asyncio.wait(
        (consumer_task, producer_task),
        return_when=asyncio.FIRST_COMPLETED,
    )
