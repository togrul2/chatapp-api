"""Websocket managers for chat related routes"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from broadcaster import Broadcast
from fastapi import WebSocket

from src.dependencies import AuthWebSocket
from src.schemas.user import UserRead
from src.services.chat import ChatService
from src.services.user import UserService


class BasePubSubManager(ABC):
    """Base class for redis publish/subscribe logic."""

    @abstractmethod
    async def receiver(self, websocket: WebSocket):
        """Consumer coroutine"""

    @abstractmethod
    async def sender(self, websocket: WebSocket):
        """Producer coroutine"""


@dataclass
class PrivateMessageManager(BasePubSubManager):
    """Private messages' pub/sub manager.
    Manages channels and messages routing"""

    broadcaster: Broadcast
    chat_service: ChatService
    user_service: UserService

    @staticmethod
    def get_channel_for_user(user_id: int):
        """Returns channel name for given user id"""
        return f"private-chat:user-{user_id}"

    async def receiver(self, websocket: AuthWebSocket):
        async for body in websocket.iter_json():

            if not frozenset({"message", "to", "type"}).issubset(body.keys()):
                return

            user_channel = self.get_channel_for_user(body["to"])
            chat = self.chat_service.get_or_create_private_chat(
                body["to"], websocket.user_id
            )
            self.chat_service.create_message(
                chat.id, websocket.user_id, body["message"]
            )
            body["from"] = UserRead.from_orm(
                self.user_service.get_by_pk(websocket.user_id)
            ).dict()
            await self.broadcaster.publish(
                channel=user_channel, message=json.dumps(body)
            )

    async def sender(self, websocket: AuthWebSocket):
        async with self.broadcaster.subscribe(
            self.get_channel_for_user(websocket.user_id)
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                match body.get("type"):
                    case "message":
                        await websocket.send_json(body)
