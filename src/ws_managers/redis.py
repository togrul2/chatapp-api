import json
from abc import ABC, abstractmethod

from aioredis import Redis
from fastapi import WebSocket, WebSocketDisconnect


class BasePubSubManager(ABC):
    """Base class for redis publish/subscribe logic."""

    @abstractmethod
    async def consume(self):
        """Consumer coroutine"""

    @abstractmethod
    async def produce(self):
        """Producer coroutine"""


class PrivateMessageManager(BasePubSubManager):
    """Private messages pub/sub manager.
    Manages channels and messages routing"""

    def __init__(self, conn: Redis) -> None:
        self.conn = conn
        self.pubsub = self.conn.pubsub()

    @staticmethod
    def get_channel_for_user(user_id: int):
        return f"private-chat:user-{user_id}"

    async def consume(self, websocket: WebSocket):
        try:
            while True:
                message: dict = await websocket.receive_json()
                if message and frozenset({"message", "to"}).issubset(
                    message.keys()
                ):
                    user_channel = self.get_channel_for_user(message["to"])
                    message["from"] = websocket.user_id
                    await self.conn.publish(user_channel, json.dumps(message))

        except WebSocketDisconnect:
            await websocket.close()

    async def produce(self, websocket: WebSocket):
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
            await websocket.close()
