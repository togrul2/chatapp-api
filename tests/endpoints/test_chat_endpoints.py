"""Module with chat endpoint tests"""

from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatapp_api.base.schemas import PaginatedResponse
from src.chatapp_api.chat.models import Chat, Membership, Message
from src.chatapp_api.chat.schemas import (
    ChatRead,
    ChatReadWithUsersCount,
    MessageRead,
)
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.user.models import User
from tests.utils import AssertionErrors, validate_dict


@pytest.mark.asyncio
class TestPrivateChatApi:
    """Class with tests for private chat methods"""

    url = "/api/chats/users/{user_id}/messages"

    @staticmethod
    @pytest.fixture()
    async def private_chat_with_messages(
        session: AsyncSession, friendship: Friendship
    ):
        """Fixture for creating Chat with some messages"""
        chat = Chat(private=True)
        session.add(chat)
        await session.flush()
        await session.refresh(chat)
        session.add_all(
            [
                Membership(
                    chat_id=chat.id,
                    user_id=friendship.sender_id,
                    accepted=True,
                ),
                Membership(
                    chat_id=chat.id,
                    user_id=friendship.receiver_id,
                    accepted=True,
                ),
                Message(
                    body="Hello",
                    chat_id=chat.id,
                    sender_id=friendship.sender_id,
                ),
                Message(
                    body="Hi",
                    chat_id=chat.id,
                    sender_id=friendship.receiver_id,
                ),
                Message(
                    body="How are you?",
                    chat_id=chat.id,
                    sender_id=friendship.sender_id,
                ),
            ]
        )
        await session.commit()
        yield chat
        await session.delete(chat)
        await session.commit()

    @pytest.mark.usefixtures("private_chat_with_messages")
    async def test_get_private_chat_messages(
        self, auth_client: AsyncClient, sender_user: User
    ):
        """Tests listing messages of authenticated user with target user."""
        response = await auth_client.get(
            self.url.format(user_id=sender_user.id)
        )
        body = response.json()

        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        assert validate_dict(
            PaginatedResponse[MessageRead], body
        ), AssertionErrors.INVALID_BODY
        assert len(body["results"]) == 3, AssertionErrors.INVALID_NUM_OF_ROWS

    async def test_get_private_chat_messages_from_unexisting_user(
        self, auth_client: AsyncClient
    ):
        """Tests listing messages of authenticated user
        with unexisting target user."""
        response = await auth_client.get(
            self.url.format(user_id=12)  # Id of nonexistent user
        )
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        ), AssertionErrors.HTTP_NOT_404_NOT_FOUND


@pytest.mark.asyncio
class TestPublicChatApi:
    """Class with tests for public chat related endpoints"""

    url = "/api/chats"

    @staticmethod
    @pytest.fixture()
    async def public_chats(session: AsyncSession):
        """Fixture creating list of chats."""
        chats = [
            Chat(private=False, name="Auto-Parts"),
            Chat(private=False, name="Web-Gym"),
            Chat(private=False, name="Cook with Ernie"),
            Chat(private=False, name="Guide for Python"),
        ]
        session.add_all(chats)
        await session.commit()
        yield chats
        for chat in chats:
            await session.delete(chat)
        await session.commit()

    @pytest.mark.usefixtures("public_chats")
    async def test_list_public_chats(self, client: AsyncClient):
        """Test listing all public chats."""
        response = await client.get(self.url)
        body = response.json()

        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        assert validate_dict(
            PaginatedResponse[ChatReadWithUsersCount], body
        ), AssertionErrors.INVALID_BODY
        assert len(body["results"]) == 4, AssertionErrors.INVALID_NUM_OF_ROWS

    @pytest.mark.usefixtures("public_chats")
    async def test_search_public_chats(self, client: AsyncClient):
        """Test searching for public chats by keyword."""
        response = await client.get(self.url + "?keyword=Auto-")
        body = response.json()

        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        assert validate_dict(
            PaginatedResponse[ChatReadWithUsersCount], body
        ), AssertionErrors.INVALID_BODY
        assert len(body["results"]) == 1, AssertionErrors.INVALID_NUM_OF_ROWS

    async def test_create_public_chat(
        self,
        session: AsyncSession,
        auth_client: AsyncClient,
        user: User,
        sender_user: User,
    ):
        """Tests creating a public chat with a given name and members."""
        payload = {
            "name": "Cars.com",
            "members": [{"id": sender_user.id, "is_admin": False}],
        }
        response = await auth_client.post(self.url, json=payload)
        body = response.json()
        assert (
            validate_dict(ChatRead, body) is True
        ), AssertionErrors.INVALID_BODY
        assert (
            response.status_code == status.HTTP_201_CREATED
        ), AssertionErrors.HTTP_NOT_200_OK

        chat = (
            await session.scalars(
                select(Chat).where(Chat.name == payload["name"])
            )
        ).one_or_none()
        assert chat is not None, "Chat is not created"
        assert (
            await session.scalar(
                exists()
                .where(Membership.chat_id == chat.id)
                .where(Membership.user_id == user.id)
                .select()
            )
            is True
        ), "Chat creator is not its member"
        assert (
            await session.scalar(
                exists()
                .where(Membership.chat_id == chat.id)
                .where(Membership.user_id == sender_user.id)
                .select()
            )
            is True
        ), "Passed user is not its member"

    async def test_create_public_chat_with_taken_name(
        self,
        auth_client: AsyncClient,
        public_chat: Chat,
    ):
        """Tests creating a public chat with a given name and members."""
        payload: dict[str, Any] = {"name": public_chat.name, "members": []}
        response = await auth_client.post(self.url, json=payload)
        assert (
            response.status_code == status.HTTP_409_CONFLICT
        ), AssertionErrors.HTTP_NOT_409_CONFLICT


