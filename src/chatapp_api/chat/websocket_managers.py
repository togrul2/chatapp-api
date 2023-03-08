"""Websocket managers for chat related routes"""
import asyncio
import json
from dataclasses import dataclass, field
from typing import Literal, Protocol, cast

from broadcaster import Broadcast  # type: ignore
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.base import services as base_services
from src.chatapp_api.chat import services as chat_services
from src.chatapp_api.chat.exceptions import (
    AuthUserNotFoundWebSocketException,
    TargetUserNotFoundWebSocketException,
    WebSocketChatDoesNotExist,
)
from src.chatapp_api.chat.models import Chat, Message
from src.chatapp_api.user.models import User
from src.chatapp_api.user.schemas import UserRead


class MessageBody(BaseModel):
    """Pyndatic model for validating message payload in websockets managers."""

    type: Literal["message"]
    message: str


class WebsocketManager(Protocol):
    """Interface for websocket managers"""

    async def accept(self) -> None:
        ...

    async def run(self) -> None:
        ...


class Sender(Protocol):
    """Interface for sender websocket managers"""

    async def sender(self) -> None:
        ...


class Receiver(Protocol):
    """Interface for receiver websocket managers"""

    async def receiver(self) -> None:
        ...


@dataclass
class BasePubSubManager(WebsocketManager):
    """Base class for redis publish/subscribe logic."""

    broadcaster: Broadcast
    websocket: WebSocket

    async def accept(self) -> None:
        """Accepts given websocket connection."""
        await self.websocket.accept()

    async def run(self) -> None:
        """Concurrently runs receiver and producer."""
        await asyncio.wait(
            [
                asyncio.create_task(self.receiver()),
                asyncio.create_task(self.sender()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )


@dataclass
class PrivateChatMessagingManager(BasePubSubManager):
    """Private messages pub/sub manager.
    Manages messaging between two users."""

    session: AsyncSession
    user_id: int
    target_id: int
    chat: Chat | None = field(init=False, default=None)

    @staticmethod
    def _get_channel_for_user(user_id: int):
        """Returns channel name for given user id"""
        return f"private-chat:user-{user_id}"

    async def accept(self):
        if await self.session.get(User, self.user_id) is None:
            raise AuthUserNotFoundWebSocketException

        if await self.session.get(User, self.user_id) is None:
            raise TargetUserNotFoundWebSocketException

        self.chat, _ = await chat_services.get_or_create_private_chat(
            self.session, self.user_id, self.target_id
        )
        await super().accept()

    async def receiver(self) -> None:
        try:
            async for body in self.websocket.iter_json():
                try:
                    MessageBody(**body)
                except ValidationError:
                    return

                await base_services.create(
                    self.session,
                    Message(
                        chat_id=cast(Chat, self.chat).id,  # TODO: relook
                        sender_id=self.user_id,
                        body=body["message"],
                    ),
                )

                body["from"] = UserRead.from_orm(
                    await self.session.get(User, self.user_id)
                ).dict()
                # TODO: send notification
                await self.broadcaster.publish(
                    channel=self._get_channel_for_user(self.target_id),
                    message=json.dumps(body),
                )
        except WebSocketDisconnect:
            ...

    async def sender(self) -> None:
        try:
            async with self.broadcaster.subscribe(
                self._get_channel_for_user(self.user_id)
            ) as subscriber:
                async for event in subscriber:
                    body = json.loads(event.message)

                    match body.get("type"):
                        case "message":
                            await self.websocket.send_json(body)
        except WebSocketDisconnect:
            ...


@dataclass
class PublicChatMessagingManager(BasePubSubManager):
    """Public chat messaging manager.
    Manages messaging between public chat members."""

    websocket: WebSocket
    session: AsyncSession
    user_id: int
    chat_id: int

    def _get_current_chat_channel(self) -> str:
        """Returns set chat channel name."""
        return f"public-chat:chat-{self.chat_id}"

    async def accept(self) -> None:
        """Accepts given websocket connection.
        If user is not Chat member refuses."""
        if not await chat_services.is_chat_member(
            self.session, self.user_id, self.chat_id
        ):
            raise WebSocketChatDoesNotExist

        await super().accept()

    async def receiver(self) -> None:
        async for body in self.websocket.iter_json():
            try:
                MessageBody(**body)
            except ValidationError:
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
                await self.session.get(User, self.user_id)
            ).dict()
            # TODO: send notifications

            await self.broadcaster.publish(
                channel=self._get_current_chat_channel(),
                message=json.dumps(body),
            )

    async def sender(self) -> None:
        async with self.broadcaster.subscribe(
            self._get_current_chat_channel()
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                match body.get("type"):
                    case "message":
                        if body["from"]["id"] != self.user_id:
                            await self.websocket.send_json(body)


@dataclass
class NotificationsMessagingManager(Sender):
    """Messaging manager for obtaining notifications."""

    broadcaster: Broadcast
    websocket: WebSocket
    session: AsyncSession
    user_id: int

    def _get_current_user_channel(self):
        return f"notifications:user-{self.user_id}"

    async def accept(self) -> None:
        if await self.session.get(User, self.user_id) is None:
            raise AuthUserNotFoundWebSocketException

        await self.websocket.accept()

    async def sender(self) -> None:
        async with self.broadcaster.subscribe(
            self._get_current_user_channel()
        ) as subscriber:
            async for event in subscriber:
                body = json.loads(event.message)

                if body.get("type") == "notification":
                    await self.websocket.send_json(body)

    async def run(self) -> None:
        await self.sender()
