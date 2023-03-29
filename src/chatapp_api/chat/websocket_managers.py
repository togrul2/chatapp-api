"""Websocket managers for chat related routes"""
import asyncio
import json
from dataclasses import dataclass, field
from typing import Literal, Protocol

from broadcaster import Broadcast  # type: ignore
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from src.chatapp_api.chat.exceptions import (
    AuthUserNotFoundWebSocketException,
    TargetUserNotFoundWebSocketException,
    WebSocketChatDoesNotExist,
)
from src.chatapp_api.chat.models import Chat
from src.chatapp_api.chat.service import ChatService
from src.chatapp_api.user.repository import UserRepository
from src.chatapp_api.user.schemas import UserRead


class MessageBody(BaseModel):
    """Pyndatic model for validating message payload in websockets managers."""

    type: Literal["message"]
    message: str


class AsyncWebsocketManager(Protocol):
    """Interface for websocket managers"""

    async def accept(self) -> None:
        ...

    async def run(self) -> None:
        ...


class AsyncSender(Protocol):
    """Interface for sender websocket managers"""

    async def sender(self) -> None:
        ...


class AsyncReceiver(Protocol):
    """Interface for receiver websocket managers"""

    async def receiver(self) -> None:
        ...


@dataclass
class PrivateChatMessagingManager(
    AsyncSender, AsyncReceiver, AsyncWebsocketManager
):
    """Private messages pub/sub manager.
    Manages messaging between two users."""

    broadcaster: Broadcast
    websocket: WebSocket
    chat_service: ChatService
    user_repository: UserRepository
    user_id: int
    target_id: int
    chat: Chat | None = field(init=False, default=None)

    @staticmethod
    def _get_channel_for_user(user_id: int):
        """Returns channel name for given user id"""
        return f"private-chat:user-{user_id}"

    async def accept(self) -> None:
        if await self.user_repository.find_by_id(self.user_id) is None:
            raise AuthUserNotFoundWebSocketException

        if await self.user_repository.find_by_id(self.user_id) is None:
            raise TargetUserNotFoundWebSocketException

        self.chat, _ = await self.chat_service.get_or_create_private_chat(
            self.user_id, self.target_id
        )
        await self.websocket.accept()

    async def receiver(self) -> None:
        try:
            async for body in self.websocket.iter_json():
                try:
                    MessageBody(**body)
                except ValidationError:
                    return

                if self.chat:
                    await self.chat_service.create_message(
                        self.chat.id, self.user_id, body["message"]
                    )

                body["from"] = UserRead.from_orm(
                    await self.user_repository.find_by_id(self.user_id)
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
class PublicChatMessagingManager(
    AsyncSender, AsyncReceiver, AsyncWebsocketManager
):
    """Public chat messaging manager.
    Manages messaging between public chat members."""

    broadcaster: Broadcast
    websocket: WebSocket
    chat_service: ChatService
    user_repository: UserRepository
    user_id: int
    chat_id: int

    def _get_current_chat_channel(self) -> str:
        """Returns set chat channel name."""
        return f"public-chat:chat-{self.chat_id}"

    async def accept(self) -> None:
        """Accepts given websocket connection.
        If user is not Chat member refuses."""
        if not await self.chat_service.is_chat_member(
            self.user_id, self.chat_id
        ):
            raise WebSocketChatDoesNotExist

        await self.websocket.accept()

    async def receiver(self) -> None:
        async for body in self.websocket.iter_json():
            try:
                MessageBody(**body)
            except ValidationError:
                return

            await self.chat_service.create_message(
                self.chat_id, self.user_id, body["message"]
            )

            body["from"] = UserRead.from_orm(
                await self.user_repository.find_by_id(self.user_id)
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
class NotificationsMessagingManager(AsyncSender, AsyncWebsocketManager):
    """Messaging manager for obtaining notifications."""

    broadcaster: Broadcast
    websocket: WebSocket
    user_repository: UserRepository
    user_id: int

    def _get_current_user_channel(self):
        return f"notifications:user-{self.user_id}"

    async def accept(self) -> None:
        if await self.user_repository.find_by_id(self.user_id) is None:
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
