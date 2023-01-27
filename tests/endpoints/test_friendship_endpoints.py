"""Tests for friendship endpoints."""
from typing import cast

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import Friendship, User


@pytest.mark.asyncio
class TestFriendshipRequestList:
    """Test endpoints related to listing friendship requests"""

    url = "/api/friendship/requests"

    async def test_get_pending_requests(
        self, auth_client: AsyncClient, friendship_request: Friendship
    ):
        """Test friendship requests listing endpoint"""
        response = await auth_client.get(self.url)
        body = response.json()

        assert (
            response.status_code == status.HTTP_200_OK
        ), "Status code is not successful."
        assert len(body["results"]) == 1
        assert friendship_request.id == body["results"][0]["id"]


@pytest.mark.asyncio
class TestFriendshipRequestDetail:
    """
    Test endpoints related friendship request detail methods
    such as get, accept, reject.
    """

    @staticmethod
    def get_url(target_id: int) -> str:
        """Returns url for target user's friendship."""
        return f"/api/friendship/requests/users/{target_id}"

    async def test_get_friendship_request(
        self,
        user: User,
        sender_user: User,
        auth_client: AsyncClient,
        friendship_request: Friendship,
    ):
        """Test getting friendship request."""
        response = await auth_client.get(
            self.get_url(cast(int, sender_user.id))
        )
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert body["id"] == friendship_request.id
        assert body["sender_id"] == sender_user.id
        assert body["receiver_id"] == user.id
        assert body["accepted"] is None

    async def test_send_friendship_request(
        self,
        user: User,
        sender_user: User,
        auth_client: AsyncClient,
        session: AsyncSession,
    ):
        """Test sending friendship request to a target user."""
        response = await auth_client.post(
            self.get_url(cast(int, sender_user.id))
        )
        body = response.json()

        created_friendship_query = await session.execute(
            select(Friendship).where(
                (Friendship.sender_id == user.id)
                & (Friendship.receiver_id == sender_user.id)
            )
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert body["sender_id"] == user.id
        assert body["receiver_id"] == sender_user.id

        assert (
            created_friendship_query.fetchone() is not None
        ), "Friendship is not created."

        # teardown, delete created friendship
        await session.execute(
            delete(Friendship).where(
                (Friendship.sender_id == user.id)
                & (Friendship.receiver_id == sender_user.id)
            )
        )
        await session.commit()

    async def test_reject_friendship_request(
        self,
        sender_user: User,
        auth_client: AsyncClient,
        friendship_request: Friendship,
        session: AsyncSession,
    ):
        """Test rejecting friendship request from a target user."""
        # target id must be preserved
        # since after rejection friendship record will be deleted
        target_id = friendship_request.id
        response = await auth_client.delete(
            self.get_url(cast(int, sender_user.id))
        )
        friendship_query = await session.execute(
            select(Friendship).where(Friendship.id == target_id)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert (
            friendship_query.fetchone() is None
        ), "Friendship is not deleted after rejection"

    async def test_accept_friendship_request(
        self,
        sender_user: User,
        auth_client: AsyncClient,
        friendship_request: Friendship,
        session: AsyncSession,
    ):
        """Test accepting friendship request from a target user."""
        response = await auth_client.patch(
            self.get_url(cast(int, sender_user.id))
        )
        friendship_query = await session.execute(
            select(Friendship).where(
                (Friendship.id == friendship_request.id)
                & (Friendship.accepted == True)  # noqa: E712
            )
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            friendship_query.fetchone() is not None
        ), "Target friendship is deleted or does not exist"


@pytest.mark.asyncio
async def test_list_friends(auth_client: AsyncClient, friendship: Friendship):
    """Tests listing authenticated user's friends."""
    response = await auth_client.get("/api/friendship/friends")
    body = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(body["results"]) == 1
    assert body["results"][0]["id"] == friendship.sender_id
