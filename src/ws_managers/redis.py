import json
from abc import ABC, abstractmethod

from aioredis import Redis
from fastapi import WebSocket, WebSocketDisconnect

from dependencies import AuthWebSocket
from services.chat import ChatService


class BasePubSubManager(ABC):
    """Base class for redis publish/subscribe logic."""

    @abstractmethod
    async def consume(self, websocket: WebSocket):
        """Consumer coroutine"""

    @abstractmethod
    async def produce(self, websocket: WebSocket):
        """Producer coroutine"""


class PrivateMessageManager(BasePubSubManager):
    """Private messages' pub/sub manager.
    Manages channels and messages routing"""

    def __init__(self, conn: Redis, chat_service: ChatService) -> None:
        self.conn = conn
        self.pubsub = self.conn.pubsub()
        self.chat_service = chat_service

    @staticmethod
    def get_channel_for_user(user_id: int):
        return f"private-chat:user-{user_id}"

    async def consume(self, websocket: AuthWebSocket):
        try:
            while True:
                body = await websocket.receive_json()
                # FIXME: better error handling
                if body and frozenset({"message", "to"}).issubset(body.keys()):
                    user_channel = self.get_channel_for_user(body["to"])
                    body["from"] = websocket.user_id
                    chat = self.chat_service.get_or_create_private_chat(
                        body["to"], body["from"]
                    )
                    self.chat_service.create_message(
                        chat.id, body["from"], body["message"]
                    )
                    await self.conn.publish(user_channel, json.dumps(body))

        except WebSocketDisconnect:
            ...

    async def produce(self, websocket: AuthWebSocket):
        await self.pubsub.subscribe(
            self.get_channel_for_user(websocket.user_id)
        )
        try:
            while True:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True
                )
                if message:
                    await websocket.send_json(json.loads(message.get("data")))

        except WebSocketDisconnect:
            await self.pubsub.unsubscribe(
                self.get_channel_for_user(websocket.user_id)
            )
