"""Websocket managers for chat related routes"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from broadcaster import Broadcast  # type: ignore
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.chat import WebSocketChatDoesNotExist
from src.models.chat import Chat, Message
from src.schemas.user import UserRead
from src.services import base as base_services
from src.services import chat as chat_services
from src.services import user as user_services


@dataclass
class BasePubSubManager(ABC):
    """Base class for redis publish/subscribe logic."""

    broadcaster: Broadcast
    session: AsyncSession

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

    user_id: int
    chat: Chat | None = field(init=False, default=None)

    @staticmethod
    def get_channel_for_user(user_id: int):
        """Returns channel name for given user id"""
        return f"private-chat:user-{user_id}"

    async def receiver(self, websocket: WebSocket) -> None:
        async for body in websocket.iter_json():

            # TODO: validate with pydantic
            if not frozenset({"message", "to", "type"}).issubset(body.keys()):
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
                await user_services.get_by_id(self.session, self.user_id)
            ).dict()
            await self.broadcaster.publish(
                channel=user_channel, message=json.dumps(body)
            )

    async def sender(self, websocket: WebSocket) -> None:
        async with self.broadcaster.subscribe(
            self.get_channel_for_user(self.user_id)
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                match body.get("type"):
                    case "message":
                        await websocket.send_json(body)


@dataclass
class ChatMessagesManager(BasePubSubManager):
    user_id: int
    chat_id: int

    def _get_current_chat_channel(self) -> str:
        """Returns set chat channel name."""
        return f"public-chat:chat-{self.chat_id}"

    async def accept(self, websocket: WebSocket) -> None:
        """Accepts given websocket connection.
        If user is not Chat member refuses."""
        if not await chat_services.is_chat_member(
            self.session, self.user_id, self.chat_id
        ):
            raise WebSocketChatDoesNotExist

        await websocket.accept()

    async def receiver(self, websocket: WebSocket) -> None:
        async for body in websocket.iter_json():

            # TODO: validate with pydantic
            if not frozenset({"message", "type"}).issubset(body.keys()):
                return

            await base_services.create(
                self.session,
                Message(
                    chat_id=self.chat_id,
                    sender_id=self.user_id,
                    body=body["message"],
                ),
            )

            body["from"] = UserRead.from_orm(
                await user_services.get_by_id(self.session, self.user_id)
            ).dict()
            await self.broadcaster.publish(
                channel=self._get_current_chat_channel(),
                message=json.dumps(body),
            )

    async def sender(self, websocket: WebSocket) -> None:
        async with self.broadcaster.subscribe(
            self._get_current_chat_channel()
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                match body.get("type"):
                    case "message":
                        if body["from"]["id"] != self.user_id:
                            await websocket.send_json(body)
