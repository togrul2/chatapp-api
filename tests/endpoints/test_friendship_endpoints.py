"""Tests for friendship endpoints."""
from typing import cast

import pytest
from fastapi import status
from sqlalchemy import delete, select

from src.models.user import Friendship


@pytest.mark.asyncio
class TestFriendshipRequestList:
    """Test endpoints related to listing friendship requests"""

    url = "/api/friendship/requests"

    async def test_get_pending_requests(self, auth_client, friendship_request):
        """Test friendship requests listing endpoint"""
        response = await auth_client.get(self.url)
        body = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert friendship_request.id == body["results"][0]["id"]


@pytest.mark.asyncio
class TestFriendshipRequestDetail:
    """
    Test endpoints related friendship request detail methods
    such as get, accept, reject.
    """

    @staticmethod
    def get_url(target_id: int):
        """Returns url for target user's friendship."""
        return f"/api/friendship/requests/users/{target_id}"

    async def test_get_friendship_request(
        self, user, sender_user, auth_client, friendship_request
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
        self, user, sender_user, auth_client, session
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
        self, sender_user, auth_client, friendship_request, session
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
        self, sender_user, auth_client, friendship_request, session
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
class TestListFriends:
    async def test_list_friends(self, auth_client, friendship):
        ...
