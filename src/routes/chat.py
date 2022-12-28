"""Module with Chat API Routes & Websockets"""
from fastapi import APIRouter
from fastapi.websockets import WebSocket

router = APIRouter(prefix="chat")


@router.websocket("/ws")
async def private_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        pass
