"""Websocket managers for chat related routes"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from broadcaster import Broadcast  # type: ignore
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chat import Message
from src.schemas.user import UserRead
from src.services import base as base_services
from src.services import chat as chat_services
from src.services import user as user_services


class BasePubSubManager(ABC):
    """Base class for redis publish/subscribe logic."""

    @abstractmethod
    async def receiver(self, websocket: WebSocket) -> None:
        """Consumer coroutine"""

    @abstractmethod
    async def sender(self, websocket: WebSocket) -> None:
        """Producer coroutine"""


@dataclass
class PrivateMessageManager(BasePubSubManager):
    """Private messages' pub/sub manager.
    Manages message channels and routing."""

    broadcaster: Broadcast
    session: AsyncSession
    user_id: int

    @staticmethod
    def get_channel_for_user(user_id: int):
        """Returns channel name for given user id"""
        return f"private-chat:user-{user_id}"

    @property
    def current_user_channel(self):
        """Property with channel name for set user."""
        return self.get_channel_for_user(self.user_id)

    async def receiver(self, websocket: WebSocket) -> None:
        async for body in websocket.iter_json():

            if not frozenset({"message", "to", "type"}).issubset(body.keys()):
                # TODO: validate with pydantic
                return

            user_channel = self.get_channel_for_user(body["to"])
            chat = await chat_services.get_or_create_private_chat(
                self.session, body["to"], self.user_id
            )
            await base_services.create(
                self.session,
                Message(
                    chat_id=chat.id,
                    sender_id=self.user_id,
                    body=body["message"],
                ),
            )

            body["from"] = UserRead.from_orm(
                user_services.get_by_id(self.session, self.user_id)
            ).dict()
            await self.broadcaster.publish(
                channel=user_channel, message=json.dumps(body)
            )

    async def sender(self, websocket: WebSocket) -> None:
        async with self.broadcaster.subscribe(
            self.current_user_channel
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                match body.get("type"):
                    case "message":
                        await websocket.send_json(body)