@pytest.mark.asyncio
class TestPublicChatDetailsApi:
    """This class contains tests for the public chat details API endpoint."""

    url = "/api/chats/{chat_id}"

    async def test_get_public_chat_by_id(
        self, client: AsyncClient, public_chat
    ):
        """Test to get a public chat by its ID."""
        response = await client.get(self.url.format(chat_id=public_chat.id))
        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        body = response.json()
        assert validate_dict(ChatReadWithUsersCount, body)

    async def test_get_public_nonexistent_chat_by_id(
        self, client: AsyncClient, public_chat
    ):
        """Test to get a nonexistent public chat by its ID."""
        response = await client.get(self.url.format(chat_id=public_chat.id))
        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_404_NOT_FOUND

    async def test_update_public_chat(
        self,
        session: AsyncSession,
        user: User,
        auth_client: AsyncClient,
        public_chat: Chat,
    ):
        """Test to update a public chat."""
        session.add(
            Membership(
                user_id=user.id,
                chat_id=public_chat.id,
                is_admin=True,
                is_owner=True,
                accepted=True,
            )
        )
        await session.commit()
        payload = {"name": "new-chat-name"}
        response = await auth_client.put(
            self.url.format(chat_id=public_chat.id), json=payload
        )
        assert (
            response.status_code == status.HTTP_200_OK
        ), AssertionErrors.HTTP_NOT_200_OK
        body = response.json()
        assert validate_dict(ChatRead, body) is True
        assert body["name"] == payload["name"]

    async def test_update_nonexistent_public_chat(
        self, auth_client: AsyncClient
    ):
        """Test to update a nonexistent public chat."""
        payload = {"name": "new-chat-name"}
        response = await auth_client.put(
            self.url.format(chat_id=12), json=payload
        )
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        ), AssertionErrors.HTTP_NOT_404_NOT_FOUND

    async def test_update_public_chat_by_unauthorized(
        self, auth_client: AsyncClient, public_chat: Chat
    ):
        """Test to update a public chat by an unauthorized user,
        who is not an admin."""
        payload = {"name": "Somename"}
        response = await auth_client.put(
            self.url.format(chat_id=public_chat.id), json=payload
        )
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), AssertionErrors.HTTP_NOT_403_FORBIDDEN

    async def test_delete_public_chat(
        self, session: AsyncSession, user: User, auth_client: AsyncClient
    ):
        """Test to delete a public chat."""
        chat = Chat(private=False, name="somename")
        session.add(chat)
        await session.flush()
        owner = Membership(
            chat_id=chat.id,
            user_id=user.id,
            is_owner=True,
            is_admin=True,
            accepted=True,
        )
        session.add(owner)
        await session.flush()
        response = await auth_client.delete(self.url.format(chat_id=chat.id))
        assert (
            response.status_code == status.HTTP_204_NO_CONTENT
        ), AssertionErrors.HTTP_NOT_204_NO_CONTENT

    async def test_delete_public_chat_by_unauthorized(
        self, session: AsyncSession, auth_client: AsyncClient
    ):
        """Test to delete a public chat by an unauthorized user,
        who is not an owner."""
        chat = Chat(private=False, name="somename")
        session.add(chat)
        await session.flush()

        response = await auth_client.delete(self.url.format(chat_id=chat.id))
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), AssertionErrors.HTTP_NOT_403_FORBIDDEN

    async def test_delete_nonexistent_public_chat(
        self, auth_client: AsyncClient
    ):
        """Test to delete a nonexistent public chat."""
        response = await auth_client.delete(self.url.format(chat_id=2))
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        ), AssertionErrors.HTTP_NOT_403_FORBIDDEN
